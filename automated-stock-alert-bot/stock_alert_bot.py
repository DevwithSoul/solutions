#aiwebarchitects
import requests
from bs4 import BeautifulSoup
import time
import argparse
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class StockMonitor:
    def __init__(self, url, selector, search_text, webhook_url, check_interval, headers=None, negative_match=False):
        """
        Initialize the Stock Monitor.
        
        :param url: The URL of the product page.
        :param selector: The CSS selector to find the stock status element.
        :param search_text: The text to look for inside the element.
        :param webhook_url: Discord Webhook URL for notifications.
        :param check_interval: Time in seconds between checks.
        :param headers: HTTP headers to mimic a browser.
        :param negative_match: If True, alerts when text is NOT found (e.g., alert if 'Out of Stock' is gone).
        """
        self.url = url
        self.selector = selector
        self.search_text = search_text.lower()
        self.webhook_url = webhook_url
        self.check_interval = check_interval
        self.negative_match = negative_match
        
        # Default headers to mimic a real browser to avoid 403 Forbidden errors
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        self.last_status = None

    def check_stock(self):
        """
        Fetches the page and checks for stock availability.
        Returns True if stock is found (based on criteria), False otherwise.
        """
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            element = soup.select_one(self.selector)
            
            if not element:
                logger.warning(f"Element with selector '{self.selector}' not found on page.")
                return False, "ElementNotFound"
            
            element_text = element.get_text(strip=True).lower()
            logger.debug(f"Found text: '{element_text}'")

            # Logic: 
            # If negative_match is False (default): Alert if 'search_text' IS in 'element_text' (e.g., "In Stock")
            # If negative_match is True: Alert if 'search_text' IS NOT in 'element_text' (e.g., "Out of Stock" disappeared)
            
            found_text = self.search_text in element_text
            
            if self.negative_match:
                is_in_stock = not found_text
            else:
                is_in_stock = found_text
                
            return is_in_stock, element_text
            
        except requests.RequestException as e:
            logger.error(f"Network error: {e}")
            return False, "Error"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False, "Error"

    def send_notification(self, current_text):
        """Sends a notification to Discord via Webhook."""
        if not self.webhook_url:
            logger.info("Stock detected! (No webhook URL provided for alert)")
            return

        data = {
            "content": f"🚨 **STOCK ALERT!** 🚨\n\nItem detected in stock!\n**URL:** {self.url}\n**Status Text:** {current_text}\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        try:
            result = requests.post(self.webhook_url, json=data)
            result.raise_for_status()
            logger.info("Notification sent successfully!")
        except requests.RequestException as e:
            logger.error(f"Failed to send notification: {e}")

    def start(self):
        """Main loop."""
        logger.info(f"Starting monitoring for: {self.url}")
        logger.info(f"Target Selector: {self.selector}")
        logger.info(f"Trigger Condition: '{self.search_text}' (Negative Match: {self.negative_match})")
        
        # Send a startup message to verify webhook
        if self.webhook_url:
            try:
                requests.post(self.webhook_url, json={"content": f"🤖 Bot started monitoring: {self.url}"})
            except: 
                logger.warning("Could not send startup message. Check Webhook URL.")

        while True:
            is_in_stock, current_text = self.check_stock()
            
            if is_in_stock:
                logger.info(f"SUCCESS: Stock detected! Text found: '{current_text}'")
                self.send_notification(current_text)
                # Optional: Break loop or sleep longer to avoid spamming alerts
                # For this example, we sleep for 5 minutes after a success to give user time to buy
                time.sleep(300) 
            else:
                logger.info(f"Not in stock. (Checked text: '{current_text}' vs Target: '{self.search_text}')")
            
            time.sleep(self.check_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automated Stock Alert Bot')
    
    parser.add_argument('--url', required=True, help='The URL of the product page to monitor')
    parser.add_argument('--selector', required=True, help='CSS selector for the status element (e.g., ".stock-status" or "#add-to-cart")')
    parser.add_argument('--text', required=True, help='Text to match (e.g., "In Stock" or "Sold Out")')
    parser.add_argument('--webhook', required=False, help='Discord Webhook URL for notifications')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds (default: 30)')
    parser.add_argument('--negative', action='store_true', help='Trigger alert if text is NOT found (e.g., alert if "Sold Out" is missing)')
    
    args = parser.parse_args()
    
    bot = StockMonitor(
        url=args.url,
        selector=args.selector,
        search_text=args.text,
        webhook_url=args.webhook,
        check_interval=args.interval,
        negative_match=args.negative
    )
    
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        sys.exit(0)
