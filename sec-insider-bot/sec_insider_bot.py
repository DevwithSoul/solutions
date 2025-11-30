#aiwebarchitects
import os
import time
import json
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import argparse

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InsiderTradingBot:
    """
    A bot that monitors SEC EDGAR RSS feeds for Form 4 filings,
    parses the XML data to find Open Market Purchases (Code 'P'),
    and sends alerts to Discord if the transaction value exceeds a threshold.
    """

    # SEC EDGAR RSS Feed for Form 4 (Insider trading)
    SEC_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom"
    
    # File to store processed IDs to prevent duplicate alerts
    HISTORY_FILE = "processed_filings.json"

    def __init__(self, webhook_url, min_value=100000, user_agent="Individual investor@example.com"):
        """
        Initialize the bot.
        :param webhook_url: Discord Webhook URL.
        :param min_value: Minimum transaction value ($) to trigger an alert.
        :param user_agent: Required by SEC. Format: 'Name email@domain.com'
        """
        self.webhook_url = webhook_url
        self.min_value = min_value
        self.headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        self.processed_ids = self._load_history()

    def _load_history(self):
        """Load processed filing IDs from disk."""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    return set(json.load(f))
            except json.JSONDecodeError:
                return set()
        return set()

    def _save_history(self):
        """Save processed filing IDs to disk."""
        # Keep history small (last 1000) to prevent file bloat
        if len(self.processed_ids) > 1000:
            # Convert to list, slice, convert back to set
            recent_ids = list(self.processed_ids)[-1000:]
            self.processed_ids = set(recent_ids)
            
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump(list(self.processed_ids), f)

    def fetch_rss_feed(self):
        """Fetch and parse the SEC RSS feed."""
        try:
            # feedparser handles the HTTP request, but we need custom headers for SEC
            # So we fetch raw content first
            response = requests.get(self.SEC_RSS_URL, headers=self.headers, timeout=10)
            response.raise_for_status()
            return feedparser.parse(response.content)
        except Exception as e:
            logger.error(f"Error fetching RSS feed: {e}")
            return None

    def get_xml_url(self, link):
        """
        Convert the standard HTML index link to the raw XML link.
        Standard Link: https://www.sec.gov/Archives/edgar/data/123/456/456-index.htm
        Target Link:   https://www.sec.gov/Archives/edgar/data/123/456/primary_doc.xml
        
        Note: The filename isn't always primary_doc.xml, but usually the first xml in the directory.
        For robustness, we will request the index page and scrape the XML link.
        """
        try:
            # Fetch the index page
            resp = requests.get(link, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.content, 'html.parser')
            
            # Look for the document table
            # We want the link where Type is '4' and Format is 'XML' usually
            # Simplified logic: Find the first link ending in .xml inside the table
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href.endswith('.xml') and 'xslF345' not in href:
                    # Construct full URL
                    return "https://www.sec.gov" + href
            return None
        except Exception as e:
            logger.error(f"Error extracting XML URL from {link}: {e}")
            return None

    def parse_form_4(self, xml_url):
        """
        Download and parse the Form 4 XML to extract transaction data.
        Returns a summary dictionary or None.
        """
        try:
            resp = requests.get(xml_url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.content, 'xml') # Use XML parser

            # Extract Issuer and Owner
            issuer_name = soup.find('issuerName').text if soup.find('issuerName') else "Unknown"
            ticker = soup.find('issuerTradingSymbol').text if soup.find('issuerTradingSymbol') else "Unknown"
            owner_name = soup.find('rptOwnerName').text if soup.find('rptOwnerName') else "Unknown"
            is_officer = soup.find('isOfficer').text if soup.find('isOfficer') else "0"
            is_director = soup.find('isDirector').text if soup.find('isDirector') else "0"
            is_ten_percent = soup.find('isTenPercentOwner').text if soup.find('isTenPercentOwner') else "0"

            title = []
            if is_director == '1' or is_director == 'true': title.append("Director")
            if is_officer == '1' or is_officer == 'true': 
                officer_title = soup.find('officerTitle').text if soup.find('officerTitle') else "Officer"
                title.append(officer_title)
            if is_ten_percent == '1' or is_ten_percent == 'true': title.append("10% Owner")
            
            owner_title = ", ".join(title) if title else "Insider"

            # Process Non-Derivative Transactions
            transactions = soup.find_all('nonDerivativeTransaction')
            
            total_buy_value = 0.0
            total_shares = 0.0
            avg_price = 0.0

            found_purchase = False

            for trans in transactions:
                # Check transaction code
                trans_code = trans.find('transactionCode')
                if not trans_code or trans_code.get('transactionCode') != 'P':
                    continue # Skip if not 'P' (Open Market Purchase)

                # Get shares and price
                shares_tag = trans.find('transactionShares')
                price_tag = trans.find('transactionPricePerShare')
                
                if shares_tag and price_tag:
                    try:
                        shares = float(shares_tag.find('value').text)
                        price = float(price_tag.find('value').text)
                        
                        total_buy_value += (shares * price)
                        total_shares += shares
                        found_purchase = True
                    except (ValueError, AttributeError):
                        continue

            if not found_purchase or total_buy_value < self.min_value:
                return None

            if total_shares > 0:
                avg_price = total_buy_value / total_shares

            return {
                "ticker": ticker,
                "issuer": issuer_name,
                "owner": owner_name,
                "title": owner_title,
                "total_value": total_buy_value,
                "shares": total_shares,
                "price": avg_price,
                "url": xml_url
            }

        except Exception as e:
            logger.error(f"Error parsing XML {xml_url}: {e}")
            return None

    def send_discord_alert(self, data):
        """Send a formatted embed to Discord."""
        if not self.webhook_url:
            logger.warning("No Webhook URL provided. Skipping alert.")
            return

        formatted_value = "${:,.2f}".format(data['total_value'])
        formatted_price = "${:,.2f}".format(data['price'])
        formatted_shares = "{:,.0f}".format(data['shares'])

        embed = {
            "title": f"🚨 Insider Buy Alert: {data['ticker']}",
            "description": f"**{data['owner']}** ({data['title']}) just bought shares.",
            "url": data['url'],
            "color": 5763719, # Green-ish
            "fields": [
                {
                    "name": "Total Value",
                    "value": formatted_value,
                    "inline": True
                },
                {
                    "name": "Shares Bought",
                    "value": formatted_shares,
                    "inline": True
                },
                {
                    "name": "Avg Price",
                    "value": formatted_price,
                    "inline": True
                },
                {
                    "name": "Company",
                    "value": data['issuer'],
                    "inline": False
                }
            ],
            "footer": {
                "text": "SEC Form 4 Real-Time Monitor"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        payload = {
            "embeds": [embed]
        }

        try:
            resp = requests.post(self.webhook_url, json=payload)
            if resp.status_code in [200, 204]:
                logger.info(f"Alert sent for {data['ticker']}")
            else:
                logger.error(f"Failed to send Discord alert: {resp.status_code} {resp.text}")
        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    def run(self):
        """Main polling loop."""
        logger.info(f"Starting Insider Trading Bot. Threshold: ${self.min_value:,.2f}")
        logger.info("Press Ctrl+C to stop.")
        
        while True:
            feed = self.fetch_rss_feed()
            if feed:
                # RSS entries are usually ordered newest first. 
                # We reverse to process oldest to newest in this batch if multiple arrived.
                for entry in reversed(feed.entries):
                    # Create a unique ID for this filing based on the link or ID provided by RSS
                    filing_id = entry.id if 'id' in entry else entry.link
                    
                    if filing_id in self.processed_ids:
                        continue

                    logger.info(f"Processing new filing: {entry.title}")
                    
                    # Get the HTML link to the filing index
                    link = entry.link
                    
                    # Resolve to XML
                    xml_url = self.get_xml_url(link)
                    
                    if xml_url:
                        # Parse
                        data = self.parse_form_4(xml_url)
                        if data:
                            self.send_discord_alert(data)
                        else:
                            logger.info("Filing processed: No significant purchase found.")
                    else:
                        logger.warning(f"Could not find XML URL for {link}")

                    # Mark as processed regardless of result to avoid infinite loops
                    self.processed_ids.add(filing_id)
                    self._save_history()
                    
                    # Be polite to SEC servers (max 10 req/sec allowed, we go much slower)
                    time.sleep(0.2)

            # Wait before checking RSS again. SEC filings don't happen every second.
            # 60 seconds is a reasonable poll interval.
            time.sleep(60)

if __name__ == "__main__":
    # Simple Argument Parsing
    parser = argparse.ArgumentParser(description='SEC Form 4 Insider Trading Bot')
    parser.add_argument('--webhook', type=str, required=True, help='Discord Webhook URL')
    parser.add_argument('--threshold', type=int, default=100000, help='Minimum USD value to alert (default: 100k)')
    parser.add_argument('--user-agent', type=str, required=True, help='User-Agent string (Name email@domain.com)')
    
    args = parser.parse_args()

    bot = InsiderTradingBot(
        webhook_url=args.webhook, 
        min_value=args.threshold,
        user_agent=args.user_agent
    )
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
