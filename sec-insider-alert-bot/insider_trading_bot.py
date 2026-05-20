#aiwebarchitects
import requests
import argparse
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import json
import sys
import re

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
SEC_RSS_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&dateb=&owner=only&start=0&count=40&output=atom"

# SEC requires a User-Agent in the format: "AppName/Version (ContactEmail)"
DEFAULT_USER_AGENT = "InsiderBot/1.0 (example@domain.com)"

class InsiderTradingBot:
    def __init__(self, webhook_url, threshold, check_interval, user_agent):
        self.webhook_url = webhook_url
        self.threshold = threshold
        self.check_interval = check_interval
        self.headers = {"User-Agent": user_agent}
        self.seen_filings = set()
        self.first_run = True

    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

    def send_discord_alert(self, data):
        """Sends a formatted embed to Discord."""
        if not self.webhook_url:
            self.log("No webhook URL provided. Skipping alert.")
            return

        payload = {
            "embeds": [{
                "title": "‼️ Insider Buy Alert",
                "color": 5763719,  # Greenish
                "fields": [
                    {"name": "Issuer", "value": data['issuer'], "inline": True},
                    {"name": "Reporting Owner", "value": data['owner'], "inline": True},
                    {"name": "Total Buy Value", "value": f"${data['total_value']:,.2f}", "inline": False},
                    {"name": "Filing Date", "value": data['date'], "inline": True},
                    {"name": "Link", "value": f"[View Filing]({data['link']})", "inline": False}
                ],
                "footer": {"text": "SEC Form 4 - Open Market Purchase (Code P)"}
            }]
        }

        try:
            resp = requests.post(self.webhook_url, json=payload)
            if resp.status_code == 204:
                self.log(f"Alert sent for {data['issuer']}")
            else:
                self.log(f"Failed to send alert: {resp.status_code}")
        except Exception as e:
            self.log(f"Error sending alert: {e}")

    def get_xml_url(self, html_link):
        """
        Scrapes the filing detail page to find the primary XML document.
        Returns the URL of the .xml file or None.
        """
        try:
            response = requests.get(html_link, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for the table containing document links
            # Usually, the first row with Type '4' and Document format 'xml' is what we want
            # Or look for the link ending in .xml inside the document table
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.xml'):
                    # SEC links are relative, prepend domain
                    return f"https://www.sec.gov{href}"
            return None
        except Exception as e:
            self.log(f"Error fetching XML link: {e}")
            return None

    def parse_filing_xml(self, xml_url):
        """
        Parses the SEC Form 4 XML to calculate total 'P' (Open Market) purchases.
        """
        try:
            response = requests.get(xml_url, headers=self.headers)
            # Remove namespaces to make parsing easier with ElementTree
            xml_content = response.text
            # Strip all XML namespace declarations for easier parsing
            xml_content = re.sub(r' xmlns[^=]*="[^"]*"', '', xml_content)
            
            root = ET.fromstring(xml_content)
            
            total_purchase_value = 0.0
            found_purchase = False

            issuer_name = root.findtext('.//issuerName')
            owner_name = root.findtext('.//rptOwnerName')

            # Iterate over non-derivative transactions
            for trans in root.findall('.//nonDerivativeTransaction'):
                # Check Transaction Code
                code_tag = trans.find('.//transactionCoding/transactionCode')
                if code_tag is not None and code_tag.text == 'P':
                    # It is an open market purchase
                    shares_tag = trans.find('.//transactionAmounts/transactionShares/value')
                    price_tag = trans.find('.//transactionAmounts/transactionPricePerShare/value')
                    
                    if shares_tag is not None and price_tag is not None:
                        try:
                            shares = float(shares_tag.text)
                            price = float(price_tag.text)
                            value = shares * price
                            total_purchase_value += value
                            found_purchase = True
                        except ValueError:
                            continue

            if found_purchase:
                return {
                    "issuer": issuer_name,
                    "owner": owner_name,
                    "total_value": total_purchase_value
                }
            return None

        except Exception as e:
            self.log(f"Error parsing XML: {e}")
            return None

    def run(self):
        self.log("Starting Insider Trading Bot... (Ctrl+C to stop)")
        self.log(f"Monitoring SEC Feed. Threshold: ${self.threshold:,.2f}")

        while True:
            try:
                resp = requests.get(SEC_RSS_URL, headers=self.headers)
                if resp.status_code != 200:
                    self.log(f"Failed to fetch RSS feed: {resp.status_code}")
                    time.sleep(self.check_interval)
                    continue

                # Parse Atom Feed
                soup = BeautifulSoup(resp.content, 'xml')
                entries = soup.find_all('entry')

                # Process entries (newest first usually)
                for entry in entries:
                    id_tag = entry.find('id')
                    if not id_tag:
                        continue
                    
                    filing_id = id_tag.text
                    
                    # If first run, just populate cache to avoid spamming old alerts
                    if self.first_run:
                        self.seen_filings.add(filing_id)
                        continue

                    if filing_id in self.seen_filings:
                        continue

                    # New filing found
                    self.seen_filings.add(filing_id)
                    
                    title = entry.find('title').text
                    link = entry.find('link')['href']
                    
                    # Quick filter: ensure it's a Form 4
                    if "4" not in title and "Subject to Section 16" not in title:
                         continue

                    self.log(f"Inspecting new filing: {title}")
                    
                    # 1. Get XML URL from the filing detail page
                    xml_url = self.get_xml_url(link)
                    if not xml_url:
                        continue
                    
                    # 2. Parse XML for logic
                    data = self.parse_filing_xml(xml_url)
                    
                    # 3. Check logic
                    if data and data['total_value'] >= self.threshold:
                        data['link'] = link
                        data['date'] = datetime.now().strftime("%Y-%m-%d")
                        self.send_discord_alert(data)
                    
                    # Respect SEC rate limits (10 req/sec limit, be gentle)
                    time.sleep(0.2)

                if self.first_run:
                    self.log(f"Initial scan complete. Cached {len(self.seen_filings)} filings. Waiting for new data...")
                    self.first_run = False

            except KeyboardInterrupt:
                self.log("Stopping bot...")
                sys.exit(0)
            except Exception as e:
                self.log(f"Unexpected error in main loop: {e}")
            
            time.sleep(self.check_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Insider Trading Alert Bot")
    
    parser.add_argument("--webhook", type=str, required=True, help="Discord Webhook URL for alerts")
    parser.add_argument("--threshold", type=float, default=10000.0, help="Minimum USD value of purchase to alert (default: 10000)")
    parser.add_argument("--interval", type=int, default=60, help="Seconds to wait between feed checks (default: 60)")
    parser.add_argument("--user-agent", type=str, default=DEFAULT_USER_AGENT, help="User-Agent string (Required by SEC). Format: Name (Email)")

    args = parser.parse_args()

    bot = InsiderTradingBot(
        webhook_url=args.webhook,
        threshold=args.threshold,
        check_interval=args.interval,
        user_agent=args.user_agent
    )
    
    bot.run()