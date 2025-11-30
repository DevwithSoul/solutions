#aiwebarchitects
import argparse
import time
import requests
import feedparser
from bs4 import BeautifulSoup
import logging
import sys
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
SEC_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom"
SEEN_ENTRIES = set()

class InsiderTradingBot:
    def __init__(self, user_agent, webhook_url=None, threshold=10000, interval=60):
        self.headers = {'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}
        self.webhook_url = webhook_url
        self.threshold = threshold
        self.interval = interval
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_rss_feed(self):
        """Fetches the latest Form 4 filings from SEC RSS feed."""
        try:
            response = self.session.get(SEC_RSS_URL, timeout=10)
            if response.status_code == 200:
                return feedparser.parse(response.content)
            else:
                logger.error(f"Failed to fetch RSS feed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return None

    def get_xml_link(self, index_url):
        """Scrapes the filing index page to find the primary XML document link."""
        try:
            response = self.session.get(index_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the XML file in the document table
            # Usually the first row with type '4' and format 'xml'
            tables = soup.find_all('table', class_='tableFile')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) > 3:
                        doc_type = cols[3].text.strip()
                        doc_href = cols[2].find('a')['href']
                        # We want the main XML document
                        if doc_type == '4' and doc_href.endswith('.xml'):
                            return f"https://www.sec.gov{doc_href}"
            return None
        except Exception as e:
            logger.error(f"Error extracting XML link from {index_url}: {e}")
            return None

    def parse_transaction_xml(self, xml_url):
        """Parses the Form 4 XML to calculate total purchase value."""
        try:
            response = self.session.get(xml_url, timeout=10)
            soup = BeautifulSoup(response.content, 'xml') # Using XML parser

            issuer_name = soup.find('issuerName').text if soup.find('issuerName') else "Unknown Company"
            ticker = soup.find('issuerTradingSymbol').text if soup.find('issuerTradingSymbol') else "UNKNOWN"
            
            reporting_owner = soup.find('rptOwnerName').text if soup.find('rptOwnerName') else "Unknown Owner"
            is_director = soup.find('isDirector').text if soup.find('isDirector') else "0"
            is_officer = soup.find('isOfficer').text if soup.find('isOfficer') else "0"
            is_ten_percent = soup.find('isTenPercentOwner').text if soup.find('isTenPercentOwner') else "0"

            transactions = soup.find_all('nonDerivativeTransaction')
            total_purchase_value = 0.0
            purchase_details = []

            for t in transactions:
                # Check for Transaction Code 'P' (Purchase)
                # 'A' is Grant (Award), 'S' is Sale. We want 'P'.
                trans_code = t.find('transactionCode').text if t.find('transactionCode') else ''
                
                if trans_code == 'P':
                    try:
                        shares = float(t.find('transactionShares').find('value').text)
                        price = float(t.find('transactionPricePerShare').find('value').text)
                        value = shares * price
                        total_purchase_value += value
                        purchase_details.append(f"Bought {int(shares):,} @ ${price:.2f}")
                    except (AttributeError, ValueError):
                        continue

            return {
                'issuer': issuer_name,
                'ticker': ticker,
                'owner': reporting_owner,
                'total_value': total_purchase_value,
                'details': purchase_details,
                'roles': {
                    'Director': is_director,
                    'Officer': is_officer,
                    '10% Owner': is_ten_percent
                }
            }

        except Exception as e:
            logger.error(f"Error parsing XML {xml_url}: {e}")
            return None

    def send_alert(self, data, link):
        """Sends notification to console and optional Webhook."""
        title = f"🚨 INSIDER BUY: {data['ticker']} - ${data['total_value']:,.2f}"
        roles = [k for k, v in data['roles'].items() if v == '1' or v == 'true' or v == True]
        role_str = ", ".join(roles) if roles else "Insider"
        
        msg = (
            f"{title}\n"
            f"👤 {data['owner']} ({role_str})\n"
            f"🏢 {data['issuer']}\n"
            f"💰 Total: ${data['total_value']:,.2f}\n"
            f"📝 Details: {', '.join(data['details'])}\n"
            f"🔗 Link: {link}"
        )

        logger.info("\n" + "="*50 + "\n" + msg + "\n" + "="*50)

        if self.webhook_url:
            payload = {
                "content": f"**{title}**\n> {msg}"
            }
            try:
                requests.post(self.webhook_url, json=payload)
            except Exception as e:
                logger.error(f"Failed to send webhook: {e}")

    def run(self):
        logger.info(f"Starting SEC Insider Trading Bot.")
        logger.info(f"Tracking Form 4 Purchases > ${self.threshold:,.2f}")
        logger.info("Press Ctrl+C to stop.")

        while True:
            feed = self.fetch_rss_feed()
            if feed:
                # Process entries (newest first)
                for entry in feed.entries:
                    entry_id = entry.id
                    
                    # Skip if already seen
                    if entry_id in SEEN_ENTRIES:
                        continue
                    
                    SEEN_ENTRIES.add(entry_id)
                    
                    # Only process recently seen entries to avoid flood on startup
                    # (In a real DB implementation, we would check against DB timestamp)
                    
                    # Extract URL to the filing index
                    filing_href = entry.link
                    
                    # 1. Get XML Link
                    xml_link = self.get_xml_link(filing_href)
                    if not xml_link:
                        continue

                    # 2. Parse XML for 'P' codes
                    data = self.parse_transaction_xml(xml_link)
                    
                    # 3. Check Threshold and Alert
                    if data and data['total_value'] >= self.threshold:
                        self.send_alert(data, filing_href)
                    
                    # Respect SEC rate limits (ensure we don't hit 10 req/sec)
                    time.sleep(0.2)
            
            # Clean up SEEN_ENTRIES if it gets too big (simple memory management)
            if len(SEEN_ENTRIES) > 10000:
                SEEN_ENTRIES.clear()

            logger.info(f"Sleeping for {self.interval} seconds...")
            time.sleep(self.interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time SEC Insider Trading Alert System")
    
    # REQUIRED: SEC requires a User-Agent with contact info (e.g., email)
    parser.add_argument("--email", required=True, help="Your email address for SEC User-Agent compliance (REQUIRED)")
    
    parser.add_argument("--webhook", help="Discord/Slack Webhook URL for alerts")
    parser.add_argument("--threshold", type=float, default=10000.0, help="Minimum purchase value to trigger alert (default: 10000)")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between RSS checks (default: 60)")

    args = parser.parse_args()

    # Construct compliant user agent: "AppName/Version (Email)"
    user_agent = f"InsiderBot/1.0 ({args.email})"

    bot = InsiderTradingBot(
        user_agent=user_agent,
        webhook_url=args.webhook,
        threshold=args.threshold,
        interval=args.interval
    )

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
