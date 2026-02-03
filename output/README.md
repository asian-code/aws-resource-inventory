# Output Directory

This directory contains the generated Excel inventory reports.

Files are named: `aws-inventory-YYYY-MM-DD_HH-MM-SS.xlsx`

## Example Output

Each Excel file contains:
- **Summary** sheet with scan statistics
- Individual sheets for each resource type (35 total)
- **Errors-Skipped** sheet for any issues encountered

## Retention

- Files are not tracked in git (excluded in .gitignore)
- Consider archiving or deleting old reports periodically
