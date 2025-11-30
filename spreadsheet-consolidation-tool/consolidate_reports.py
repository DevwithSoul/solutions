#aiwebarchitects
import os
import glob
import argparse
import pandas as pd
import re
from datetime import datetime

def normalize_header(header):
    """
    Normalizes a single header string.
    Example: '  First Name ' -> 'first_name'
    """
    if not isinstance(header, str):
        return str(header)
    # Strip whitespace, convert to lowercase, replace spaces/special chars with underscores
    clean = header.strip().lower()
    clean = re.sub(r'[^a-z0-9]+', '_', clean)
    clean = clean.strip('_')
    return clean

def extract_metadata_from_filename(filename):
    """
    Extracts metadata from the filename.
    Assumes a convention like 'Category_YYYY-MM-DD.csv' or just captures the raw name.
    Returns a dictionary of metadata.
    """
    base_name = os.path.basename(filename)
    name_without_ext = os.path.splitext(base_name)[0]
    
    metadata = {
        'source_filename': base_name,
        'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Try to find a date in the filename (YYYY-MM-DD)
    date_match = re.search(r'\d{4}-\d{2}-\d{2}', name_without_ext)
    if date_match:
        metadata['extracted_date'] = date_match.group(0)
    
    # split by underscore to try and get categories/regions
    parts = name_without_ext.split('_')
    if len(parts) > 1:
        metadata['category_guess'] = parts[0]
        
    return metadata

def process_files(input_dir, output_file, file_pattern):
    """
    Main logic to read, normalize, and merge files.
    """
    all_dataframes = []
    
    # Find all matching files
    search_path = os.path.join(input_dir, file_pattern)
    files = glob.glob(search_path)
    
    if not files:
        print(f"[!] No files found in {input_dir} matching {file_pattern}")
        return

    print(f"[*] Found {len(files)} files to process.")

    for file_path in files:
        try:
            print(f"    -> Processing: {os.path.basename(file_path)}")
            
            # Determine loader based on extension
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                print(f"    [!] Skipping unsupported format: {file_path}")
                continue

            # Normalize Headers
            # This ensures 'Product Name' and 'product_name' end up in the same column
            df.columns = [normalize_header(col) for col in df.columns]

            # Extract and inject metadata
            meta = extract_metadata_from_filename(file_path)
            for key, value in meta.items():
                df[key] = value

            all_dataframes.append(df)
            
        except Exception as e:
            print(f"    [ERROR] Could not process {file_path}: {e}")

    if not all_dataframes:
        print("[!] No data extracted. Exiting.")
        return

    # Consolidate
    print("[*] Merging dataframes...")
    master_df = pd.concat(all_dataframes, ignore_index=True, sort=False)

    # Export
    try:
        if output_file.endswith('.csv'):
            master_df.to_csv(output_file, index=False)
        else:
            master_df.to_excel(output_file, index=False)
        print(f"[SUCCESS] Master report created: {output_file}")
        print(f"          Total Rows: {len(master_df)}")
        print(f"          Total Columns: {len(master_df.columns)}")
    except Exception as e:
        print(f"[ERROR] Could not save master file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Spreadsheet Consolidation Tool")
    
    parser.add_argument(
        '--input', 
        type=str, 
        required=True, 
        help="Directory containing the CSV/Excel files to merge"
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default="master_report.xlsx", 
        help="Filename for the output report (default: master_report.xlsx)"
    )
    
    parser.add_argument(
        '--pattern', 
        type=str, 
        default="*.*", 
        help="File pattern to match (e.g., '*.csv' or 'sales_*.xlsx')"
    )

    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.input):
        print(f"[ERROR] Input directory '{args.input}' does not exist.")
    else:
        process_files(args.input, args.output, args.pattern)

# Example Usage:
# python consolidate_reports.py --input "./weekly_data" --output "./final_report.xlsx"
# python consolidate_reports.py --input "./data" --pattern "*.csv" --output "merged.csv"