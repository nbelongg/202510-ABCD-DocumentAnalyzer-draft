# ABCD Document Analyzer - Prompts Sync Workflow

## Overview

This document describes the prompts synchronization workflow for the ABCD Document Analyzer improved system. The workflow maintains backwards compatibility with the legacy Google Colab-based approach while leveraging the new PostgreSQL-based API architecture.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prompt Types](#prompt-types)
3. [CSV Structure](#csv-structure)
4. [Usage Methods](#usage-methods)
5. [API Endpoints](#api-endpoints)
6. [Common Workflows](#common-workflows)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### Legacy System vs New System

**Legacy System (202509-ABCD-Document-Analyzer):**
- MySQL database
- Direct SQL operations from Colab
- Manual CSV parsing and row-by-row updates
- No API layer for bulk operations

**New System (202510-ABCD-Document-Analyzer-Improved):**
- PostgreSQL database with Alembic migrations
- RESTful API with FastAPI
- Bulk update endpoints for efficient operations
- Backwards-compatible CSV processing
- Both CLI and Colab execution options

### Migration Benefits

1. **Better Performance**: Bulk updates instead of row-by-row
2. **API Security**: All operations go through authenticated API
3. **Validation**: Pydantic schemas ensure data integrity
4. **Logging**: Structured logging for all operations
5. **Maintainability**: Clean separation of concerns

---

## Prompt Types

The system supports multiple prompt types organized by partition labels:

### 1. Analyzer Prompts (P1-P5)

Core analysis prompts for document processing:

- **P1**: Primary analysis prompt
  - P1.F1, P1.F2, P1.F3: Sub-prompts with specific focus areas
- **P2**: Secondary analysis
  - P2.F1, P2.F2, P2.F3: Sub-prompts
- **P3**: Tertiary analysis
  - P3.F1, P3.F2, P3.F3: Sub-prompts
- **P4**: Quaternary analysis
  - P4.F1, P4.F2, P4.F3: Sub-prompts
- **P5**: Quinary analysis
  - P5.F1, P5.F2, P5.F3: Sub-prompts

**API Endpoint**: `/update_prompts?prompt_label={label}`

### 2. Summary Prompts

Special prompts for document summarization:

- **P0**: Comments summary prompts
- **P-IS**: Proposal summary prompts (Investment Summary)
- **TOR-SUMMARY**: Terms of Reference summary prompts

**API Endpoints**:
- `/update_analyzer_comments_summary_prompts`
- `/update_analyzer_proposal_summary_prompts`
- `/update_tor_summary_prompts`

### 3. Evaluator Prompts

Evaluation-specific prompts:

- **P_Internal**: Internal evaluation prompts
  - P_Internal.F1, P_Internal.F2: Sub-prompts
- **P_External**: External evaluation prompts
- **P_Delta**: Delta/change evaluation prompts

**API Endpoint**: `/update_evaluator_prompts`

### 4. Custom Organization Prompts

Organization-specific prompts:

- **P_Custom**: Custom prompts per organization

**API Endpoint**: `/update_custom_prompts`

---

## CSV Structure

### Required Columns

All prompt CSVs must include these columns:

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| `partition_label` | String | Prompt type (P1, P2, P_Internal, etc.) | Yes |
| `doc_type` | String | Document type | Yes |
| `base_prompt` | Text | Main prompt text | Yes |
| `customization_prompt` | Text | Additional customization instructions | No |
| `organization_id` | String | Organization ID (for custom/org-specific prompts) | Conditional |
| `delete` | Boolean | Set to "True" to delete this prompt | No |

### Extended Columns (Analyzer Prompts)

For P1-P5 prompts:

| Column | Type | Description |
|--------|------|-------------|
| `corpus_id` | String | ID for prompt corpus/examples |
| `section_title` | String | Display title for this section |
| `wisdom_1` | String | First wisdom/guideline reference |
| `wisdom_2` | String | Second wisdom/guideline reference |
| `number_of_chunks` | Integer | Number of example chunks to use |
| `dependencies` | String | Comma-separated dependencies on other prompts |
| `customize_prompt_based_on` | String | Fields to use for customization |
| `send_along_customised_prompt` | String | Whether to send customized prompt |
| `which_chunks` | String | Which chunks to use (all/selected) |
| `wisdom_received` | String | Dependencies received |
| `llm_flow` | String | Execution flow (sequential/parallel) |
| `llm` | String | LLM provider (openai/anthropic/etc.) |
| `model` | String | Model name (gpt-4/claude-3-sonnet/etc.) |
| `show_on_frontend` | String | Display on frontend (True/False) |
| `label_for_output` | String | Output label for frontend |
| `system_prompt` | String | System-level instructions |
| `temperature` | Float | LLM temperature (0.0-1.0) |
| `max_tokens` | Integer | Maximum tokens for response |

### Extended Columns (Evaluator Prompts)

For P_Internal, P_External, P_Delta prompts:

| Column | Type | Description |
|--------|------|-------------|
| `org_guideline_id` | String | Organization guideline ID |
| `prompt_corpus` | String | Prompt corpus reference |

### Sample CSV Format

See `docs/csv_templates/prompts_template.csv` for a complete example.

---

## Usage Methods

### Method 1: Command-Line Script (Recommended for Production)

Use the Python script directly:

```bash
# Navigate to project directory
cd /path/to/202510-ABCD-Document-Analyzer-Improved

# Set environment variables
export API_BASE_URL="https://your-api-domain.com"
export API_KEY="your-api-key"
export API_SECRET="your-api-secret"

# Update all prompts
python scripts/update_analyzer_prompts.py --csv prompts_2025.csv --all

# Update specific prompt types
python scripts/update_analyzer_prompts.py --csv prompts_2025.csv --p1-p5 --evaluators

# Enable deletions (use with caution!)
python scripts/update_analyzer_prompts.py --csv prompts_2025.csv --all --delete-prompts
```

**Command-line Options:**

```
--csv PATH              Path to CSV file (required)
--api-url URL          Override API base URL
--all                  Update all prompt types
--p1-p5                Update P1-P5 analyzer prompts
--proposal             Update proposal summary prompts
--tor                  Update TOR summary prompts
--comments             Update comments summary prompts
--evaluators           Update evaluator prompts
--custom               Update custom org prompts
--delete-prompts       Enable deletion of marked prompts
--delete-custom        Enable deletion of marked custom prompts
```

### Method 2: Google Colab (Recommended for Admins)

Use the Colab-specific script:

1. **Open Google Colab**: Create a new notebook or open existing one

2. **Upload Script**:
```python
# Upload the script
from google.colab import files
uploaded = files.upload()  # Upload update_analyzer_prompts_colab.py
```

3. **Configure**:
```python
# Edit configuration in the script
class Config:
    API_BASE_URL = 'https://your-api-domain.com'
    API_KEY = 'your-api-key'
    API_SECRET = 'your-api-secret'
    
    # Option 1: Use uploaded CSV
    CSV_PATH = 'abcd_prompts_2025.csv'
    
    # Option 2: Use Google Sheets
    GOOGLE_SHEET_ID = '1a2b3c4d5e6f7g8h9i0j'
    
    # Enable/disable prompt types
    UPDATE_P1_P5_PROMPTS = True
    UPDATE_EVALUATORS_PROMPTS = True
```

4. **Run**:
```python
# Run the script
exec(open('update_analyzer_prompts_colab.py').read())
```

5. **Review Output**: Check console for success/failure messages

### Method 3: Direct API Calls

For programmatic access:

```python
import requests
import json

API_BASE_URL = "https://your-api-domain.com"
HEADERS = {
    'api-key': 'your-api-key',
    'api-secret': 'your-api-secret',
    'Content-Type': 'application/json'
}

# Update P1 prompts
prompts_data = [
    {
        "doc_type": "Program design Document",
        "base_prompt": "Analyze this document...",
        "customization_prompt": "Focus on...",
        # ... other fields
    }
]

response = requests.put(
    f"{API_BASE_URL}/update_prompts?prompt_label=P1",
    headers=HEADERS,
    data=json.dumps(prompts_data)
)

print(response.json())
```

---

## API Endpoints

### Analyzer Prompts

#### Update Analyzer Prompts (P1-P5)

```http
PUT /update_prompts?prompt_label={label}
Content-Type: application/json
api-key: {key}
api-secret: {secret}

[
  {
    "doc_type": "string",
    "base_prompt": "string",
    "customization_prompt": "string",
    "corpus_id": "string",
    "section_title": "string",
    "wisdom_1": "string",
    "wisdom_2": "string",
    "number_of_chunks": 5,
    "dependencies": "string",
    "customize_prompt_based_on": "string",
    "send_along_customised_prompt": "string",
    "which_chunks": "string",
    "wisdom_received": "string",
    "llm_flow": "string",
    "llm": "string",
    "model": "string",
    "show_on_frontend": "string",
    "label_for_output": "string",
    "system_prompt": "string",
    "temperature": 0.7,
    "max_tokens": 4000
  }
]
```

**Response:**
```json
{
  "success": true,
  "message": "Updated 5 and created 2 prompts for P1",
  "prompt_label": "P1",
  "total_processed": 7,
  "created": 2,
  "updated": 5
}
```

#### Delete Analyzer Prompts

```http
DELETE /delete_prompts?prompt_label={label}&doc_type={type}
api-key: {key}
api-secret: {secret}
```

**Response:**
```json
{
  "success": true,
  "message": "Deleted 1 prompts",
  "deleted_count": 1
}
```

### Summary Prompts

#### Update Comments Summary (P0)

```http
PUT /update_analyzer_comments_summary_prompts
Content-Type: application/json
api-key: {key}
api-secret: {secret}

[
  {
    "doc_type": "string",
    "summary_prompt": "string"
  }
]
```

#### Update Proposal Summary (P-IS)

```http
PUT /update_analyzer_proposal_summary_prompts
Content-Type: application/json
api-key: {key}
api-secret: {secret}

[
  {
    "doc_type": "string",
    "proposal_prompt": "string"
  }
]
```

#### Update TOR Summary

```http
PUT /update_tor_summary_prompts
Content-Type: application/json
api-key: {key}
api-secret: {secret}

[
  {
    "doc_type": "string",
    "tor_summary_prompt": "string",
    "organization_id": "string"
  }
]
```

### Evaluator Prompts

#### Update Evaluator Prompts

```http
PUT /update_evaluator_prompts
Content-Type: application/json
api-key: {key}
api-secret: {secret}

[
  {
    "prompt_label": "P_Internal",
    "doc_type": "string",
    "base_prompt": "string",
    "customization_prompt": "string",
    "organization_id": "string",
    "org_guideline_id": "string",
    "wisdom_1": "string",
    "wisdom_2": "string",
    "section_title": "string",
    "number_of_chunks": 5,
    "additional_dependencies": "string",
    "customize_prompt_based_on": "string",
    "send_along_customised_prompt": "string",
    "wisdom_received": "string",
    "llm_flow": "string",
    "llm": "string",
    "model": "string",
    "show_on_frontend": "string",
    "label_for_output": "string",
    "prompt_corpus": "string"
  }
]
```

### Custom Prompts

#### Update Custom Prompts

```http
PUT /update_custom_prompts
Content-Type: application/json
api-key: {key}
api-secret: {secret}

[
  {
    "doc_type": "string",
    "corpus_id": "string",
    "base_prompt": "string",
    "customization_prompt": "string",
    "organization_id": "string",
    "number_of_chunks": 5
  }
]
```

#### Delete Custom Prompts

```http
DELETE /delete_custom_prompts?organization_id={org_id}&doc_type={type}
api-key: {key}
api-secret: {secret}
```

---

## Common Workflows

### Workflow 1: Update All Prompts from Google Sheets

1. **Maintain CSV in Google Sheets**:
   - Create/update prompts in Google Sheets
   - Follow the CSV structure documented above
   - Use one sheet per prompt type or combine all

2. **Get Sheet ID**:
   - Open Google Sheet
   - Copy ID from URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

3. **Update Colab Script**:
```python
class Config:
    GOOGLE_SHEET_ID = '1a2b3c4d5e6f7g8h9i0j'
    UPDATE_P1_P5_PROMPTS = True
    UPDATE_EVALUATORS_PROMPTS = True
```

4. **Run Script**: Execute in Colab

5. **Verify**: Check API logs and test analyzer

### Workflow 2: Update Specific Prompt Type Locally

1. **Prepare CSV**: Create CSV with only the prompts you want to update

2. **Run Script**:
```bash
python scripts/update_analyzer_prompts.py \
    --csv p1_prompts_update.csv \
    --p1-p5 \
    --api-url https://api.abcd-analyzer.com
```

3. **Review Output**: Check console for statistics

4. **Test**: Run analyzer with updated prompts

### Workflow 3: Delete Outdated Prompts

1. **Mark for Deletion**: Add `delete` column to CSV, set to "True" for rows to delete

2. **Run with Delete Flag**:
```bash
python scripts/update_analyzer_prompts.py \
    --csv prompts_cleanup.csv \
    --p1-p5 \
    --delete-prompts
```

3. **Verify**: Check database that prompts were removed

### Workflow 4: Organization-Specific Updates

1. **Prepare Custom Prompts**: Create CSV with `P_Custom` partition label

2. **Include Organization ID**: Set `organization_id` column for each row

3. **Update**:
```bash
python scripts/update_analyzer_prompts.py \
    --csv org_unicef_prompts.csv \
    --custom
```

---

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Error**: `401 Unauthorized` or `403 Forbidden`

**Solution**:
- Verify API_KEY and API_SECRET are correct
- Check that API key has admin permissions
- Ensure headers are properly formatted

#### 2. CSV Parsing Errors

**Error**: `KeyError: 'partition_label'` or missing column errors

**Solution**:
- Verify CSV has all required columns
- Check for typos in column names (case-sensitive)
- Ensure no extra spaces in column headers
- Use the template CSV as reference

#### 3. Data Type Errors

**Error**: `ValidationError` from Pydantic

**Solution**:
- Check `number_of_chunks` is a valid integer
- Verify `temperature` is a float between 0.0 and 1.0
- Ensure `max_tokens` is a positive integer
- Make sure boolean fields use "True"/"False" strings

#### 4. Connection Timeout

**Error**: `requests.exceptions.Timeout`

**Solution**:
- Increase timeout in script (default: 60 seconds)
- Check API server is running and accessible
- Verify network connectivity
- For large batches, split into smaller updates

#### 5. Partial Updates

**Problem**: Some prompts updated, others failed

**Solution**:
- Review console output for specific errors
- Re-run script with only failed prompts
- Check database constraints (unique keys, foreign keys)
- Verify data integrity

### Debugging Tips

#### Enable Verbose Logging

Modify script to add debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Check API Response Details

```python
response = requests.put(url, ...)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
print(f"Headers: {response.headers}")
```

#### Validate CSV Before Upload

```python
import pandas as pd

df = pd.read_csv('prompts.csv')
print(f"Rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(f"Partition labels: {df['partition_label'].unique()}")
print(f"Missing values:\n{df.isnull().sum()}")
```

#### Test Individual Endpoints

Use curl or Postman to test single prompt update:

```bash
curl -X PUT "https://api.abcd-analyzer.com/update_prompts?prompt_label=P1" \
  -H "api-key: your-key" \
  -H "api-secret: your-secret" \
  -H "Content-Type: application/json" \
  -d '[{"doc_type": "test", "base_prompt": "test prompt"}]'
```

---

## Best Practices

### 1. Version Control for Prompts

- Keep prompts in version-controlled CSV files
- Use meaningful commit messages when updating
- Tag releases when deploying to production

### 2. Testing Updates

- Always test in staging environment first
- Verify analyzer output after prompt updates
- Compare results before/after to check impact

### 3. Backup Before Bulk Updates

- Export current prompts before major updates
- Keep backup CSV of production prompts
- Use database snapshots for critical changes

### 4. Incremental Updates

- Update one prompt type at a time
- Test after each update
- Roll back if issues detected

### 5. Documentation

- Document prompt changes in commit messages
- Maintain changelog for prompt updates
- Note any breaking changes or new requirements

---

## Migration from Legacy System

If you're migrating from the old Colab script:

### Key Differences

1. **Database**: MySQL -> PostgreSQL
2. **API Layer**: Direct DB access -> REST API
3. **Bulk Operations**: Row-by-row -> Batch updates
4. **Authentication**: DB credentials -> API keys
5. **Validation**: Manual checks -> Pydantic schemas

### Migration Steps

1. **Export Current Prompts**: Use old system to export all prompts to CSV

2. **Update CSV Format**: Ensure compatibility with new schema

3. **Test API Access**: Verify credentials and connectivity

4. **Dry Run**: Test with small subset of prompts

5. **Full Migration**: Update all prompts using new script

6. **Validation**: Compare old vs new system results

7. **Cutover**: Switch to new system exclusively

---

## Support

For issues or questions:

1. Check this documentation
2. Review API logs in monitoring dashboard
3. Check database for data integrity
4. Contact ABCD technical team

---

## Appendix

### Document Types

Supported document types:
- Program design Document
- Investment or grant proposal
- Strategy recommendations
- School or college course outline
- MEL approach
- Research draft or proposal
- Media article or draft
- Policy Document
- Product or service design

### LLM Providers

Supported providers:
- `openai`: GPT-4, GPT-4o, GPT-3.5-turbo
- `anthropic`: Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- `google`: Gemini models (if configured)

### System Prompt Templates

Example system prompts:
```
"You are an expert document analyzer specializing in program design."
"You are a financial analyst evaluating investment proposals."
"You are an internal auditor ensuring compliance with organizational standards."
```

---

**Last Updated**: October 2025  
**Version**: 1.0  
**Maintainer**: ABCD Technical Team
