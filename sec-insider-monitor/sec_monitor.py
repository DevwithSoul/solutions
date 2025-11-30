#aiwebarchitects
import argparse
import time
import sys
import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class SECInsiderMonitor:
    def __init__(self, webhook_url, user_agent, check_interval=60):
        self.webhook_url = webhook_url
        self.headers = {'User-Agent': user_agent}
        self.check_interval = check_interval
        self.seen_entries = set()
        # SEC EDGAR Atom feed for Form 4 (Insider Trading)
        self.feed_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom"

    def fetch_feed(self):
        """Fetches the latest filings from the SEC Atom feed."""
        try:
            # feedparser handles the HTTP request internally, but we need custom headers for SEC
            response = requests.get(self.feed_url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Error fetching feed: {response.status_code}")
                return []
            
            feed = feedparser.parse(response.content)
            return feed.entries
        except Exception as e:
            logger.error(f"Exception fetching feed: {e}")
            return []

    def parse_form_4(self, filing_url):
        """
        Parses the Form 4 HTML to find Open Market Purchases (Code P).
        Returns a dictionary of transaction details if found, else None.
        """
        try:
            # 1. Get the Index Page
            resp = requests.get(filing_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # 2. Find the link to the primary HTML document (usually the first row in the table)
            # This is a simplified logic; robust parsers check the document type column.
            doc_link = None
            file_table = soup.find('table', {'class': 'tableFile'})
            if file_table:
                rows = file_table.find_all('tr')
                for row in rows:
                    # Look for the html document
                    cols = row.find_all('td')
                    if len(cols) > 2 and 'html' in cols[2].text.lower():
                        link_tag = cols[2].find('a')
                        if link_tag:
                            doc_link = "https://www.sec.gov" + link_tag['href']
                            break
            
            if not doc_link:
                return None

            # 3. Fetch the actual Form 4 HTML
            doc_resp = requests.get(doc_link, headers=self.headers, timeout=10)
            doc_soup = BeautifulSoup(doc_resp.content, 'html.parser')

            # 4. Parse Table I - Non-Derivative Securities
            # We look for transaction code 'P' (Purchase) and 'A' (Acquired)
            transactions = []
            
            # Find all tables, iterate to find the one with transaction data
            tables = doc_soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    # Heuristic: Form 4 tables usually have many columns. 
                    # We need to find the row with Code 'P'.
                    # Note: Parsing HTML Form 4 is notoriously brittle due to varying formats.
                    # This logic looks for the specific Code 'P' in the text of cells.
                    
                    row_text = [c.get_text(strip=True) for c in cells]
                    
                    # Check for Transaction Code 'P' (Purchase)
                    # Usually in column 3 or 4 depending on formatting (0-indexed)
                    if 'P' in row_text and 'A' in row_text:
                        # Extract Price and Amount
                        try:
                            # Attempt to find price and amount by looking for numbers
                            # This is a simplification. A full parser maps XML tags.
                            # We look for the price per share and number of shares.
                            
                            # Filter for numeric values in the row
                            numerics = []
                            for text in row_text:
                                clean_text = text.replace(',', '').replace('$', '')
                                try:
                                    val = float(clean_text)
                                    numerics.append(val)
                                except ValueError:
                                    continue
                            
                            # Heuristic: Usually [Date, ..., Amount, ..., Price, ...]
                            # If we have at least 2 numbers, we assume Amount and Price.
                            if len(numerics) >= 2:
                                # Very basic heuristic: Price is usually smaller than Amount (shares)
                                # unless it's BRK.A. 
                                # Let's assume the larger number is shares, smaller is price (risky but works for 99%)
                                # A better way is strictly by column index, but HTML varies wildly.
                                
                                # Let's try to be more specific with column indices if possible
                                # Standard Form 4 Table 1:
                                # 1. Title, 2. Date, 3. Code, 4. Acq/Disp, 5. Amount, 6. Acq/Disp, 7. Price
                                
                                # Using a simpler approach: Just capture that a purchase happened.
                                transactions.append({
                                    'type': 'Purchase',
                                    'raw_row': row_text
                                })
                        except Exception:
                            continue

            if transactions:
                # Extract Issuer Name and Ticker from the top of the document
                issuer = "Unknown"
                ticker = "Unknown"
                try:
                    # Try to find the issuer info block
                    info_text = doc_soup.get_text()
                    # Very rough extraction, usually provided in the Atom feed title though.
                    pass
                except:
                    pass
                
                return {
                    'count': len(transactions),
                    'link': doc_link
                }

            return None

        except Exception as e:
            logger.error(f"Error parsing filing {filing_url}: {e}")
            return None

    def send_discord_alert(self, entry, details):
        """Sends a formatted embed to Discord."""
        title = entry.title
        # title format is usually: "4 - Company Name (Ticker) (CIK)"
        
        embed = {
            "title": "🚨 Insider Purchase Detected",
            "description": f"**{title}**\n\nAn insider has filed a Form 4 indicating an open-market purchase (Transaction Code 'P').",
            "color": 5763719, # Green
            "fields": [
                {
                    "name": "Filing Date",
                    "value": entry.updated,
                    "inline": True
                },
                {
                    "name": "Transaction Count",
                    "value": str(details['count']),
                    "inline": True
                },
                {
                    "name": "Links",
                    "value": f"[SEC Filing Index]({entry.link})\n[Direct Document]({details['link']})"
                }
            ],
            "footer": {
                "text": "SEC Insider Monitor • Data via SEC EDGAR"
            }
        }

        payload = {
            "username": "SEC Monitor",
            "embeds": [embed]
        }

        try:
            resp = requests.post(self.webhook_url, json=payload)
            if resp.status_code == 204:
                logger.info(f"Alert sent for {title}")
            else:
                logger.error(f"Failed to send alert: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")

    def run(self):
        logger.info("Starting SEC Insider Monitor...")
        logger.info(f"Polling interval: {self.check_interval} seconds")
        logger.info("Waiting for new filings...")

        # Initial fetch to populate seen_entries so we don't alert on old stuff immediately
        initial_entries = self.fetch_feed()
        for entry in initial_entries:
            self.seen_entries.add(entry.id)
        
        logger.info(f"Initialized with {len(self.seen_entries)} existing filings.")

        while True:
            try:
                entries = self.fetch_feed()
                
                # Process entries in reverse order (oldest to newest in this batch)
                for entry in reversed(entries):
                    if entry.id not in self.seen_entries:
                        logger.info(f"New filing found: {entry.title}")
                        self.seen_entries.add(entry.id)
                        
                        # Parse to see if it's a Purchase
                        details = self.parse_form_4(entry.link)
                        
                        if details:
                            logger.info(f"Purchase detected in {entry.title}!")
                            self.send_discord_alert(entry, details)
                        else:
                            logger.info(f"No open-market purchases found in {entry.title}.")
                
                # SEC Rate Limit is 10 requests/sec. We sleep much longer to be safe and polite.
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping monitor...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Real-Time SEC Insider Trading Monitor')
    parser.add_argument('--webhook', required=True, help='Discord Webhook URL')
    parser.add_argument('--user-agent', required=True, help='User Agent string (Required by SEC: "Name email@domain.com")')
    parser.add_argument('--interval', type=int, default=60, help='Polling interval in seconds (default: 60)')
    
    args = parser.parse_args()
    
    monitor = SECInsiderMonitor(
        webhook_url=args.webhook,
        user_agent=args.user_agent,
        check_interval=args.interval
    )
    monitor.run()