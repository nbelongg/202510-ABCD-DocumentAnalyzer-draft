"""
CSV-based sync API for guideline management

Allows ABCD admins to manage organizations, guidelines, and access mappings
via CSV files (typically exported from Google Sheets).

Workflow:
1. Export current state to CSV
2. Edit CSV in Google Sheets
3. Preview changes
4. Apply changes to database
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Response
from fastapi.responses import PlainTextResponse
from typing import Optional
import csv
import io
import json

from schemas.guideline_access import SyncPreview, SyncResult
from db.connection import get_db_cursor
from services.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def parse_csv(file_content: str) -> list[dict]:
    """Parse CSV content into list of dictionaries"""
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        return list(reader)
    except Exception as e:
        logger.error("csv_parse_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format: {str(e)}"
        )


def validate_organization_row(row: dict, line_num: int) -> Optional[str]:
    """Validate organization CSV row"""
    required = ['organization_id', 'organization_name', 'email_domains']
    
    for field in required:
        if not row.get(field) or row[field].strip() == '':
            return f"Line {line_num}: Missing required field '{field}'"
    
    # Validate email domains format
    domains = row['email_domains'].strip()
    if not domains:
        return f"Line {line_num}: email_domains cannot be empty"
    
    # Check if domains are comma-separated
    domain_list = [d.strip() for d in domains.split(',')]
    for domain in domain_list:
        if '@' in domain:
            return f"Line {line_num}: email_domains should not contain '@' symbol"
        if '.' not in domain:
            return f"Line {line_num}: '{domain}' doesn't look like a valid domain"
    
    return None


def validate_guideline_row(row: dict, line_num: int) -> Optional[str]:
    """Validate guideline CSV row"""
    required = ['guideline_id', 'guideline_name', 'organization_id', 'visibility_scope']
    
    for field in required:
        if not row.get(field) or row[field].strip() == '':
            return f"Line {line_num}: Missing required field '{field}'"
    
    # Validate visibility scope
    valid_scopes = ['organization', 'public_mapped', 'universal']
    if row['visibility_scope'] not in valid_scopes:
        return f"Line {line_num}: visibility_scope must be one of {valid_scopes}"
    
    return None


def validate_access_row(row: dict, line_num: int) -> Optional[str]:
    """Validate access CSV row"""
    required = ['organization_id', 'guideline_id']
    
    for field in required:
        if not row.get(field) or row[field].strip() == '':
            return f"Line {line_num}: Missing required field '{field}'"
    
    return None


@router.post("/preview", response_model=SyncPreview)
async def preview_csv_sync(
    organizations_csv: Optional[UploadFile] = File(None),
    guidelines_csv: Optional[UploadFile] = File(None),
    guideline_access_csv: Optional[UploadFile] = File(None)
):
    """
    Preview changes that would be made by syncing CSV files
    
    Upload one or more CSV files to see what would change.
    No changes are made to the database.
    
    Returns a detailed preview showing:
    - Organizations to add/update/deactivate
    - Guidelines to add/update/deactivate
    - Access mappings to add/remove
    - Validation errors if any
    """
    preview = SyncPreview()
    errors = []
    warnings = []
    
    try:
        # Parse Organizations CSV
        organizations_from_csv = []
        if organizations_csv:
            content = (await organizations_csv.read()).decode('utf-8')
            organizations_from_csv = parse_csv(content)
            
            # Validate each row
            for i, row in enumerate(organizations_from_csv, start=2):
                error = validate_organization_row(row, i)
                if error:
                    errors.append(error)
        
        # Parse Guidelines CSV
        guidelines_from_csv = []
        if guidelines_csv:
            content = (await guidelines_csv.read()).decode('utf-8')
            guidelines_from_csv = parse_csv(content)
            
            # Validate each row
            for i, row in enumerate(guidelines_from_csv, start=2):
                error = validate_guideline_row(row, i)
                if error:
                    errors.append(error)
        
        # Parse Access CSV
        access_from_csv = []
        if guideline_access_csv:
            content = (await guideline_access_csv.read()).decode('utf-8')
            access_from_csv = parse_csv(content)
            
            # Validate each row
            for i, row in enumerate(access_from_csv, start=2):
                error = validate_access_row(row, i)
                if error:
                    errors.append(error)
        
        if errors:
            preview.has_errors = True
            preview.errors = errors
            return preview
        
        # Compare with database
        with get_db_cursor() as cursor:
            # Check organizations
            if organizations_from_csv:
                cursor.execute(
                    "SELECT organization_id, organization_name, is_active FROM organizations"
                )
                existing_orgs = {row['organization_id']: row for row in cursor.fetchall()}
                
                for row in organizations_from_csv:
                    org_id = row['organization_id']
                    is_active = row.get('is_active', 'TRUE').upper() == 'TRUE'
                    
                    if org_id not in existing_orgs:
                        preview.organizations_to_add.append(row)
                    elif existing_orgs[org_id]['organization_name'] != row['organization_name']:
                        preview.organizations_to_update.append(row)
                    elif existing_orgs[org_id]['is_active'] and not is_active:
                        preview.organizations_to_deactivate.append(row)
            
            # Check guidelines
            if guidelines_from_csv:
                cursor.execute(
                    "SELECT guideline_id, guideline_name, visibility_scope, is_active "
                    "FROM organization_guidelines"
                )
                existing_guidelines = {
                    row['guideline_id']: row for row in cursor.fetchall()
                }
                
                for row in guidelines_from_csv:
                    guideline_id = row['guideline_id']
                    is_active = row.get('is_active', 'TRUE').upper() == 'TRUE'
                    
                    if guideline_id not in existing_guidelines:
                        preview.guidelines_to_add.append(row)
                        warnings.append(
                            f"Note: Guideline '{guideline_id}' text must be set separately "
                            "(CSV only syncs metadata)"
                        )
                    elif (existing_guidelines[guideline_id]['guideline_name'] != row['guideline_name'] or
                          existing_guidelines[guideline_id]['visibility_scope'] != row['visibility_scope']):
                        preview.guidelines_to_update.append(row)
                    elif existing_guidelines[guideline_id]['is_active'] and not is_active:
                        preview.guidelines_to_deactivate.append(row)
            
            # Check access mappings
            if access_from_csv:
                cursor.execute(
                    "SELECT organization_id, guideline_id FROM organization_guideline_access"
                )
                existing_access = {
                    (row['organization_id'], row['guideline_id'])
                    for row in cursor.fetchall()
                }
                
                csv_access = {
                    (row['organization_id'], row['guideline_id'])
                    for row in access_from_csv
                }
                
                # New access to add
                for row in access_from_csv:
                    key = (row['organization_id'], row['guideline_id'])
                    if key not in existing_access:
                        preview.access_to_add.append(row)
                
                # Access to remove (in DB but not in CSV)
                for key in existing_access:
                    if key not in csv_access:
                        preview.access_to_remove.append({
                            'organization_id': key[0],
                            'guideline_id': key[1]
                        })
        
        # Calculate total changes
        preview.total_changes = (
            len(preview.organizations_to_add) +
            len(preview.organizations_to_update) +
            len(preview.organizations_to_deactivate) +
            len(preview.guidelines_to_add) +
            len(preview.guidelines_to_update) +
            len(preview.guidelines_to_deactivate) +
            len(preview.access_to_add) +
            len(preview.access_to_remove)
        )
        
        preview.warnings = warnings
        
        logger.info(
            "csv_preview_generated",
            total_changes=preview.total_changes,
            has_errors=preview.has_errors
        )
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("preview_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


@router.post("/apply", response_model=SyncResult)
async def apply_csv_sync(
    organizations_csv: Optional[UploadFile] = File(None),
    guidelines_csv: Optional[UploadFile] = File(None),
    guideline_access_csv: Optional[UploadFile] = File(None),
    admin_user: str = Query(..., description="Admin user applying changes")
):
    """
    Apply CSV sync to database
    
    **WARNING**: This will modify the database based on CSV contents.
    Always run /preview first!
    
    Changes applied:
    - Organizations: Upserted (insert or update)
    - Guidelines: Upserted (metadata only)
    - Access mappings: Replaced (existing removed, CSV added)
    """
    result = SyncResult(
        success=False,
        changes_applied=0,
        organizations_synced=0,
        guidelines_synced=0,
        access_mappings_synced=0
    )
    
    try:
        # First validate with preview (but don't show full preview to user)
        preview_check = await preview_csv_sync(
            organizations_csv=organizations_csv,
            guidelines_csv=guidelines_csv,
            guideline_access_csv=guideline_access_csv
        )
        
        if preview_check.has_errors:
            result.errors = preview_check.errors
            return result
        
        # Reset file positions after preview
        if organizations_csv:
            await organizations_csv.seek(0)
        if guidelines_csv:
            await guidelines_csv.seek(0)
        if guideline_access_csv:
            await guideline_access_csv.seek(0)
        
        with get_db_cursor() as cursor:
            # Sync Organizations
            if organizations_csv:
                content = (await organizations_csv.read()).decode('utf-8')
                organizations = parse_csv(content)
                
                for row in organizations:
                    org_id = row['organization_id']
                    org_name = row['organization_name']
                    email_domains = [d.strip() for d in row['email_domains'].split(',')]
                    is_active = row.get('is_active', 'TRUE').upper() == 'TRUE'
                    notes = row.get('notes', '')
                    
                    # Upsert organization
                    query = """
                        INSERT INTO organizations
                        (organization_id, organization_name, email_domains, is_active, 
                         description, created_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (organization_id) DO UPDATE
                        SET organization_name = EXCLUDED.organization_name,
                            email_domains = EXCLUDED.email_domains,
                            is_active = EXCLUDED.is_active,
                            description = EXCLUDED.description,
                            updated_at = NOW()
                    """
                    cursor.execute(query, (
                        org_id, org_name, json.dumps(email_domains), is_active, notes
                    ))
                    result.organizations_synced += 1
            
            # Sync Guidelines (metadata only)
            if guidelines_csv:
                content = (await guidelines_csv.read()).decode('utf-8')
                guidelines = parse_csv(content)
                
                for row in guidelines:
                    guideline_id = row['guideline_id']
                    guideline_name = row['guideline_name']
                    org_id = row['organization_id']
                    visibility_scope = row['visibility_scope']
                    is_active = row.get('is_active', 'TRUE').upper() == 'TRUE'
                    is_public = visibility_scope in ['public_mapped', 'universal']
                    description = row.get('description', '')
                    
                    # Note: guideline_text should be managed separately (too long for CSV)
                    # Check if exists first
                    cursor.execute(
                        "SELECT guideline_text FROM organization_guidelines WHERE guideline_id = %s",
                        (guideline_id,)
                    )
                    existing = cursor.fetchone()
                    
                    # Use existing text or placeholder
                    guideline_text = existing['guideline_text'] if existing else "[Guideline text - set via API]"
                    
                    query = """
                        INSERT INTO organization_guidelines
                        (guideline_id, organization_id, guideline_name, guideline_text,
                         description, is_public, visibility_scope, is_active, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (guideline_id) DO UPDATE
                        SET guideline_name = EXCLUDED.guideline_name,
                            organization_id = EXCLUDED.organization_id,
                            description = EXCLUDED.description,
                            is_public = EXCLUDED.is_public,
                            visibility_scope = EXCLUDED.visibility_scope,
                            is_active = EXCLUDED.is_active,
                            updated_at = NOW()
                    """
                    cursor.execute(query, (
                        guideline_id, org_id, guideline_name, guideline_text,
                        description, is_public, visibility_scope, is_active
                    ))
                    result.guidelines_synced += 1
            
            # Sync Access Mappings (replace all)
            if guideline_access_csv:
                content = (await guideline_access_csv.read()).decode('utf-8')
                access_mappings = parse_csv(content)
                
                # First, clear all existing mappings (we'll rebuild from CSV)
                cursor.execute("DELETE FROM organization_guideline_access")
                
                # Insert all from CSV
                for row in access_mappings:
                    org_id = row['organization_id']
                    guideline_id = row['guideline_id']
                    granted_by = row.get('granted_by', admin_user)
                    notes = row.get('notes', '')
                    
                    query = """
                        INSERT INTO organization_guideline_access
                        (organization_id, guideline_id, granted_by, granted_at, notes)
                        VALUES (%s, %s, %s, NOW(), %s)
                        ON CONFLICT (organization_id, guideline_id) DO NOTHING
                    """
                    cursor.execute(query, (org_id, guideline_id, granted_by, notes))
                    result.access_mappings_synced += 1
        
        result.success = True
        result.changes_applied = (
            result.organizations_synced +
            result.guidelines_synced +
            result.access_mappings_synced
        )
        result.warnings = preview_check.warnings
        
        logger.info(
            "csv_sync_applied",
            admin_user=admin_user,
            changes=result.changes_applied,
            orgs=result.organizations_synced,
            guidelines=result.guidelines_synced,
            access=result.access_mappings_synced
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("sync_apply_failed", error=str(e), admin_user=admin_user)
        result.errors = [str(e)]
        return result


@router.get("/export/organizations", response_class=PlainTextResponse)
async def export_organizations_csv():
    """Export current organizations as CSV"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT organization_id, organization_name, email_domains, 
                       is_active, description as notes
                FROM organizations
                ORDER BY organization_name
            """)
            rows = cursor.fetchall()
        
        # Convert to CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'organization_id', 'organization_name', 'email_domains', 'is_active', 'notes'
        ])
        writer.writeheader()
        
        for row in rows:
            # Convert JSON array to comma-separated string
            if isinstance(row['email_domains'], str):
                domains = json.loads(row['email_domains'])
            else:
                domains = row['email_domains']
            
            writer.writerow({
                'organization_id': row['organization_id'],
                'organization_name': row['organization_name'],
                'email_domains': ','.join(domains) if isinstance(domains, list) else domains,
                'is_active': 'TRUE' if row['is_active'] else 'FALSE',
                'notes': row.get('notes', '')
            })
        
        logger.info("organizations_exported", count=len(rows))
        return output.getvalue()
        
    except Exception as e:
        logger.error("export_organizations_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/export/guidelines", response_class=PlainTextResponse)
async def export_guidelines_csv():
    """Export current guidelines as CSV (metadata only)"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT guideline_id, guideline_name, organization_id,
                       visibility_scope, is_active, description
                FROM organization_guidelines
                ORDER BY organization_id, guideline_name
            """)
            rows = cursor.fetchall()
        
        # Convert to CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'guideline_id', 'guideline_name', 'organization_id',
            'visibility_scope', 'is_active', 'description'
        ])
        writer.writeheader()
        
        for row in rows:
            writer.writerow({
                'guideline_id': row['guideline_id'],
                'guideline_name': row['guideline_name'],
                'organization_id': row['organization_id'],
                'visibility_scope': row['visibility_scope'],
                'is_active': 'TRUE' if row['is_active'] else 'FALSE',
                'description': row.get('description', '')
            })
        
        logger.info("guidelines_exported", count=len(rows))
        return output.getvalue()
        
    except Exception as e:
        logger.error("export_guidelines_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/export/access", response_class=PlainTextResponse)
async def export_guideline_access_csv():
    """Export current guideline access mappings as CSV"""
    try:
        with get_db_cursor() as cursor:
            cursor.execute("""
                SELECT oga.organization_id, oga.guideline_id, 
                       oga.granted_by, oga.notes
                FROM organization_guideline_access oga
                ORDER BY oga.organization_id, oga.guideline_id
            """)
            rows = cursor.fetchall()
        
        # Convert to CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'organization_id', 'guideline_id', 'granted_by', 'notes'
        ])
        writer.writeheader()
        writer.writerows(rows)
        
        logger.info("access_mappings_exported", count=len(rows))
        return output.getvalue()
        
    except Exception as e:
        logger.error("export_access_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
