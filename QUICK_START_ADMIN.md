# Quick Start Guide - Admin Operations

## For Developers Deploying the System

### Prerequisites
- Python 3.9+
- PostgreSQL database
- API credentials (API_KEY, API_SECRET)
- Access to production environment

### Deployment Checklist

- [ ] Clone repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Configure `.env` file with production credentials
- [ ] Run database migrations: `alembic upgrade head`
- [ ] Start API server: `python -m api.main`
- [ ] Verify API health: `curl http://localhost:8001/api/v1/health`
- [ ] Test authentication with API keys
- [ ] Provide admin team with Colab script and documentation

---

## For Admin Team Managing Prompts

### Option 1: Google Colab (Recommended)

1. **Open Colab Notebook**
   - Go to Google Colab
   - Upload `scripts/update_analyzer_prompts_colab.py`

2. **Configure Credentials**
   ```python
   class Config:
       API_BASE_URL = 'https://your-api.com'
       API_KEY = 'your_key'
       API_SECRET = 'your_secret'
       GOOGLE_SHEET_ID = 'your_sheet_id'  # Or leave None for local CSV
   ```

3. **Run Script**
   ```python
   exec(open('update_analyzer_prompts_colab.py').read())
   ```

4. **Review Output**
   - Check for "Success" messages
   - Note any failed updates
   - Verify in analyzer that prompts are updated

### Option 2: Command Line

```bash
# Set credentials
export API_BASE_URL="https://your-api.com"
export API_KEY="your_key"
export API_SECRET="your_secret"

# Update all prompts
python scripts/update_analyzer_prompts.py --csv prompts.csv --all

# Update specific types
python scripts/update_analyzer_prompts.py --csv prompts.csv --p1-p5 --evaluators
```

---

## For Admin Team Managing Guidelines

### Grant Organization Access to Public Guidelines

```bash
curl -X POST https://your-api.com/api/v1/admin/guidelines/access/grant \
  -H "api-key: your_key" \
  -H "api-secret: your_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "guideline_id": "guide_gates_2025",
    "organization_ids": ["unicef", "worldbank"]
  }'
```

### Update Organization Access via CSV

```bash
# Preview changes
python scripts/sync_guidelines_from_csv.py --preview access_mappings.csv

# Apply changes
python scripts/sync_guidelines_from_csv.py --apply access_mappings.csv
```

---

## CSV Templates

### Prompts CSV Format

Required columns:
- `partition_label` (P1, P2, P_Internal, P_Custom, etc.)
- `doc_type` (document type)
- `base_prompt` (main prompt text)

Optional columns:
- `customization_prompt`, `organization_id`, `corpus_id`, etc.

See: `docs/csv_templates/prompts_template.csv`

### Guidelines Access CSV Format

Required columns:
- `guideline_id`
- `organization_id`
- `granted_by`
- `granted_at`

See: `docs/csv_templates/guideline_access_template.csv`

---

## Common Tasks

### Task 1: Update P1 Prompts for All Document Types

1. Edit prompts in Google Sheets
2. Ensure `partition_label` = "P1"
3. Run Colab script with `UPDATE_P1_P5_PROMPTS = True`

### Task 2: Add Custom Prompts for New Organization

1. Create CSV row with `partition_label` = "P_Custom"
2. Set `organization_id` to organization's ID
3. Run script with `--custom` flag

### Task 3: Delete Outdated Prompts

1. Add `delete` column to CSV
2. Set to "True" for prompts to delete
3. Run script with `--delete-prompts` flag

### Task 4: Grant Access to Shared Guideline

1. Use API endpoint `/api/v1/admin/guidelines/access/grant`
2. Provide guideline_id and list of organization_ids
3. Verify with `/api/v1/admin/guidelines/public`

---

## Troubleshooting

### Error: 401 Unauthorized
- Check API_KEY and API_SECRET are correct
- Verify credentials have admin permissions

### Error: CSV parsing failed
- Verify all required columns exist
- Check for typos in column names (case-sensitive)
- Remove extra spaces in headers

### Error: Partial updates
- Review console output for specific errors
- Re-run with only failed prompts
- Check database logs

### Need Help?
- Read full documentation: `docs/PROMPTS_SYNC_WORKFLOW.md`
- Check API logs for errors
- Contact technical team

---

## Important Notes

⚠️ **Always test in staging first**  
⚠️ **Backup prompts before bulk updates**  
⚠️ **Use delete flags with caution**  
⚠️ **Keep CSV files version controlled**  

✅ **Prompts update immediately**  
✅ **Changes apply to all new analysis requests**  
✅ **Existing sessions keep their original prompts**  

---

## Documentation References

| Topic | Document |
|-------|----------|
| Complete Prompt Sync Guide | `docs/PROMPTS_SYNC_WORKFLOW.md` |
| Guideline Access Control | `docs/GUIDELINE_ACCESS_CONTROL.md` |
| Implementation Details | `PROMPTS_SYNC_INTEGRATION_SUMMARY.md` |
| API Documentation | `docs/API.md` |
| General System Docs | `README.md` |

---

**Last Updated**: October 2025  
**Version**: 1.0
