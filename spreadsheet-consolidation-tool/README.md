# Automated Spreadsheet Consolidation Tool

## Problem Description
Manually merging dozens of CSV or Excel files into a single master report is time-consuming and error-prone. Inconsistent column headers (e.g., "Email" vs "email address") and the need to track which file data came from make this task difficult to automate with simple copy-pasting.

## Solution Overview
This Python utility automates the consolidation process. It:
1. Scans a directory for CSV or Excel files.
2. Normalizes column headers (converts to snake_case) to ensure data aligns correctly across files.
3. Extracts metadata from filenames (e.g., dates, source names) and adds them as new columns.
4. Merges everything into a single Master Excel (.xlsx) or CSV file.

## Prerequisites
- **Python 3.7+** installed on your system.

## Installation
1. Download the script.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the script from the command line.

### Basic Usage
Merge all files in the `data` folder into a generic Excel report:
```bash
python consolidate_reports.py --input "./data"
```

### Custom Output
Specify the output filename (supports .csv or .xlsx):
```bash
python consolidate_reports.py --input "./data" --output "October_Summary.csv"
```

### Filtering Files
Only merge files matching a specific pattern:
```bash
python consolidate_reports.py --input "./data" --pattern "sales_*.xlsx"
```

## How it Works
1. **Header Normalization**: It cleans headers. ` First Name ` becomes `first_name`. This aligns columns even if formatting differs slightly between files.
2. **Metadata Injection**: It adds a column `source_filename` to every row so you know the origin of the data. It also attempts to regex extract dates (YYYY-MM-DD) from the filename.

## Recommendations
- Ensure your input files have a generally similar structure (files don't need to be identical, but should share core columns).
- Use the `--pattern` argument if your folder contains unrelated files.