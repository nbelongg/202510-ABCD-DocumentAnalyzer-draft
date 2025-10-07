"""
Admin API for managing public guideline access

Provides endpoints for ABCD admins to:
- Mark guidelines as public
- Grant organizations access to public guidelines
- Bulk operations for managing 20+ organizations
- List and revoke access mappings
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime

from schemas.guideline_access import (
    GuidelineAccessMapping,
    GuidelineAccessMappingResponse,
    BulkGuidelineAccessRequest,
    GuidelineVisibilityUpdate,
    AccessMappingListResponse,
    PublicGuidelineListResponse,
    BulkOperationResponse
)
from db.connection import get_db_cursor
from services.logger import get_logger
from services.exceptions import DatabaseError, NotFoundError

logger = get_logger(__name__)
router = APIRouter()


@router.post("/access-mappings", response_model=GuidelineAccessMappingResponse)
async def grant_guideline_access(
    mapping: GuidelineAccessMapping,
    admin_user: str = Query(..., description="Admin user performing this action")
):
    """
    Grant an organization access to a public guideline
    
    **Admin only**: This endpoint should be protected with admin authentication
    
    Example:
        ```python
        {
            "organization_id": "org-unicef",
            "guideline_id": "guideline-public-001",
            "granted_by": "admin@abcd.org",
            "notes": "Common best practices for all partners"
        }
        ```
    """
    try:
        with get_db_cursor() as cursor:
            # Verify guideline exists and is public
            cursor.execute(
                """SELECT guideline_name, is_public, visibility_scope 
                   FROM organization_guidelines WHERE guideline_id = %s""",
                (mapping.guideline_id,)
            )
            guideline = cursor.fetchone()
            
            if not guideline:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Guideline {mapping.guideline_id} not found"
                )
            
            if not guideline['is_public'] or guideline['visibility_scope'] != 'public_mapped':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Guideline must be public with 'public_mapped' scope. "
                           f"Current: is_public={guideline['is_public']}, "
                           f"scope={guideline['visibility_scope']}"
                )
            
            # Verify organization exists
            cursor.execute(
                "SELECT organization_name FROM organizations WHERE organization_id = %s",
                (mapping.organization_id,)
            )
            org = cursor.fetchone()
            
            if not org:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Organization {mapping.organization_id} not found"
                )
            
            # Insert mapping (ON CONFLICT DO NOTHING handles duplicates)
            query = """
                INSERT INTO organization_guideline_access
                (organization_id, guideline_id, granted_by, granted_at, notes)
                VALUES (%s, %s, %s, NOW(), %s)
                ON CONFLICT (organization_id, guideline_id) DO NOTHING
                RETURNING id, granted_at
            """
            cursor.execute(query, (
                mapping.organization_id,
                mapping.guideline_id,
                mapping.granted_by,
                mapping.notes
            ))
            result = cursor.fetchone()
            
            if not result:
                # Already exists - fetch existing
                cursor.execute(
                    """SELECT id, granted_at FROM organization_guideline_access 
                       WHERE organization_id = %s AND guideline_id = %s""",
                    (mapping.organization_id, mapping.guideline_id)
                )
                result = cursor.fetchone()
            
            logger.info(
                "guideline_access_granted",
                org_id=mapping.organization_id,
                guideline_id=mapping.guideline_id,
                granted_by=mapping.granted_by,
                admin_user=admin_user
            )
            
            return GuidelineAccessMappingResponse(
                id=result['id'],
                organization_id=mapping.organization_id,
                guideline_id=mapping.guideline_id,
                guideline_name=guideline['guideline_name'],
                granted_by=mapping.granted_by,
                granted_at=result['granted_at'],
                notes=mapping.notes
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("grant_access_failed", error=str(e), admin_user=admin_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant access: {str(e)}"
        )


@router.post("/access-mappings/bulk", response_model=BulkOperationResponse)
async def bulk_grant_guideline_access(
    request: BulkGuidelineAccessRequest,
    admin_user: str = Query(..., description="Admin user performing bulk operation")
):
    """
    Grant multiple organizations access to a guideline at once
    
    **Admin only**: Useful for quickly setting up access for 20+ organizations
    
    Example:
        ```python
        {
            "guideline_id": "guideline-public-001",
            "organization_ids": ["org-unicef", "org-gates", "org-who", ...],
            "granted_by": "admin@abcd.org",
            "notes": "Common best practices for all partners"
        }
        ```
    """
    try:
        success_count = 0
        failed_orgs = []
        
        with get_db_cursor() as cursor:
            # Verify guideline exists and is public
            cursor.execute(
                """SELECT guideline_name, is_public, visibility_scope 
                   FROM organization_guidelines WHERE guideline_id = %s""",
                (request.guideline_id,)
            )
            guideline = cursor.fetchone()
            
            if not guideline:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Guideline {request.guideline_id} not found"
                )
            
            if not guideline['is_public']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Guideline must be public for bulk sharing"
                )
            
            # Grant access to each organization
            for org_id in request.organization_ids:
                try:
                    query = """
                        INSERT INTO organization_guideline_access
                        (organization_id, guideline_id, granted_by, granted_at, notes)
                        VALUES (%s, %s, %s, NOW(), %s)
                        ON CONFLICT (organization_id, guideline_id) DO NOTHING
                    """
                    cursor.execute(query, (
                        org_id,
                        request.guideline_id,
                        request.granted_by,
                        request.notes
                    ))
                    success_count += 1
                    
                except Exception as e:
                    logger.warning("bulk_grant_failed_for_org", org_id=org_id, error=str(e))
                    failed_orgs.append(org_id)
            
            logger.info(
                "bulk_access_granted",
                guideline_id=request.guideline_id,
                success_count=success_count,
                failed_count=len(failed_orgs),
                admin_user=admin_user
            )
            
            return BulkOperationResponse(
                success=True,
                message=f"Granted access to {success_count} organizations",
                success_count=success_count,
                failure_count=len(failed_orgs),
                failed_items=failed_orgs,
                details={
                    "guideline_id": request.guideline_id,
                    "guideline_name": guideline['guideline_name'],
                    "total_requested": len(request.organization_ids)
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("bulk_grant_failed", error=str(e), admin_user=admin_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk operation failed: {str(e)}"
        )


@router.get("/access-mappings", response_model=AccessMappingListResponse)
async def list_guideline_access_mappings(
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    guideline_id: Optional[str] = Query(None, description="Filter by guideline"),
    limit: int = Query(100, le=500, description="Maximum results")
):
    """
    List all guideline access mappings
    
    Filter by organization or guideline to see what access exists.
    """
    try:
        with get_db_cursor() as cursor:
            where_clauses = []
            params = []
            
            if organization_id:
                where_clauses.append("oga.organization_id = %s")
                params.append(organization_id)
            
            if guideline_id:
                where_clauses.append("oga.guideline_id = %s")
                params.append(guideline_id)
            
            where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
                SELECT oga.id, oga.organization_id, oga.guideline_id,
                       oga.granted_by, oga.granted_at, oga.notes,
                       o.organization_name,
                       g.guideline_name, g.visibility_scope
                FROM organization_guideline_access oga
                JOIN organizations o ON oga.organization_id = o.organization_id
                JOIN organization_guidelines g ON oga.guideline_id = g.guideline_id
                {where_sql}
                ORDER BY oga.granted_at DESC
                LIMIT %s
            """
            
            params.append(limit)
            cursor.execute(query, tuple(params))
            mappings = cursor.fetchall()
            
            filtered_by = {}
            if organization_id:
                filtered_by['organization_id'] = organization_id
            if guideline_id:
                filtered_by['guideline_id'] = guideline_id
            
            return AccessMappingListResponse(
                mappings=mappings,
                total_count=len(mappings),
                filtered_by=filtered_by if filtered_by else None
            )
            
    except Exception as e:
        logger.error("list_mappings_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list mappings: {str(e)}"
        )


@router.delete("/access-mappings/{mapping_id}")
async def revoke_guideline_access(
    mapping_id: int,
    admin_user: str = Query(..., description="Admin revoking access")
):
    """
    Revoke an organization's access to a public guideline
    """
    try:
        with get_db_cursor() as cursor:
            # Get mapping details before deleting
            cursor.execute(
                """SELECT organization_id, guideline_id 
                   FROM organization_guideline_access WHERE id = %s""",
                (mapping_id,)
            )
            mapping = cursor.fetchone()
            
            if not mapping:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Mapping not found"
                )
            
            # Delete mapping
            cursor.execute(
                "DELETE FROM organization_guideline_access WHERE id = %s",
                (mapping_id,)
            )
            
            logger.info(
                "guideline_access_revoked",
                mapping_id=mapping_id,
                org_id=mapping['organization_id'],
                guideline_id=mapping['guideline_id'],
                revoked_by=admin_user
            )
            
            return {
                "success": True,
                "message": "Access revoked successfully",
                "mapping_id": mapping_id,
                "organization_id": mapping['organization_id'],
                "guideline_id": mapping['guideline_id']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("revoke_access_failed", error=str(e), admin_user=admin_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke access: {str(e)}"
        )


@router.put("/guidelines/{guideline_id}/visibility")
async def update_guideline_visibility(
    guideline_id: str,
    update: GuidelineVisibilityUpdate,
    admin_user: str = Query(..., description="Admin updating visibility")
):
    """
    Update guideline visibility settings
    
    Visibility scopes:
    - **organization**: Only the owning organization can see
    - **public_mapped**: Admin controls which organizations can see
    - **universal**: All organizations can see
    """
    try:
        with get_db_cursor() as cursor:
            query = """
                UPDATE organization_guidelines
                SET is_public = %s,
                    visibility_scope = %s,
                    updated_at = NOW()
                WHERE guideline_id = %s
                RETURNING guideline_name
            """
            cursor.execute(query, (
                update.is_public,
                update.visibility_scope.value,
                guideline_id
            ))
            
            result = cursor.fetchone()
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Guideline not found"
                )
            
            logger.info(
                "guideline_visibility_updated",
                guideline_id=guideline_id,
                guideline_name=result['guideline_name'],
                is_public=update.is_public,
                scope=update.visibility_scope.value,
                updated_by=admin_user
            )
            
            return {
                "success": True,
                "message": "Visibility updated",
                "guideline_id": guideline_id,
                "guideline_name": result['guideline_name'],
                "is_public": update.is_public,
                "visibility_scope": update.visibility_scope.value
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_visibility_failed", error=str(e), admin_user=admin_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update visibility: {str(e)}"
        )


@router.get("/public-guidelines", response_model=PublicGuidelineListResponse)
async def list_public_guidelines(
    visibility_scope: Optional[str] = Query(
        None, 
        regex="^(public_mapped|universal)$",
        description="Filter by visibility scope"
    ),
    limit: int = Query(100, le=500)
):
    """
    List all public guidelines available for mapping
    
    Shows which guidelines can be shared with organizations.
    """
    try:
        with get_db_cursor() as cursor:
            where_clause = "WHERE is_public = TRUE AND is_active = TRUE"
            params = []
            
            if visibility_scope:
                where_clause += " AND visibility_scope = %s"
                params.append(visibility_scope)
            
            query = f"""
                SELECT g.guideline_id, g.organization_id, g.guideline_name,
                       g.description, g.visibility_scope, g.is_public,
                       g.created_at, g.updated_at,
                       o.organization_name as owner_organization,
                       COUNT(DISTINCT oga.organization_id) as mapped_org_count
                FROM organization_guidelines g
                LEFT JOIN organizations o ON g.organization_id = o.organization_id
                LEFT JOIN organization_guideline_access oga ON g.guideline_id = oga.guideline_id
                {where_clause}
                GROUP BY g.guideline_id, g.organization_id, g.guideline_name,
                         g.description, g.visibility_scope, g.is_public, 
                         g.created_at, g.updated_at, o.organization_name
                ORDER BY g.created_at DESC
                LIMIT %s
            """
            
            params.append(limit)
            cursor.execute(query, tuple(params))
            guidelines = cursor.fetchall()
            
            return PublicGuidelineListResponse(
                guidelines=guidelines,
                total_count=len(guidelines),
                visibility_scope=visibility_scope
            )
            
    except Exception as e:
        logger.error("list_public_guidelines_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list public guidelines: {str(e)}"
        )
