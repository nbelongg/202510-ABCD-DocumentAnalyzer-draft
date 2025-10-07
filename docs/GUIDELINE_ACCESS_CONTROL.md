# Guideline Access Control - Complete Implementation Guide

## Overview

This document describes the complete implementation of organization-specific guideline access control with CSV-based management for the ABCD Document Analyzer.

## Table of Contents

1. [Architecture](#architecture)
2. [Three-Tier Access Model](#three-tier-access-model)
3. [Setup Instructions](#setup-instructions)
4. [Admin Workflow](#admin-workflow)
5. [API Reference](#api-reference)
6. [CSV Management](#csv-management)
7. [Troubleshooting](#troubleshooting)

---

## Architecture

### Components

```
┌─────────────────────────────────────────────┐
│  Email Domain Resolution                     │
│  - Extract organization from user email      │
│  - Support multiple domains per org          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Three-Tier Guideline Access                 │
│  1. Organization's own guidelines            │
│  2. Public guidelines (admin-mapped)         │
│  3. Universal public guidelines              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  CSV-Based Configuration                     │
│  - Export current state                      │
│  - Edit in Google Sheets                     │
│  - Preview changes                           │
│  - Apply to database                         │
└─────────────────────────────────────────────┘
```

### Database Schema

**New Tables:**
- `organization_guideline_access` - Access mappings
- `guideline_access_log` - Audit trail

**Modified Tables:**
- `organizations` - Added `email_domains` (JSONB)
- `organization_guidelines` - Added `is_public`, `visibility_scope`

---

## Three-Tier Access Model

### Tier 1: Organization Guidelines (Private)

**Description:** Guidelines owned and visible only to the owning organization.

**Visibility Scope:** `organization`

**Example:**
- UNICEF's internal proposal guidelines
- Gates Foundation's specific requirements

**Access Control:**
- User's email domain must match organization
- Automatically accessible to org members

### Tier 2: Public Mapped Guidelines (Admin-Controlled)

**Description:** Public guidelines that admins can share with specific organizations.

**Visibility Scope:** `public_mapped`

**Example:**
- Best practices shared with 5 selected organizations
- Template guidelines for partner organizations

**Access Control:**
- Admin explicitly grants access via API or CSV
- Organizations can only see guidelines they've been granted access to

### Tier 3: Universal Public Guidelines

**Description:** Guidelines available to all organizations.

**Visibility Scope:** `universal`

**Example:**
- General proposal writing tips
- Common evaluation frameworks

**Access Control:**
- No restrictions
- Automatically available to everyone

---

## Setup Instructions

### Step 1: Run Database Migration

```bash
cd /path/to/202510-ABCD-Document-Analyzer-Improved

# Run PostgreSQL migration
psql -U your_user -d document_analyzer -f migrations/008_public_guidelines_and_access.sql
```

**Migration creates:**
- Access control tables
- Helper functions
- Sample data (universal guideline, ABCD public org)

### Step 2: Configure Email Domain Mappings

**Option A: Database (Recommended)**

Update organizations with email domains:

```sql
UPDATE organizations 
SET email_domains = '["unicef.org", "unicef.ch"]'::jsonb
WHERE organization_id = 'org-unicef';
```

**Option B: Environment Variable (Fallback)**

```bash
export ORG_EMAIL_DOMAINS='{"unicef.org": "org-unicef", "gatesfoundation.org": "org-gates"}'
```

### Step 3: Verify API Endpoints

Start the API and check Swagger docs:

```bash
# Start API
uvicorn api.main:app --reload --port 8001

# Open Swagger
open http://localhost:8001/docs
```

**New Endpoints:**
- `/api/v1/admin/guidelines/*` - Guideline management
- `/api/v1/admin/csv-sync/*` - CSV sync operations

---

## Admin Workflow

### Workflow Overview

```
1. Export → 2. Edit → 3. Preview → 4. Apply
   (CSV)     (Sheets)   (Check)     (Database)
```

### Detailed Steps

#### 1. Export Current State

```bash
python scripts/sync_guidelines_from_csv.py --export
```

**Output files:**
- `organizations_exported.csv`
- `guidelines_exported.csv`
- `guideline_access_exported.csv`

#### 2. Edit in Google Sheets

**Setup:**
1. Create Google Sheet with 3 tabs
2. Import CSV files
3. Share with team
4. Make edits

**Google Sheets URL Format:**
```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit#gid=SHEET_GID
```

**To get export URL:**
```
File → Share → Publish to web → Entire Document → CSV → Publish
```

#### 3. Preview Changes

```bash
python scripts/sync_guidelines_from_csv.py --preview \
  --google-sheet-orgs "https://docs.google.com/.../export?format=csv&gid=0" \
  --google-sheet-guidelines "https://docs.google.com/.../export?format=csv&gid=1" \
  --google-sheet-access "https://docs.google.com/.../export?format=csv&gid=2"
```

**Output:**
```
========================================================================
 📊 PREVIEW SUMMARY
========================================================================
Total changes: 25
Has errors: False

📍 Organizations to ADD (2):
  + org-new-partner: New Partner Organization
  + org-another: Another Organization

🔑 Access mappings to ADD (15):
  + org-unicef → guideline-public-001
  + org-gates → guideline-public-001
  ...
```

#### 4. Apply Changes

```bash
python scripts/sync_guidelines_from_csv.py --apply \
  --google-sheet-orgs "..." \
  --google-sheet-guidelines "..." \
  --google-sheet-access "..."
```

**Confirmation Required:**
```
⚠️  WARNING: This will modify the database!
   Type 'yes' to continue:
```

---

## API Reference

### Grant Access to Single Organization

**Endpoint:** `POST /api/v1/admin/guidelines/access-mappings`

```bash
curl -X POST "http://localhost:8001/api/v1/admin/guidelines/access-mappings?admin_user=admin@abcd.org" \
  -H "api-key: your-key" \
  -H "api-secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_id": "org-unicef",
    "guideline_id": "guideline-public-001",
    "granted_by": "admin@abcd.org",
    "notes": "Best practices for all partners"
  }'
```

### Bulk Grant Access

**Endpoint:** `POST /api/v1/admin/guidelines/access-mappings/bulk`

```bash
curl -X POST "http://localhost:8001/api/v1/admin/guidelines/access-mappings/bulk?admin_user=admin@abcd.org" \
  -H "api-key: your-key" \
  -H "api-secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "guideline_id": "guideline-public-001",
    "organization_ids": [
      "org-unicef", "org-gates", "org-who", "org-world-bank",
      "org-usaid", "org-dfid", "org-giz", "org-sida",
      "org-norad", "org-danida", "org-jica", "org-ausaid",
      "org-nzaid", "org-cida", "org-irish-aid", "org-swiss-dev",
      "org-ec", "org-undp", "org-unhcr", "org-wfp"
    ],
    "granted_by": "admin@abcd.org",
    "notes": "Common best practices for all 20 partner organizations"
  }'
```

### Mark Guideline as Public

**Endpoint:** `PUT /api/v1/admin/guidelines/guidelines/{guideline_id}/visibility`

```bash
curl -X PUT "http://localhost:8001/api/v1/admin/guidelines/guidelines/guideline-123/visibility?admin_user=admin@abcd.org" \
  -H "api-key: your-key" \
  -H "api-secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "is_public": true,
    "visibility_scope": "public_mapped"
  }'
```

### List Access Mappings

**Endpoint:** `GET /api/v1/admin/guidelines/access-mappings`

```bash
# All mappings
curl "http://localhost:8001/api/v1/admin/guidelines/access-mappings" \
  -H "api-key: your-key" \
  -H "api-secret: your-secret"

# For specific organization
curl "http://localhost:8001/api/v1/admin/guidelines/access-mappings?organization_id=org-unicef" \
  -H "api-key: your-key" \
  -H "api-secret: your-secret"

# For specific guideline
curl "http://localhost:8001/api/v1/admin/guidelines/access-mappings?guideline_id=guideline-public-001" \
  -H "api-key: your-key" \
  -H "api-secret: your-secret"
```

---

## CSV Management

### CSV File Formats

#### organizations.csv

```csv
organization_id,organization_name,email_domains,is_active,notes
org-unicef,UNICEF,"unicef.org,unicef.ch",TRUE,United Nations Children's Fund
org-gates,Gates Foundation,"gatesfoundation.org,gates.com",TRUE,Bill & Melinda Gates Foundation
```

**Fields:**
- `organization_id` - Unique identifier (required)
- `organization_name` - Display name (required)
- `email_domains` - Comma-separated domains WITHOUT @ (required)
- `is_active` - TRUE or FALSE (default: TRUE)
- `notes` - Optional description

#### guidelines.csv

```csv
guideline_id,guideline_name,organization_id,visibility_scope,is_active,description
guideline-public-001,Best Practices,org-abcd-public,public_mapped,TRUE,Common best practices
guideline-universal-001,General Tips,org-abcd-public,universal,TRUE,Available to all
```

**Fields:**
- `guideline_id` - Unique identifier (required)
- `guideline_name` - Display name (required)
- `organization_id` - Owner organization (required)
- `visibility_scope` - organization, public_mapped, or universal (required)
- `is_active` - TRUE or FALSE (default: TRUE)
- `description` - Optional description

**Note:** Guideline text is NOT managed via CSV (too long). Set via API separately.

#### guideline_access.csv

```csv
organization_id,guideline_id,granted_by,notes
org-unicef,guideline-public-001,admin@abcd.org,Common best practices
org-gates,guideline-public-001,admin@abcd.org,Common best practices
```

**Fields:**
- `organization_id` - Organization to grant access (required)
- `guideline_id` - Guideline to share (required)
- `granted_by` - Admin email (default: admin@abcd.org)
- `notes` - Optional reason

### CSV Sync Behavior

**Organizations:**
- INSERT new organizations
- UPDATE existing organizations (name, domains, active status)
- NEVER DELETE organizations

**Guidelines:**
- INSERT new guidelines (with placeholder text)
- UPDATE guideline metadata (name, visibility, active status)
- PRESERVE existing guideline text
- NEVER DELETE guidelines

**Access Mappings:**
- DELETE all existing mappings
- INSERT all mappings from CSV
- This is a REPLACE operation

---

## Troubleshooting

### Common Issues

#### 1. Email Domain Not Recognized

**Problem:** User's email doesn't match any organization.

**Solution:**
```sql
-- Check current mappings
SELECT organization_id, email_domains FROM organizations;

-- Update organization
UPDATE organizations 
SET email_domains = email_domains || '["newdomain.org"]'::jsonb
WHERE organization_id = 'org-example';
```

#### 2. Access Denied to Guideline

**Problem:** User can't see a public guideline they should have access to.

**Check access mapping:**
```sql
SELECT * FROM organization_guideline_access 
WHERE organization_id = 'org-unicef' 
  AND guideline_id = 'guideline-public-001';
```

**Grant access:**
```bash
curl -X POST ".../admin/guidelines/access-mappings" \
  -d '{"organization_id": "org-unicef", "guideline_id": "guideline-public-001", ...}'
```

#### 3. CSV Validation Errors

**Common errors:**
- Email domains contain @ symbol → Remove @
- Missing required fields → Check CSV headers match exactly
- Invalid visibility_scope → Must be: organization, public_mapped, or universal

**Fix:**
```bash
# Preview first to see errors
python scripts/sync_guidelines_from_csv.py --preview
```

#### 4. Guideline Text Not Syncing

**This is expected behavior.** CSV only syncs metadata.

**To update guideline text:**
```sql
UPDATE organization_guidelines 
SET guideline_text = 'Your full guideline text here...'
WHERE guideline_id = 'guideline-public-001';
```

### Audit Logs

Check who accessed what:

```sql
SELECT user_email, organization_id, guideline_id, 
       access_granted, access_reason, accessed_at
FROM guideline_access_log
WHERE user_email = 'user@unicef.org'
ORDER BY accessed_at DESC
LIMIT 20;
```

---

## Advanced Usage

### Python Script Configuration

**Environment Variables:**
```bash
export API_BASE="https://your-api.abcd.org/api/v1"
export API_KEY="your-production-api-key"
export API_SECRET="your-production-secret"
export ADMIN_USER="your-email@abcd.org"
```

### Automated Sync (Cron Job)

```bash
# Add to crontab: sync every hour
0 * * * * cd /path/to/project && python scripts/sync_guidelines_from_csv.py --apply --google-sheet-orgs "..." >> /var/log/guideline-sync.log 2>&1
```

### Google Colab Integration

```python
# In Google Colab
!pip install requests

import requests
import pandas as pd

# Load from Google Sheets
orgs_df = pd.read_csv("https://docs.google.com/.../export?format=csv&gid=0")

# Preview changes
files = {
    'organizations_csv': ('orgs.csv', orgs_df.to_csv(index=False))
}

response = requests.post(
    "https://your-api.abcd.org/api/v1/admin/csv-sync/preview",
    headers={"api-key": "...", "api-secret": "..."},
    files=files
)

print(response.json())
```

---

## Security Considerations

1. **Admin Authentication:** All admin endpoints require API key/secret
2. **Audit Logging:** All access attempts are logged
3. **Email Validation:** Email domains verified against database
4. **No Client UI Needed:** Prevents unauthorized access configuration
5. **Preview Before Apply:** Always check changes before applying

---

## Support

For issues or questions:
1. Check this documentation
2. Review audit logs in `guideline_access_log` table
3. Test with CSV preview before applying
4. Contact ABCD technical team

---

**Last Updated:** 2025-10-07  
**Version:** 1.0  
**Author:** ABCD Technical Team
