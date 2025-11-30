#aiwebarchitects
import time
import argparse
import logging
import sys
import re
from datetime import datetime
import requests
import feedparser
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class SECInsiderBot:
    """
    Monitors SEC EDGAR RSS feeds for Form 4 filings.
    Filters for Open Market Purchases (Transaction Code 'P') to distinguish
    real buys from stock grants.
    """

    # SEC EDGAR RSS Feed for Form 4 (Statement of changes in beneficial ownership of securities)
    RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom"

    def __init__(self, webhook_url, user_agent_name, user_agent_email, poll_interval=60):
        self.webhook_url = webhook_url
        self.headers = {
            # SEC requires a specific User-Agent format: "AppName/Version AdminContactEmail"
            "User-Agent": f"{user_agent_name} {user_agent_email}",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        self.poll_interval = poll_interval
        self.seen_entries = set()
        self.first_run = True

    def fetch_rss_feed(self):
        """Parses the SEC Atom feed."""
        try:
            # feedparser handles the HTTP request, but we need custom headers for SEC
            # So we fetch raw content first
            response = requests.get(self.RSS_URL, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch RSS feed: {response.status_code}")
                return []
            
            feed = feedparser.parse(response.content)
            return feed.entries
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return []

    def get_xml_url_from_index(self, index_url):
        """
        The RSS feed links to an HTML index page.
        We need to scrape this page to find the raw XML filing link.
        """
        try:
            response = requests.get(index_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the table row containing the XML document
            # Usually labeled as Type '4' or 'XML'
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) > 3:
                    doc_type = cells[3].text.strip()
                    if 'xml' in doc_type.lower() or doc_type == '4':
                        link = row.find('a', href=True)
                        if link and link['href'].endswith('.xml'):
                            return "https://www.sec.gov" + link['href']
            return None
        except Exception as e:
            logger.error(f"Error parsing index page {index_url}: {e}")
            return None

    def parse_filing_xml(self, xml_url):
        """
        Fetches the XML filing and sums up Open Market Purchases (Code 'P').
        Returns a dictionary of trade data if purchases exist, else None.
        """
        try:
            response = requests.get(xml_url, headers=self.headers, timeout=10)
            # Remove namespace prefixes to make parsing easier (simple regex strip)
            xml_content = re.sub(' xmlns="[^"]+"', '', response.text, count=1)
            root = ET.fromstring(xml_content)

            transactions = []
            total_value = 0.0
            
            # Extract Issuer Info
            issuer_symbol = root.findtext('.//issuerTradingSymbol')
            
            # Extract Reporting Owner
            rpt_owner = root.find('.//reportingOwnerId')
            owner_name = rpt_owner.findtext('.//rptOwnerName') if rpt_owner else "Unknown"
            is_director = rpt_owner.findtext('.//isDirector') == '1' or rpt_owner.findtext('.//isDirector') == 'true' if rpt_owner else False
            is_officer = rpt_owner.findtext('.//isOfficer') == '1' or rpt_owner.findtext('.//isOfficer') == 'true' if rpt_owner else False
            officer_title = rpt_owner.findtext('.//officerTitle') if rpt_owner else ""

            # Iterate non-derivative transactions (actual stock trades)
            for trans in root.findall('.//nonDerivativeTransaction'):
                # Check transaction code
                trans_code = trans.findtext('.//transactionCoding/transactionCode')
                acquired_code = trans.findtext('.//transactionAmounts/transactionAcquiredDisposedCode')

                # 'P' = Open market or private purchase of non-derivative or derivative security
                # 'A' = Acquired (Buy)
                if trans_code == 'P' and acquired_code == 'A':
                    shares = float(trans.findtext('.//transactionAmounts/transactionShares/value') or 0)
                    price = float(trans.findtext('.//transactionAmounts/transactionPricePerShare/value') or 0)
                    
                    value = shares * price
                    total_value += value
                    transactions.append({
                        'shares': shares,
                        'price': price,
                        'value': value
                    })

            if total_value > 0:
                return {
                    'symbol': issuer_symbol,
                    'owner': owner_name,
                    'title': officer_title if officer_title else ('Director' if is_director else 'Insider'),
                    'total_value': total_value,
                    'avg_price': total_value / sum(t['shares'] for t in transactions),
                    'total_shares': sum(t['shares'] for t in transactions),
                    'link': xml_url
                }
            return None

        except Exception as e:
            logger.error(f"Error parsing XML {xml_url}: {e}")
            return None

    def send_discord_alert(self, data, filing_url):
        """Sends a formatted embed to Discord."""
        if not self.webhook_url:
            logger.info(f"[Dry Run] Alert: {data['owner']} bought ${data['total_value']:,.2f} of {data['symbol']}")
            return

        embed = {
            "title": f"🚨 Insider Buy Alert: {data['symbol']}",
            "description": f"**{data['owner']}** ({data['title']}) just filed a Form 4.",
            "url": filing_url,
            "color": 5763719,  # Green
            "fields": [
                {
                    "name": "Total Value",
                    "value": f"${data['total_value']:,.2f}",
                    "inline": True
                },
                {
                    "name": "Shares Bought",
                    "value": f"{data['total_shares']:,.0f}",
                    "inline": True
                },
                {
                    "name": "Avg Price",
                    "value": f"${data['avg_price']:,.2f}",
                    "inline": True
                }
            ],
            "footer": {
                "text": "SEC EDGAR Real-Time Monitor"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        payload = {
            "embeds": [embed],
            "username": "Insider Bot"
        }

        try:
            requests.post(self.webhook_url, json=payload)
            logger.info(f"Discord alert sent for {data['symbol']}")
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")

    def run(self):
        """Main execution loop."""
        logger.info(f"Starting SEC Insider Bot...")
        logger.info(f"Poll Interval: {self.poll_interval}s")
        logger.info("Waiting for new filings...")

        while True:
            entries = self.fetch_rss_feed()
            
            # On first run, just populate seen entries so we don't alert on old data
            if self.first_run:
                for entry in entries:
                    self.seen_entries.add(entry.id)
                self.first_run = False
                logger.info(f"Initialized. Tracking {len(self.seen_entries)} existing filings.")
            else:
                # Check newest entries first
                for entry in entries:
                    if entry.id not in self.seen_entries:
                        self.seen_entries.add(entry.id)
                        logger.info(f"New Filing Detected: {entry.title}")
                        
                        # 1. Get Index URL from RSS
                        index_url = entry.link
                        
                        # 2. Scrape Index to find XML URL
                        xml_url = self.get_xml_url_from_index(index_url)
                        
                        if xml_url:
                            # 3. Parse XML to check for 'P' codes
                            trade_data = self.parse_filing_xml(xml_url)
                            
                            if trade_data:
                                logger.info(f"VALID BUY SIGNAL: {trade_data['symbol']} - ${trade_data['total_value']}")
                                self.send_discord_alert(trade_data, index_url)
                            else:
                                logger.info("Ignored: No open market purchases found (likely a grant/award).")
                        
                        # Respect SEC Rate Limits (10 req/sec allowed, but we play safe)
                        time.sleep(0.5)

            time.sleep(self.poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEC Insider Trade Discord Bot")
    parser.add_argument("--webhook", type=str, required=True, help="Discord Webhook URL")
    parser.add_argument("--name", type=str, required=True, help="Your Name/Company (for SEC User-Agent)")
    parser.add_argument("--email", type=str, required=True, help="Your Email (for SEC User-Agent)")
    parser.add_argument("--interval", type=int, default=60, help="Polling interval in seconds")

    args = parser.parse_args()

    bot = SECInsiderBot(
        webhook_url=args.webhook,
        user_agent_name=args.name,
        user_agent_email=args.email,
        poll_interval=args.interval
    )

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")