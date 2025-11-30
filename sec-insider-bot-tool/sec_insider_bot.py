#aiwebarchitects
import requests
import time
import argparse
import sys
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
SEC_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom"

class InsiderTradingBot:
    def __init__(self, webhook_url, min_value, interval, user_agent):
        self.webhook_url = webhook_url
        self.min_value = min_value
        self.interval = interval
        self.headers = {'User-Agent': user_agent}
        self.seen_entries = set()
        self.first_run = True

    def fetch_feed(self):
        """
        Fetches the latest filings from the SEC Atom feed.
        """
        try:
            response = requests.get(SEC_RSS_URL, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching SEC feed: {e}")
            return None

    def parse_filing_xml(self, txt_url):
        """
        Fetches the full text submission and parses the embedded XML
        to find 'Open Market Purchase' (Code P) transactions.
        """
        try:
            # SEC text archives contain the raw SGML/XML. 
            # We download the .txt file which includes the XML document.
            response = requests.get(txt_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Use lxml for speed and XML parsing capabilities
            soup = BeautifulSoup(response.content, 'xml')
            
            # Basic Info
            issuer_name = soup.find('issuerName')
            issuer_name = issuer_name.text.strip() if issuer_name else "Unknown Issuer"
            
            ticker = soup.find('issuerTradingSymbol')
            ticker = ticker.text.strip() if ticker else "UNKNOWN"
            
            owner_name = soup.find('rptOwnerName')
            owner_name = owner_name.text.strip() if owner_name else "Unknown Owner"
            
            # Find all non-derivative transactions
            transactions = soup.find_all('nonDerivativeTransaction')
            
            total_buy_value = 0.0
            buy_details = []

            for txn in transactions:
                # Check for Transaction Code 'P' (Open Market Purchase)
                coding = txn.find('transactionCoding')
                if coding:
                    code = coding.find('transactionCode')
                    if code and code.text.strip() == 'P':
                        try:
                            shares_tag = txn.find('transactionShares').find('value')
                            price_tag = txn.find('transactionPricePerShare').find('value')
                            
                            if shares_tag and price_tag:
                                shares = float(shares_tag.text)
                                price = float(price_tag.text)
                                value = shares * price
                                
                                total_buy_value += value
                                buy_details.append(f"{shares:,.0f} shares @ ${price:.2f}")
                        except (AttributeError, ValueError):
                            continue
            
            return {
                'total_value': total_buy_value,
                'ticker': ticker,
                'issuer': issuer_name,
                'owner': owner_name,
                'details': buy_details
            }

        except Exception as e:
            logger.error(f"Error parsing filing {txt_url}: {e}")
            return None

    def send_discord_alert(self, data, url):
        """
        Sends a formatted embed to Discord.
        """
        if not self.webhook_url:
            logger.info(f"[Dry Run] Alert: {data['owner']} bought ${data['total_value']:,.2f} of {data['ticker']}")
            return

        embed = {
            "title": f"📈 Insider Buy Alert: {data['ticker']}",
            "description": f"**{data['owner']}** acquired shares on the open market.",
            "url": url,
            "color": 5763719, # Green
            "fields": [
                {
                    "name": "Total Value",
                    "value": f"${data['total_value']:,.2f}",
                    "inline": True
                },
                {
                    "name": "Issuer",
                    "value": data['issuer'],
                    "inline": True
                },
                {
                    "name": "Transaction Details",
                    "value": "\n".join(data['details'][:5]) + ("..." if len(data['details']) > 5 else ""),
                    "inline": False
                }
            ],
            "footer": {
                "text": "SEC Form 4 | Real-Time Alert"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        payload = {
            "embeds": [embed]
        }

        try:
            resp = requests.post(self.webhook_url, json=payload)
            resp.raise_for_status()
            logger.info(f"Sent alert for {data['ticker']} (${data['total_value']:,.2f})")
        except Exception as e:
            logger.error(f"Failed to send Discord webhook: {e}")

    def run(self):
        logger.info(f"Starting Insider Trading Bot...")
        logger.info(f"Threshold: ${self.min_value:,.2f}")
        logger.info(f"User Agent: {self.headers['User-Agent']}")
        
        while True:
            xml_content = self.fetch_feed()
            if xml_content:
                soup = BeautifulSoup(xml_content, 'xml')
                entries = soup.find_all('entry')
                
                # Process entries from oldest to newest to maintain order
                for entry in reversed(entries):
                    try:
                        # Unique ID for the entry (Accession Number usually)
                        entry_id = entry.find('id').text
                        
                        if entry_id in self.seen_entries:
                            continue
                        
                        # Add to seen set
                        self.seen_entries.add(entry_id)
                        
                        # Skip processing on first run to avoid spamming old filings
                        if self.first_run:
                            continue

                        # Extract Link
                        link_tag = entry.find('link')
                        if not link_tag:
                            continue
                            
                        href = link_tag['href']
                        # The feed links to -index.htm. The full text is .txt
                        # Example: .../0001-24-0001-index.htm -> .../0001-24-0001.txt
                        txt_url = href.replace('-index.htm', '.txt').replace('-index.html', '.txt')
                        
                        title = entry.find('title').text
                        # Basic filter: Ensure it's a Form 4
                        if "4" not in title and "Form 4" not in title:
                            continue

                        logger.info(f"Processing new filing: {title}")
                        
                        # Parse the actual XML data
                        data = self.parse_filing_xml(txt_url)
                        
                        if data and data['total_value'] >= self.min_value:
                            self.send_discord_alert(data, href)
                            
                    except Exception as e:
                        logger.error(f"Error processing entry: {e}")

                if self.first_run:
                    logger.info("Initial feed fetch complete. Monitoring for new filings...")
                    self.first_run = False
            
            time.sleep(self.interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time SEC Insider Trading Alert Bot")
    
    parser.add_argument("--webhook", type=str, help="Discord Webhook URL", required=False)
    parser.add_argument("--threshold", type=float, default=10000.0, help="Minimum transaction value to alert (default: 10000)")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between checks (default: 60)")
    parser.add_argument("--user-agent", type=str, required=True, 
                        help="REQUIRED: User-Agent string in format 'Name email@domain.com' (SEC Requirement)")

    args = parser.parse_args()

    bot = InsiderTradingBot(
        webhook_url=args.webhook,
        min_value=args.threshold,
        interval=args.interval,
        user_agent=args.user_agent
    )
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
