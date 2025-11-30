#aiwebarchitects
import imaplib
import email
from email.header import decode_header
import re
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file for security
load_dotenv()

class EmailDataExtractor:
    def __init__(self):
        """
        Initialize the extractor with credentials and server settings.
        """
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', 993))
        self.mail = None

    def connect(self):
        """
        Establish a secure connection to the IMAP server.
        """
        try:
            print(f"Connecting to {self.imap_server}...")
            self.mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.mail.login(self.email_user, self.email_pass)
            print("Login successful.")
        except Exception as e:
            print(f"Connection failed: {e}")
            raise

    def parse_email_body(self, body_content):
        """
        Extract specific data points using Regex.
        Adjust the patterns below based on the specific standardized email format.
        
        Example Email Format assumed:
        'Order ID: #12345'
        'Date: 2023-10-27'
        'Total Amount: $500.00'
        """
        data = {}
        
        # Regex Patterns - MODIFY THESE based on your actual email content
        order_id_pattern = r"Order ID:\s*#?(\w+)"
        amount_pattern = r"Total Amount:\s*\$?([\d,]+\.\d{2})"
        date_pattern = r"Date:\s*([\d-]{10})"

        # Extraction
        order_match = re.search(order_id_pattern, body_content, re.IGNORECASE)
        amount_match = re.search(amount_pattern, body_content, re.IGNORECASE)
        date_match = re.search(date_pattern, body_content, re.IGNORECASE)

        data['Order_ID'] = order_match.group(1) if order_match else None
        data['Amount'] = float(amount_match.group(1).replace(',', '')) if amount_match else 0.0
        data['Date'] = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')
        
        return data

    def extract_emails(self, folder="INBOX", subject_keyword="Invoice"):
        """
        Search for emails and extract data.
        :param folder: Mailbox folder to search.
        :param subject_keyword: Keyword to filter emails by subject.
        """
        if not self.mail:
            self.connect()

        self.mail.select(folder)
        
        # Search for emails with specific subject
        # ALL means all emails, you can refine this search criteria
        status, messages = self.mail.search(None, f'(SUBJECT "{subject_keyword}")')
        
        email_ids = messages[0].split()
        extracted_records = []

        print(f"Found {len(email_ids)} emails matching subject '{subject_keyword}'.Processing...")

        for e_id in email_ids:
            try:
                # Fetch the email
                res, msg_data = self.mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode Subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        # Get Email Body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                # Look for plain text first, then html
                                if "attachment" not in content_disposition:
                                    if content_type == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break # Prefer plain text for regex
                                    elif content_type == "text/html":
                                        body = part.get_payload(decode=True).decode()
                        else:
                            body = msg.get_payload(decode=True).decode()

                        # Extract Data
                        record = self.parse_email_body(body)
                        record['Email_Subject'] = subject # Optional: keep track of source
                        
                        # Only add if we actually found distinct data
                        if record['Order_ID']:
                            extracted_records.append(record)
                            
            except Exception as e:
                print(f"Error processing email ID {e_id}: {e}")
                continue

        return extracted_records

    def save_to_csv(self, data, filename="extracted_data.csv"):
        """
        Save the list of dictionaries to a CSV file using Pandas.
        """
        if not data:
            print("No data extracted to save.")
            return

        df = pd.DataFrame(data)
        
        # Reorder columns if needed
        cols = ['Date', 'Order_ID', 'Amount', 'Email_Subject']
        # Ensure columns exist before reordering
        cols = [c for c in cols if c in df.columns]
        df = df[cols]

        # Append if file exists, else create new
        if os.path.isfile(filename):
            df.to_csv(filename, mode='a', header=False, index=False)
            print(f"Data appended to {filename}")
        else:
            df.to_csv(filename, index=False)
            print(f"Data saved to new file {filename}")

    def close(self):
        """
        Close the connection.
        """
        if self.mail:
            self.mail.close()
            self.mail.logout()
            print("Connection closed.")

if __name__ == "__main__":
    # Configuration
    OUTPUT_FILE = "invoices_report.csv"
    SUBJECT_FILTER = "Order Confirmation" # Change this to match your target emails

    extractor = EmailDataExtractor()
    try:
        records = extractor.extract_emails(subject_keyword=SUBJECT_FILTER)
        extractor.save_to_csv(records, filename=OUTPUT_FILE)
        print("Process completed successfully.")
    except Exception as main_e:
        print(f"Critical Error: {main_e}")
    finally:
        extractor.close()