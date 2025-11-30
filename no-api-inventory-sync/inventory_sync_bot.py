#aiwebarchitects
import requests
from bs4 import BeautifulSoup
import csv
import json
import argparse
import logging
import sys
import os
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class InventorySyncBot:
    """
    A bot designed to scrape inventory data from legacy websites without APIs.
    It extracts product details (SKU, Name, Price, Stock) and exports them to CSV/JSON.
    """

    def __init__(self, url, selectors, headers=None):
        """
        Initialize the bot.
        :param url: Target URL to scrape (or file path if local).
        :param selectors: Dictionary containing CSS selectors for 'item', 'name', 'sku', 'stock', 'price'.
        :param headers: HTTP headers for the request.
        """
        self.url = url
        self.selectors = selectors
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.inventory_data = []

    def fetch_content(self):
        """
        Fetches HTML content from a URL or a local file.
        """
        try:
            if self.url.startswith('http'):
                logger.info(f"Fetching data from remote URL: {self.url}")
                response = requests.get(self.url, headers=self.headers, timeout=15)
                response.raise_for_status()
                return response.text
            elif os.path.exists(self.url):
                logger.info(f"Reading data from local file: {self.url}")
                with open(self.url, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.error("Invalid URL or file path provided.")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch content: {str(e)}")
            return None

    def parse_html(self, html_content):
        """
        Parses the HTML content using BeautifulSoup and extracts inventory data.
        """
        if not html_content:
            return

        soup = BeautifulSoup(html_content, 'lxml')
        items = soup.select(self.selectors['item_container'])

        logger.info(f"Found {len(items)} items matching selector '{self.selectors['item_container']}'")

        for item in items:
            try:
                # Helper to safely extract text
                def get_text(selector):
                    el = item.select_one(selector)
                    return el.get_text(strip=True) if el else "N/A"

                product = {
                    'sku': get_text(self.selectors['sku']),
                    'name': get_text(self.selectors['name']),
                    'stock': self._clean_stock(get_text(self.selectors['stock'])),
                    'price': self._clean_price(get_text(self.selectors['price'])),
                    'timestamp': datetime.now().isoformat()
                }
                self.inventory_data.append(product)
            except Exception as e:
                logger.warning(f"Error parsing an item: {e}")

    def _clean_stock(self, stock_str):
        """Parses stock string to integer."""
        try:
            # Remove commmas, 'In Stock', etc.
            clean = ''.join(filter(str.isdigit, stock_str))
            return int(clean) if clean else 0
        except ValueError:
            return 0

    def _clean_price(self, price_str):
        """Parses price string to float."""
        try:
            # Remove currency symbols
            clean = price_str.replace('$', '').replace('€', '').replace(',', '')
            return float(clean)
        except ValueError:
            return 0.0

    def export_data(self, output_format='csv', filename='inventory_sync'):
        """
        Exports the parsed data to a file.
        """
        if not self.inventory_data:
            logger.warning("No data to export.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.{output_format}"

        if output_format == 'csv':
            keys = self.inventory_data[0].keys()
            with open(full_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.inventory_data)
        elif output_format == 'json':
            with open(full_filename, 'w', encoding='utf-8') as f:
                json.dump(self.inventory_data, f, indent=4)
        
        logger.info(f"Successfully exported {len(self.inventory_data)} records to {full_filename}")

# --- DEMO UTILITIES ---

def create_mock_legacy_site():
    """
    Creates a dummy HTML file to simulate a legacy supplier site.
    This ensures the user can run the code immediately to see it work.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>Legacy Parts Supply - Q3 Inventory</title></head>
    <body>
        <h1>Weekly Stock List</h1>
        <table id="inventory-table" border="1">
            <thead>
                <tr><th>SKU</th><th>Part Name</th><th>Qty On Hand</th><th>Unit Price</th></tr>
            </thead>
            <tbody>
                <tr class="product-row">
                    <td class="ref-code">WIDGET-001</td>
                    <td class="desc">Heavy Duty Widget</td>
                    <td class="qty">450</td>
                    <td class="cost">$12.99</td>
                </tr>
                <tr class="product-row">
                    <td class="ref-code">GADGET-A99</td>
                    <td class="desc">Micro Gadget v2</td>
                    <td class="qty">12</td>
                    <td class="cost">$145.50</td>
                </tr>
                <tr class="product-row">
                    <td class="ref-code">BOLT-HEX-5</td>
                    <td class="desc">Hex Bolt 5mm</td>
                    <td class="qty">2,300</td>
                    <td class="cost">$0.05</td>
                </tr>
                <tr class="product-row">
                    <td class="ref-code">OBSOLETE-X</td>
                    <td class="desc">Legacy Connector</td>
                    <td class="qty">0</td>
                    <td class="cost">$55.00</td>
                </tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    filename = "mock_legacy_site.html"
    with open(filename, "w") as f:
        f.write(html_content)
    logger.info(f"Created mock legacy site file: {filename}")
    return filename

def main():
    parser = argparse.ArgumentParser(description="No-API Inventory Sync Bot")
    
    # Arguments
    parser.add_argument('--url', help="Target URL to scrape")
    parser.add_argument('--demo', action='store_true', help="Run in demo mode with a local mock HTML file")
    parser.add_argument('--format', choices=['csv', 'json'], default='csv', help="Output format (default: csv)")
    
    # Selectors arguments (defaults geared towards the demo)
    parser.add_argument('--sel-container', default='tr.product-row', help="CSS selector for the product container")
    parser.add_argument('--sel-sku', default='.ref-code', help="CSS selector for SKU")
    parser.add_argument('--sel-name', default='.desc', help="CSS selector for Name")
    parser.add_argument('--sel-stock', default='.qty', help="CSS selector for Stock Level")
    parser.add_argument('--sel-price', default='.cost', help="CSS selector for Price")

    args = parser.parse_args()

    target_url = args.url

    # specific logic for demo mode
    if args.demo:
        logger.info("--- RUNNING IN DEMO MODE ---")
        target_url = create_mock_legacy_site()
        # Force demo selectors to ensure it works regardless of CLI args unless specified
        selectors = {
            'item_container': 'tr.product-row',
            'sku': '.ref-code',
            'name': '.desc',
            'stock': '.qty',
            'price': '.cost'
        }
    else:
        if not target_url:
            logger.error("You must provide a --url or use --demo")
            sys.exit(1)
        
        selectors = {
            'item_container': args.sel_container,
            'sku': args.sel_sku,
            'name': args.sel_name,
            'stock': args.sel_stock,
            'price': args.sel_price
        }

    # Run Bot
    bot = InventorySyncBot(target_url, selectors)
    html = bot.fetch_content()
    if html:
        bot.parse_html(html)
        bot.export_data(output_format=args.format)
        
    # Cleanup demo file
    if args.demo and os.path.exists(target_url):
        os.remove(target_url)
        logger.info("Cleaned up mock file.")

if __name__ == "__main__":
    main()