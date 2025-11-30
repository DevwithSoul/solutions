# Automated PDF Invoice Data Extractor

## Problem Description
Administrative staff currently spend excessive hours manually opening PDF invoices, locating specific data points (such as Invoice Numbers, Dates, and Total Amounts), and typing them into Excel. This manual process is slow, unscalable, and prone to human error (typos, missed decimals). Generic online converters often fail because they try to convert the entire PDF layout rather than extracting specific business-critical fields.

## Solution Overview
This tool is a production-ready Python automation script designed to:
1.  **Batch Process:** Automatically iterate through a designated folder of PDF files.
2.  **Intelligent Extraction:** Use `pdfplumber` for high-accuracy text extraction that respects PDF layout better than standard libraries.
3.  **Pattern Matching:** Utilize robust Regular Expressions (Regex) to identify and capture specific data points regardless of where they appear on the page.
4.  **Structured Output:** Export the clean, extracted data directly into a CSV file ready for Excel or database import.

## Prerequisites
*   **Python 3.7+** installed on your machine.
*   **pip** (Python package manager).

## Installation
1.  Download and unzip the `invoice-extractor-tool`.
2.  Open your terminal or command prompt in the project directory.
3.  Install the required dependency:
    ```bash
    pip install pdfplumber
    ```

## Usage
1.  **Prepare Folders:** Run the script once to generate the `invoices` folder, or manually create a folder named `invoices` in the same directory as the script.
2.  **Load Data:** Copy all your PDF invoice files into the `invoices` folder.
3.  **Run Script:** Execute the Python script:
    ```bash
    python invoice_extractor.py
    ```
4.  **View Results:** Open the newly created `extracted_data.csv` file in Excel or any text editor to view your data. Check `extraction.log` for any errors or files that were skipped.

## Recommendations
*   **Regex Customization:** The regex patterns in the `CONFIGURATION` section of the code are designed for standard invoice formats. If you deal with specific vendors that have unique layouts, adjust the patterns in the `PATTERNS` dictionary.
*   **OCR Support:** If your PDFs are scanned images (not text-selectable), this script will return empty text. For scanned documents, integrate `pytesseract` (OCR) to read the images before parsing.
*   **Scheduling:** For continuous automation, use Windows Task Scheduler or a Cron job to run this script daily.