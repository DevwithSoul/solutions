#aiwebarchitects
import argparse
import time
import logging
import sys
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class InsiderSignalBot:
    def __init__(self, webhook_url, min_value, check_interval, user_agent):
        self.webhook_url = webhook_url
        self.min_value = min_value
        self.check_interval = check_interval
        self.headers = {'User-Agent': user_agent}
        self.seen_guids = set()
        
        # SEC EDGAR RSS Feed for Form 4 (Statement of Changes in Beneficial Ownership)
        self.rss_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom"

    def fetch_rss_feed(self):
        """
        Fetches the latest Form 4 filings from the SEC RSS feed.
        """
        try:
            logger.info("Polling SEC EDGAR RSS feed...")
            # feedparser handles the HTTP request internally but doesn't easily allow custom headers for User-Agent
            # which SEC requires. So we fetch raw content first.
            response = requests.get(self.rss_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            return feed.entries
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return []

    def get_xml_url(self, filing_url):
        """
        The RSS feed gives a link to the HTML index page. 
        We need to scrape this page to find the primary XML document link.
        """
        try:
            response = requests.get(filing_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the table row containing the XML document
            # Usually the first row in the 'Document Format Files' table
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) > 3:
                    doc_type = cells[3].text.strip()
                    if 'xml' in doc_type.lower() or '4' in doc_type: # Often labeled '4' or 'XML'
                        link = row.find('a')['href']
                        if link.endswith('.xml'):
                            return "https://www.sec.gov" + link
            return None
        except Exception as e:
            logger.error(f"Error finding XML URL from {filing_url}: {e}")
            return None

    def parse_transaction(self, xml_url):
        """
        Parses the Form 4 XML to calculate total Open Market Purchase value.
        Returns a dictionary with transaction details if it meets criteria, else None.
        """
        try:
            response = requests.get(xml_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'xml') # Use XML parser
            
            # Basic Info
            issuer_name = soup.find('issuerName').text if soup.find('issuerName') else "Unknown"
            ticker = soup.find('issuerTradingSymbol').text if soup.find('issuerTradingSymbol') else "Unknown"
            reporting_owner = soup.find('rptOwnerName').text if soup.find('rptOwnerName') else "Unknown"
            
            # Check relationship (Officer, Director, 10% Owner)
            is_officer = soup.find('isOfficer')
            is_director = soup.find('isDirector')
            is_ten_percent = soup.find('isTenPercentOwner')
            
            titles = []
            if is_officer and is_officer.text == '1': titles.append(soup.find('officerTitle').text if soup.find('officerTitle') else "Officer")
            if is_director and is_director.text == '1': titles.append("Director")
            if is_ten_percent and is_ten_percent.text == '1': titles.append("10% Owner")
            title_str = ", ".join(titles)

            total_buy_value = 0.0
            shares_bought = 0
            avg_price = 0.0
            
            # Iterate over non-derivative transactions
            transactions = soup.find_all('nonDerivativeTransaction')
            for t in transactions:
                # Check Transaction Code
                # 'P' = Open Market Purchase
                code_tag = t.find('transactionCode')
                if code_tag and code_tag.text.strip().upper() == 'P':
                    try:
                        shares = float(t.find('transactionShares').find('value').text)
                        price_per_share = float(t.find('transactionPricePerShare').find('value').text)
                        
                        # Verify it's an acquisition (A) just in case, though P implies it
                        # code 'P' is strictly purchase, but checking acquired/disposed code is safe
                        ad_code = t.find('transactionAcquiredDisposedCode').find('value').text.strip().upper()
                        
                        if ad_code == 'A':
                            total_buy_value += (shares * price_per_share)
                            shares_bought += shares
                    except (AttributeError, ValueError):
                        continue
            
            if total_buy_value >= self.min_value:
                avg_price = total_buy_value / shares_bought if shares_bought > 0 else 0
                return {
                    'ticker': ticker,
                    'company': issuer_name,
                    'insider': reporting_owner,
                    'title': title_str,
                    'total_value': total_buy_value,
                    'shares': shares_bought,
                    'price': avg_price,
                    'filing_url': xml_url
                }
            
            return None

        except Exception as e:
            logger.error(f"Error parsing XML {xml_url}: {e}")
            return None

    def send_alert(self, data):
        """
        Sends a formatted alert to the Discord/Slack Webhook.
        """
        if not self.webhook_url:
            logger.info(f"[ALERT SIMULATION] {data['ticker']} - Insider {data['insider']} bought ${data['total_value']:,.2f}")
            return

        # Create a rich embed structure for Discord
        payload = {
            "username": "Insider Signal Bot",
            "embeds": [{
                "title": f"🚨 Insider Buy Alert: {data['ticker']}",
                "description": f"High-value open market purchase detected.",
                "color": 5763719, # Greenish
                "fields": [
                    {"name": "Company", "value": data['company'], "inline": True},
                    {"name": "Insider", "value": data['insider'], "inline": True},
                    {"name": "Role", "value": data['title'], "inline": False},
                    {"name": "Total Value", "value": f"${data['total_value']:,.2f}", "inline": True},
                    {"name": "Shares", "value": f"{data['shares']:,.0f}", "inline": True},
                    {"name": "Avg Price", "value": f"${data['price']:,.2f}", "inline": True}
                ],
                "url": data['filing_url'],
                "footer": {"text": "Source: SEC EDGAR • Open Market (P)"},
                "timestamp": datetime.utcnow().isoformat()
            }]
        }

        try:
            r = requests.post(self.webhook_url, json=payload)
            r.raise_for_status()
            logger.info(f"Alert sent for {data['ticker']}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")

    def run(self):
        logger.info(f"Starting Insider Signal Bot (Threshold: ${self.min_value:,.2f})")
        logger.info("Press Ctrl+C to stop.")
        
        # Initial fetch to populate seen_guids so we don't spam old alerts on startup
        initial_entries = self.fetch_rss_feed()
        for entry in initial_entries:
            self.seen_guids.add(entry.id)
        logger.info(f"Initialized with {len(self.seen_guids)} existing filings. Waiting for new data...")

        while True:
            try:
                entries = self.fetch_rss_feed()
                
                # Process entries in reverse (oldest first) to maintain chronological order of alerts
                for entry in reversed(entries):
                    if entry.id not in self.seen_guids:
                        self.seen_guids.add(entry.id)
                        
                        # The link in the RSS entry points to the index page
                        index_url = entry.link
                        
                        # Find the actual XML file
                        xml_url = self.get_xml_url(index_url)
                        
                        if xml_url:
                            logger.info(f"Analyzing filing for {entry.title}...")
                            signal = self.parse_transaction(xml_url)
                            if signal:
                                self.send_alert(signal)
                            else:
                                logger.debug("Filing did not meet criteria (routine or low value).")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("Stopping bot...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEC EDGAR Insider Buy Monitor")
    
    parser.add_argument("--webhook", type=str, help="Discord/Slack Webhook URL (optional, prints to console if omitted)")
    parser.add_argument("--threshold", type=float, default=10000.0, help="Minimum transaction value to alert (default: $10,000)")
    parser.add_argument("--interval", type=int, default=60, help="Seconds to wait between checks (default: 60)")
    parser.add_argument("--email", type=str, required=True, help="Your email address (REQUIRED by SEC for User-Agent header)")
    
    args = parser.parse_args()
    
    # Construct a compliant User-Agent
    # Format: "AppName/Version (ContactEmail)"
    user_agent = f"InsiderSignalBot/1.0 ({args.email})"
    
    bot = InsiderSignalBot(
        webhook_url=args.webhook,
        min_value=args.threshold,
        check_interval=args.interval,
        user_agent=user_agent
    )
    
    bot.run()