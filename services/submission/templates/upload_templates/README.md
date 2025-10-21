# Example Upload Template

This folder contains example templates for data upload to the TUS Engage Tool.

## Template Files

Place your Excel templates here with the naming convention:
`{template_name}_v{version}.xlsx`

## Required Headers (Minimum)

All upload files must include these headers:
- **submission_date**: Date of submission (YYYY-MM-DD format)
- **department**: Department name
- **category**: Category of engagement

## Example Template Structure

### Basic Template (example_template_v1.0.xlsx)

| submission_date | department | category | description | participants | duration |
|----------------|------------|----------|-------------|--------------|----------|
| 2025-01-15 | Engineering | Workshop | Python Training | 25 | 3 hours |
| 2025-01-16 | Business | Seminar | Leadership | 40 | 2 hours |

### Notes
1. Date format must be YYYY-MM-DD or Excel date
2. Department and category are required
3. Additional columns are stored in JSONB (flexible schema)
4. Empty cells are stored as NULL
5. Maximum 10,000 rows per file

## Creating Your Template

1. **Start with required headers**: submission_date, department, category
2. **Add custom columns**: Any additional fields you need
3. **Save as .xlsx**: Excel 2007+ format
4. **Upload via API**: Use the submission service

## Validation Rules

- File size: Maximum 10MB
- File types: .xlsx, .xls, .csv, .tsv
- Row limit: 10,000 rows maximum
- Required fields cannot be empty

## Example API Upload

```bash
# Upload template
curl -X POST http://localhost:5001/api/submission/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@example_template_v1.0.xlsx"
```

## Database Storage

Data is stored with:
- Core fields (submission_date, department, category) in dedicated columns
- All other fields in JSONB column for flexibility
- Full audit trail of uploads

This design allows you to change template structure without database migrations!

---

**For more information, see the main documentation.**
