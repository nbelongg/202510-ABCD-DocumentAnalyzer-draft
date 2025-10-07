#!/usr/bin/env python3
"""
Sync guideline configuration from CSV files

Can be run from:
1. Local machine
2. Google Colab
3. Scheduled cron job

Usage:
    # Export current state
    python sync_guidelines_from_csv.py --export
    
    # Preview changes from local CSV files
    python sync_guidelines_from_csv.py --preview
    
    # Apply changes from local CSV files
    python sync_guidelines_from_csv.py --apply
    
    # Download from Google Sheets and preview
    python sync_guidelines_from_csv.py --preview \\
        --google-sheet-orgs "https://docs.google.com/spreadsheets/d/.../export?format=csv&gid=0"
    
    # Download from Google Sheets and apply
    python sync_guidelines_from_csv.py --apply \\
        --google-sheet-orgs "..." \\
        --google-sheet-guidelines "..." \\
        --google-sheet-access "..."
"""

import requests
import argparse
import json
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Configuration - can be overridden by environment variables
API_BASE = os.getenv('API_BASE', 'http://localhost:8001/api/v1')
API_KEY = os.getenv('API_KEY', 'your-api-key')
API_SECRET = os.getenv('API_SECRET', 'your-api-secret')
ADMIN_USER = os.getenv('ADMIN_USER', 'admin@abcd.org')

# CSV file paths (local)
ORGANIZATIONS_CSV = "organizations.csv"
GUIDELINES_CSV = "guidelines.csv"
GUIDELINE_ACCESS_CSV = "guideline_access.csv"

headers = {
    "api-key": API_KEY,
    "api-secret": API_SECRET
}


def download_from_google_sheets(sheet_url: str, output_file: str) -> bool:
    """
    Download CSV from Google Sheets
    
    Sheet URL format (edit):
    https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={SHEET_ID}
    
    Export URL format:
    https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid={SHEET_ID}
    
    Args:
        sheet_url: Google Sheets URL
        output_file: Local file to save to
        
    Returns:
        True if successful
    """
    # Convert edit URL to export URL if needed
    if 'edit' in sheet_url:
        sheet_url = sheet_url.replace('/edit', '/export?format=csv')
        if '#gid=' in sheet_url:
            sheet_url = sheet_url.replace('#gid=', '&gid=')
    
    print(f"📥 Downloading from Google Sheets...")
    print(f"   URL: {sheet_url[:60]}...")
    
    try:
        response = requests.get(sheet_url, timeout=30)
        response.raise_for_status()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"✓ Downloaded to {output_file}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Download failed: {e}")
        return False


def preview_changes() -> bool:
    """Preview what would change"""
    print("=" * 70)
    print(" PREVIEWING CHANGES")
    print("=" * 70)
    
    files = {}
    
    if Path(ORGANIZATIONS_CSV).exists():
        files['organizations_csv'] = open(ORGANIZATIONS_CSV, 'rb')
        print(f"✓ Found {ORGANIZATIONS_CSV}")
    
    if Path(GUIDELINES_CSV).exists():
        files['guidelines_csv'] = open(GUIDELINES_CSV, 'rb')
        print(f"✓ Found {GUIDELINES_CSV}")
    
    if Path(GUIDELINE_ACCESS_CSV).exists():
        files['guideline_access_csv'] = open(GUIDELINE_ACCESS_CSV, 'rb')
        print(f"✓ Found {GUIDELINE_ACCESS_CSV}")
    
    if not files:
        print("\n⚠️  No CSV files found!")
        print(f"   Looking for: {ORGANIZATIONS_CSV}, {GUIDELINES_CSV}, {GUIDELINE_ACCESS_CSV}")
        return False
    
    print(f"\n🔍 Calling API: {API_BASE}/admin/csv-sync/preview")
    
    try:
        response = requests.post(
            f"{API_BASE}/admin/csv-sync/preview",
            headers=headers,
            files=files,
            timeout=60
        )
        
        # Close files
        for f in files.values():
            f.close()
        
        response.raise_for_status()
        preview = response.json()
        
        # Display preview
        print(f"\n{'='*70}")
        print(f" 📊 PREVIEW SUMMARY")
        print(f"{'='*70}")
        print(f"Total changes: {preview['total_changes']}")
        print(f"Has errors: {preview['has_errors']}")
        
        if preview['has_errors']:
            print(f"\n{'='*70}")
            print(" ❌ ERRORS FOUND")
            print(f"{'='*70}")
            for error in preview['errors']:
                print(f"  • {error}")
            return False
        
        print("\n✅ No validation errors found")
        
        if preview.get('warnings'):
            print(f"\n⚠️  WARNINGS:")
            for warning in preview['warnings']:
                print(f"  • {warning}")
        
        if preview['organizations_to_add']:
            print(f"\n📍 Organizations to ADD ({len(preview['organizations_to_add'])}):")
            for org in preview['organizations_to_add'][:10]:  # Show first 10
                print(f"  + {org['organization_id']}: {org['organization_name']}")
            if len(preview['organizations_to_add']) > 10:
                print(f"  ... and {len(preview['organizations_to_add']) - 10} more")
        
        if preview['organizations_to_update']:
            print(f"\n📝 Organizations to UPDATE ({len(preview['organizations_to_update'])}):")
            for org in preview['organizations_to_update'][:5]:
                print(f"  ↻ {org['organization_id']}: {org['organization_name']}")
            if len(preview['organizations_to_update']) > 5:
                print(f"  ... and {len(preview['organizations_to_update']) - 5} more")
        
        if preview['guidelines_to_add']:
            print(f"\n📋 Guidelines to ADD ({len(preview['guidelines_to_add'])}):")
            for g in preview['guidelines_to_add'][:10]:
                print(f"  + {g['guideline_id']}: {g['guideline_name']}")
            if len(preview['guidelines_to_add']) > 10:
                print(f"  ... and {len(preview['guidelines_to_add']) - 10} more")
        
        if preview['guidelines_to_update']:
            print(f"\n📝 Guidelines to UPDATE ({len(preview['guidelines_to_update'])}):")
            for g in preview['guidelines_to_update'][:5]:
                print(f"  ↻ {g['guideline_id']}: {g['guideline_name']}")
            if len(preview['guidelines_to_update']) > 5:
                print(f"  ... and {len(preview['guidelines_to_update']) - 5} more")
        
        if preview['access_to_add']:
            print(f"\n🔑 Access mappings to ADD ({len(preview['access_to_add'])}):")
            for access in preview['access_to_add'][:15]:
                print(f"  + {access['organization_id']} → {access['guideline_id']}")
            if len(preview['access_to_add']) > 15:
                print(f"  ... and {len(preview['access_to_add']) - 15} more")
        
        if preview['access_to_remove']:
            print(f"\n🗑️  Access mappings to REMOVE ({len(preview['access_to_remove'])}):")
            for access in preview['access_to_remove'][:10]:
                print(f"  - {access['organization_id']} → {access['guideline_id']}")
            if len(preview['access_to_remove']) > 10:
                print(f"  ... and {len(preview['access_to_remove']) - 10} more")
        
        if preview['total_changes'] == 0:
            print("\n✓ No changes detected - database is already in sync with CSV files")
        
        print(f"\n{'='*70}\n")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def apply_changes() -> bool:
    """Apply changes to database"""
    print("=" * 70)
    print(" APPLYING CHANGES")
    print("=" * 70)
    
    # First preview
    if not preview_changes():
        print("\n❌ Preview failed or has errors. Not applying.")
        return False
    
    # Confirm
    print("\n⚠️  WARNING: This will modify the database!")
    response = input("   Type 'yes' to continue: ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return False
    
    files = {}
    
    if Path(ORGANIZATIONS_CSV).exists():
        files['organizations_csv'] = open(ORGANIZATIONS_CSV, 'rb')
    
    if Path(GUIDELINES_CSV).exists():
        files['guidelines_csv'] = open(GUIDELINES_CSV, 'rb')
    
    if Path(GUIDELINE_ACCESS_CSV).exists():
        files['guideline_access_csv'] = open(GUIDELINE_ACCESS_CSV, 'rb')
    
    print(f"\n🔄 Applying changes...")
    print(f"   API: {API_BASE}/admin/csv-sync/apply")
    print(f"   Admin user: {ADMIN_USER}")
    
    try:
        response = requests.post(
            f"{API_BASE}/admin/csv-sync/apply?admin_user={ADMIN_USER}",
            headers=headers,
            files=files,
            timeout=120
        )
        
        # Close files
        for f in files.values():
            f.close()
        
        response.raise_for_status()
        result = response.json()
        
        print(f"\n{'='*70}")
        print(" ✅ SYNC COMPLETE")
        print(f"{'='*70}")
        print(f"Success: {result['success']}")
        print(f"Total changes applied: {result['changes_applied']}")
        print(f"Organizations synced: {result['organizations_synced']}")
        print(f"Guidelines synced: {result['guidelines_synced']}")
        print(f"Access mappings synced: {result['access_mappings_synced']}")
        print(f"Timestamp: {result['timestamp']}")
        
        if result.get('warnings'):
            print(f"\n⚠️  Warnings:")
            for warning in result['warnings']:
                print(f"  • {warning}")
        
        if result.get('errors'):
            print(f"\n❌ Errors:")
            for error in result['errors']:
                print(f"  • {error}")
        
        print(f"\n{'='*70}\n")
        return result['success']
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def export_current_state() -> bool:
    """Export current database state to CSV files"""
    print("=" * 70)
    print(" EXPORTING CURRENT STATE")
    print("=" * 70)
    
    exports = [
        ('organizations', 'organizations_exported.csv'),
        ('guidelines', 'guidelines_exported.csv'),
        ('access', 'guideline_access_exported.csv')
    ]
    
    for endpoint, filename in exports:
        print(f"\n📥 Exporting {endpoint}...")
        try:
            response = requests.get(
                f"{API_BASE}/admin/csv-sync/export/{endpoint}",
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            # Count lines (minus header)
            line_count = len(response.text.strip().split('\n')) - 1
            print(f"✓ Saved to {filename} ({line_count} rows)")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Export failed: {e}")
            return False
    
    print(f"\n{'='*70}")
    print(" ✅ EXPORT COMPLETE")
    print(f"{'='*70}")
    print("\nExported files:")
    for _, filename in exports:
        print(f"  • {filename}")
    print(f"\n{'='*70}\n")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Sync guideline configuration from CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Actions
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview changes without applying'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes to database'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export current state to CSV files'
    )
    
    # Google Sheets URLs
    parser.add_argument(
        '--google-sheet-orgs',
        metavar='URL',
        help='Google Sheets URL for organizations'
    )
    parser.add_argument(
        '--google-sheet-guidelines',
        metavar='URL',
        help='Google Sheets URL for guidelines'
    )
    parser.add_argument(
        '--google-sheet-access',
        metavar='URL',
        help='Google Sheets URL for guideline access'
    )
    
    args = parser.parse_args()
    
    # Check configuration
    if API_KEY == 'your-api-key':
        print("⚠️  Warning: API_KEY not configured. Set via environment variable or update script.")
    
    # Download from Google Sheets if URLs provided
    if args.google_sheet_orgs:
        if not download_from_google_sheets(args.google_sheet_orgs, ORGANIZATIONS_CSV):
            return 1
    
    if args.google_sheet_guidelines:
        if not download_from_google_sheets(args.google_sheet_guidelines, GUIDELINES_CSV):
            return 1
    
    if args.google_sheet_access:
        if not download_from_google_sheets(args.google_sheet_access, GUIDELINE_ACCESS_CSV):
            return 1
    
    # Execute action
    if args.export:
        success = export_current_state()
    elif args.apply:
        success = apply_changes()
    elif args.preview:
        success = preview_changes()
    else:
        parser.print_help()
        return 0
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
