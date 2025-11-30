# Bulk File Renamer via Excel Mapping

## Problem Description
Manually renaming thousands of files based on data stored in spreadsheets (like SKU lists, employee IDs, or product metadata) is error-prone and extremely time-consuming. Users often have a directory of files (e.g., `IMG_001.jpg`, `IMG_002.jpg`) and an Excel sheet mapping these generic names to descriptive ones (e.g., `Product_A.jpg`, `Product_B.jpg`).

## Solution Overview
This Python automation tool reads a mapping file (Excel or CSV) and iterates through a specified directory. It matches files based on a source column and renames them to the value found in a target column. 

**Key Features:**
- **Safety First:** Includes a `--dry-run` mode to preview changes before applying them.
- **Format Support:** Works with `.xlsx` (Excel) and `.csv` files.
- **Smart Handling:** Automatically preserves file extensions by default (e.g., renaming `file` to `newname` becomes `newname.jpg` if the source was `.jpg`).
- **Sanitization:** Removes illegal characters from new filenames to prevent filesystem errors.

## Prerequisites
- Python 3.7 or higher installed on your system.

## Installation

1. Download and unzip the tool.
2. Open a terminal or command prompt in the folder.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Command
```bash
python bulk_renamer.py --map "data/mapping.xlsx" --dir "./images" --old-col "OriginalName" --new-col "NewName"
```

### Dry Run (Recommended First Step)
Use `--dry-run` to see what *would* happen without changing any files.
```bash
python bulk_renamer.py --map "mapping.xlsx" --dir "./files" --old-col "id" --new-col "sku" --dry-run
```

### Arguments
- `--map`: Path to the spreadsheet (.xlsx or .csv).
- `--dir`: Folder containing the files to rename.
- `--old-col`: The exact header name in the spreadsheet for the current filename.
- `--new-col`: The exact header name in the spreadsheet for the desired filename.
- `--dry-run`: (Optional) Flag to print actions without executing.
- `--no-ext-preserve`: (Optional) Flag to stop the script from automatically keeping the file extension.

## Configuration (Excel Setup)
Ensure your Excel file looks something like this (headers can be named anything, just pass them to the CLI args):

| OriginalName | NewName      |
|--------------|--------------|
| IMG_1001.jpg | product_a    |
| IMG_1002.jpg | product_b    |

*Note: If `NewName` does not have an extension (like .jpg), the script automatically adds the extension from the original file unless `--no-ext-preserve` is used.*

## Recommendations
1. **Always run a Dry Run first** to verify your column names and mapping logic.
2. Ensure the spreadsheet does not contain duplicate names in the `NewName` column to avoid overwriting files.
3. Close the Excel file before running the script to avoid file lock errors.