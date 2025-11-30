# Automated Email Data Extraction Tool

## Problem Description
Users currently spend excessive amounts of time manually opening recurring, standardized emails (such as invoices, order confirmations, or system status reports) and copying specific data points into spreadsheets. This process is tedious, costly, and prone to human error. A lightweight, automated solution is required to parse these emails and update records without investing in expensive enterprise automation platforms.

## Solution Overview
This Python-based utility connects to an email server via IMAP, searches for emails matching specific criteria (e.g., Subject Line), and employs Regular Expressions (Regex) to extract structured data from the email body. The data is then compiled and exported into a CSV file, which can be opened in Excel or Google Sheets.

**Key Features:**
- Secure IMAP authentication.
- Robust parsing of Multipart (Text/HTML) emails.
- customizable Regex patterns for different data types.
- Pandas-based CSV export (supports appending to existing files).

## Prerequisites
1. **Python 3.8+** installed on the machine.
2. An email account with **IMAP enabled**.
   - *Note for Gmail users:* You must enable 2-Factor Authentication and generate an **App Password**. You cannot use your standard login password.

## Installation

1. Unzip the project folder.
2. Open a terminal/command prompt in the project directory.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the same directory as the script to store your credentials securely:
   ```env
   EMAIL_USER=your_email@example.com
   EMAIL_PASS=your_app_password
   IMAP_SERVER=imap.gmail.com
   IMAP_PORT=993
   ```

## Usage

1. **Configure Patterns:** Open `email_data_extractor.py` and locate the `parse_email_body` method. Update the Regex patterns (`order_id_pattern`, etc.) to match the format of your specific emails.
2. **Run the Script:**
   ```bash
   python email_data_extractor.py
   ```
3. **View Results:** A file named `invoices_report.csv` will be created (or updated) in the directory containing the extracted data.

## Recommendations
- **Scheduling:** For full automation, use Cron (Linux/Mac) or Task Scheduler (Windows) to run this script daily or hourly.
- **Security:** Never commit your `.env` file to version control systems like GitHub.
- **Testing:** Test the Regex patterns against a few sample emails to ensure accuracy before running on a large inbox.