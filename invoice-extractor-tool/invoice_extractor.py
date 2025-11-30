#aiwebarchitects
import os
import re
import argparse
import pandas as pd
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# ==========================================
# CONFIGURATION & PATTERNS
# ==========================================
# These Regex patterns are designed for a generic invoice format.
# In a production environment, these might need tuning for specific vendor layouts.
REGEX_PATTERNS = {
    "invoice_number": r"Invoice\s*(?:Number|#)?\s*[:.]?\s*([A-Za-z0-9-]+)",
    "date": r"Date\s*[:.]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})",
    "total_amount": r"Total\s*(?:Amount)?\s*[:.]?\s*\$?\s*([\d,]+\.\d{2})"
}

def generate_sample_pdf(folder_path):
    """
    Generates a dummy PDF invoice for testing purposes.
    This ensures the user can run the script immediately without having their own files ready.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    filename = os.path.join(folder_path, "sample_invoice_001.pdf")
    c = canvas.Canvas(filename, pagesize=letter)
    
    # Draw some text that mimics a standard invoice
    c.drawString(100, 750, "ACME Corp Invoice")
    c.drawString(100, 730, "123 Business Rd, Business City")
    
    c.drawString(100, 680, "Invoice Number: INV-2023-001")
    c.drawString(100, 660, "Date: 2023-10-27")
    
    c.drawString(100, 600, "Description              Amount")
    c.drawString(100, 580, "--------------------------------")
    c.drawString(100, 560, "Web Development          $500.00")
    c.drawString(100, 540, "Hosting (1 Year)         $120.00")
    
    c.drawString(100, 500, "Total Amount: $620.00")
    
    c.save()
    print(f"[INFO] Generated sample invoice at: {filename}")

def extract_data_from_pdf(pdf_path):
    """
    Opens a single PDF and attempts to extract fields based on REGEX_PATTERNS.
    Returns a dictionary of extracted data.
    """
    data = {
        "filename": os.path.basename(pdf_path),
        "invoice_number": None,
        "date": None,
        "total_amount": None,
        "status": "Success"
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Usually invoices fit on the first page. 
            # Iterate pages if necessary, but page 0 is standard for headers/totals.
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text_content = first_page.extract_text()
                
                if not text_content:
                    data["status"] = "No Text Found (Scanned Image?)"
                    return data

                # Apply Regex Patterns
                for key, pattern in REGEX_PATTERNS.items():
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        # Group 1 contains the actual value
                        data[key] = match.group(1)
                    else:
                        data[key] = "Not Found"
            else:
                data["status"] = "Empty PDF"

    except Exception as e:
        data["status"] = f"Error: {str(e)}"
        
    return data

def process_directory(input_dir, output_file):
    """
    Iterates through all PDFs in the input directory, extracts data,
    and saves the result to an Excel file.
    """
    if not os.path.exists(input_dir):
        print(f"[ERROR] Input directory '{input_dir}' does not exist.")
        return

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"[WARN] No PDF files found in '{input_dir}'.")
        return

    print(f"[INFO] Found {len(pdf_files)} PDF files. Processing...")
    
    extracted_results = []

    for pdf_file in pdf_files:
        full_path = os.path.join(input_dir, pdf_file)
        print(f"Processing: {pdf_file}...")
        result = extract_data_from_pdf(full_path)
        extracted_results.append(result)

    # Create DataFrame and Export
    if extracted_results:
        df = pd.DataFrame(extracted_results)
        
        # Reorder columns for readability
        cols = ["filename", "invoice_number", "date", "total_amount", "status"]
        df = df[cols]
        
        try:
            df.to_excel(output_file, index=False)
            print(f"\n[SUCCESS] Extraction complete! Data saved to: {output_file}")
            print(df.head())
        except Exception as e:
            print(f"[ERROR] Could not write to Excel file: {e}")
            print("Ensure the file is not open in another program.")
    else:
        print("[INFO] No data extracted.")

def main():
    parser = argparse.ArgumentParser(description="Automated PDF Invoice Data Extractor")
    
    parser.add_argument('--input', '-i', type=str, required=True, 
                        help='Folder path containing PDF invoices')
    parser.add_argument('--output', '-o', type=str, default='invoice_data.xlsx', 
                        help='Output Excel filename (default: invoice_data.xlsx)')
    parser.add_argument('--generate-sample', action='store_true', 
                        help='Generate a sample invoice PDF in the input folder for testing')

    args = parser.parse_args()

    # 1. Generate sample if requested
    if args.generate_sample:
        generate_sample_pdf(args.input)

    # 2. Process the directory
    process_directory(args.input, args.output)

if __name__ == "__main__":
    main()