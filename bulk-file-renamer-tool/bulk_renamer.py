#aiwebarchitects
import os
import sys
import argparse
import pandas as pd
from pathlib import Path

def sanitize_filename(filename):
    """
    Removes characters that are unsafe for filenames.
    """
    # Common invalid characters in Windows/Linux filesystems
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename.strip()

def rename_files(mapping_file, search_dir, old_col, new_col, dry_run=False, keep_ext=True):
    """
    Renames files based on a mapping spreadsheet.
    
    Args:
        mapping_file (str): Path to the Excel/CSV file.
        search_dir (str): Directory containing the files to rename.
        old_col (str): Column header for current filenames.
        new_col (str): Column header for new filenames.
        dry_run (bool): If True, only prints what would happen.
        keep_ext (bool): If True, preserves the original file extension.
    """
    
    # 1. Load the Mapping Data
    print(f"\nLoading mapping file: {mapping_file}...")
    try:
        if mapping_file.lower().endswith('.csv'):
            df = pd.read_csv(mapping_file)
        else:
            # Requires openpyxl for xlsx
            df = pd.read_excel(mapping_file)
    except Exception as e:
        print(f"[Error] Could not read mapping file: {e}")
        sys.exit(1)

    # 2. Validate Columns
    if old_col not in df.columns or new_col not in df.columns:
        print(f"[Error] Columns '{old_col}' and/or '{new_col}' not found in the spreadsheet.")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    # Clean NaN values
    df = df.dropna(subset=[old_col, new_col])
    
    search_path = Path(search_dir)
    if not search_path.exists():
        print(f"[Error] Search directory does not exist: {search_dir}")
        sys.exit(1)

    success_count = 0
    error_count = 0
    skipped_count = 0

    print(f"Processing {len(df)} rows... {'(DRY RUN)' if dry_run else ''}")
    print("-" * 60)

    # 3. Iterate and Rename
    for index, row in df.iterrows():
        current_name = str(row[old_col]).strip()
        target_name_raw = str(row[new_col]).strip()
        
        source_file = search_path / current_name
        
        # Check if source file exists
        if not source_file.exists():
            print(f"[Skip] Source not found: {current_name}")
            skipped_count += 1
            continue

        # Handle Extensions
        original_ext = source_file.suffix
        target_name = sanitize_filename(target_name_raw)
        
        if keep_ext and not target_name.lower().endswith(original_ext.lower()):
            target_name += original_ext
            
        target_file = search_path / target_name

        # Prevent overwriting existing files
        if target_file.exists() and target_file != source_file:
            print(f"[Error] Target exists: {target_name} (Skipping to prevent overwrite)")
            error_count += 1
            continue
        
        # Perform Rename
        try:
            if dry_run:
                print(f"[Dry-Run] Would rename: '{current_name}' -> '{target_name}'")
                success_count += 1
            else:
                source_file.rename(target_file)
                print(f"[Success] Renamed: '{current_name}' -> '{target_name}'")
                success_count += 1
        except Exception as e:
            print(f"[Error] Failed to rename {current_name}: {e}")
            error_count += 1

    # 4. Summary
    print("-" * 60)
    print(f"Summary: {success_count} processed, {skipped_count} skipped, {error_count} errors.")
    if dry_run:
        print("This was a Dry Run. No files were actually changed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk rename files using an Excel/CSV map.")
    
    parser.add_argument("--map", required=True, help="Path to the Excel (.xlsx) or CSV file containing the mapping.")
    parser.add_argument("--dir", required=True, help="Directory containing the files to be renamed.")
    parser.add_argument("--old-col", required=True, help="Column header name for the CURRENT filenames.")
    parser.add_argument("--new-col", required=True, help="Column header name for the NEW filenames.")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without actually renaming files.")
    parser.add_argument("--no-ext-preserve", action="store_true", help="Do NOT automatically append original extension to new name.")

    args = parser.parse_args()

    rename_files(
        mapping_file=args.map,
        search_dir=args.dir,
        old_col=args.old_col,
        new_col=args.new_col,
        dry_run=args.dry_run,
        keep_ext=not args.no_ext_preserve
    )