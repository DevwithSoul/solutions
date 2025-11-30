#aiwebarchitects
import os
import re
import csv
import logging
import pdfplumber
from typing import List, Dict, Optional

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FOLDER = 'invoices'
OUTPUT_FILE = 'extracted_data.csv'
LOG_FILE = 'extraction.log'

# Regex Patterns for extraction
# These patterns assume standard formats like "Invoice #: 12345" or "Total: $500.00"
# Modify these based on specific vendor layouts.
PATTERNS = {
    'invoice_number': r'Invoice\s*(?:Number|#)?[:\s]+([A-Za-z0-9\-]+)',
    'date': r'Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    'total_amount': r'Total(?:\s+Amount)?[:\s]+\$?([\d,]+\.\d{2})'
}

# ==========================================
# LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class InvoiceExtractor:
    """
    Handles the logic for opening PDF files, extracting text, 
    and parsing specific data points based on regex patterns.
    """

    def __init__(self, input_dir: str, output_path: str):
        self.input_dir = input_dir
        self.output_path = output_path
        self._ensure_directories()

    def _ensure_directories(self):
        """Creates input directory if it doesn't exist to avoid errors."""
        if not os.path.exists(self.input_dir):
            os.makedirs(self.input_dir)
            logger.info(f"Created input directory: {self.input_dir}")
            logger.info("Please place PDF invoices in this folder and restart the script.")

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Uses pdfplumber to extract text from the first page of a PDF.
        Using pdfplumber is preferred over PyPDF2 for better layout preservation.
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Invoices usually have summary data on the first page
                if len(pdf.pages) > 0:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text()
        except Exception as e:
            logger.error(f"Failed to read PDF {file_path}: {e}")
        return text

    def parse_data(self, text: str) -> Dict[str, str]:
        """
        Applies regex patterns to the extracted raw text to find specific fields.
        """
        data = {}
        for key, pattern in PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Group 1 contains the actual value, not the label
                data[key] = match.group(1)
            else:
                data[key] = "N/A"
        return data

    def run(self):
        """
        Main execution flow: Iterate files -> Extract -> Parse -> Save to CSV.
        """
        if not os.path.exists(self.input_dir) or not os.listdir(self.input_dir):
            logger.warning(f"No files found in '{self.input_dir}'. Please add PDF files.")
            return

        results = []
        files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.pdf')]
        
        logger.info(f"Found {len(files)} PDF files to process.")

        for filename in files:
            file_path = os.path.join(self.input_dir, filename)
            logger.info(f"Processing: {filename}")
            
            raw_text = self.extract_text_from_pdf(file_path)
            if raw_text:
                parsed_data = self.parse_data(raw_text)
                parsed_data['filename'] = filename # Add filename for reference
                results.append(parsed_data)
            else:
                logger.warning(f"No text extracted from {filename}. It might be an image-only PDF.")

        self.save_to_csv(results)

    def save_to_csv(self, data: List[Dict[str, str]]):
        """
        Writes the list of dictionaries to a CSV file.
        """
        if not data:
            logger.info("No data to save.")
            return

        # Get headers from the keys of the first dictionary
        headers = ['filename'] + list(PATTERNS.keys())

        try:
            with open(self.output_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            logger.info(f"Successfully saved data to {self.output_path}")
        except IOError as e:
            logger.error(f"Could not write to CSV file: {e}")

if __name__ == "__main__":
    # Entry point for the script
    extractor = InvoiceExtractor(INPUT_FOLDER, OUTPUT_FILE)
    extractor.run()
