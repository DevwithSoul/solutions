#aiwebarchitects
import argparse
import time
import re
import sys
import logging
import requests
from playwright.sync_api import sync_playwright
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class RestockMonitor:
    def __init__(self, url, selector, target_price=None, keyword=None, webhook=None, interval=60, headless=True):
        """
        Initialize the monitor.
        :param url: Product URL to monitor.
        :param selector: CSS Selector for the price or status text.
        :param target_price: Float. Trigger if price is below this.
        :param keyword: String. Trigger if this text is found (e.g., "In Stock").
        :param webhook: Discord Webhook URL for notifications.
        :param interval: Check interval in seconds.
        :param headless: Run browser in headless mode.
        """
        self.url = url
        self.selector = selector
        self.target_price = target_price
        self.keyword = keyword
        self.webhook = webhook
        self.interval = interval
        self.headless = headless
        self.last_notification = 0
        self.notification_cooldown = 1800  # Don't spam notifications (30 mins cooldown)

    def send_notification(self, message):
        """Sends a notification to Discord or logs to console."""
        logger.info(f"[ALERT] {message}")
        
        if self.webhook:
            if time.time() - self.last_notification < self.notification_cooldown:
                logger.info("Notification cooldown active. Skipping webhook.")
                return

            try:
                data = {
                    "content": f"🚨 **Monitor Alert** 🚨\n{message}\n[Link to Product]({self.url})"
                }
                response = requests.post(self.webhook, json=data)
                if response.status_code == 204:
                    logger.info("Discord notification sent successfully.")
                    self.last_notification = time.time()
                else:
                    logger.error(f"Failed to send notification: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending webhook: {e}")

    def clean_price(self, text):
        """Extracts the first float number from a price string."""
        try:
            # Remove currency symbols and commas, keep dots
            # Matches digits and optional decimal
            matches = re.findall(r"[\d\.]+", text.replace(',', ''))
            if matches:
                return float(matches[0])
            return None
        except Exception:
            return None

    def check_site(self):
        """Core logic to check the website using Playwright."""
        with sync_playwright() as p:
            # Launch browser (Chromium)
            # User-Agent is set to mimic a real browser to bypass basic anti-bot
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            try:
                logger.info("Navigating to URL...")
                page.goto(self.url, wait_until="networkidle", timeout=60000)
                
                # Wait for the element to appear
                logger.info(f"Waiting for selector: {self.selector}")
                try:
                    page.wait_for_selector(self.selector, timeout=10000)
                except Exception:
                    logger.warning("Selector not found (timeout). Site might be loading slowly or selector is invalid.")
                    return

                # Get text content
                element_text = page.inner_text(self.selector).strip()
                logger.info(f"Found text: '{element_text}'")

                # LOGIC 1: Price Monitoring
                if self.target_price is not None:
                    current_price = self.clean_price(element_text)
                    if current_price is not None:
                        logger.info(f"Current Price: {current_price} | Target: {self.target_price}")
                        if current_price <= self.target_price:
                            self.send_notification(f"Price Drop Detected! Current: {current_price} (Target: {self.target_price})")
                    else:
                        logger.warning(f"Could not parse price from text: {element_text}")

                # LOGIC 2: Keyword/Restock Monitoring
                if self.keyword:
                    if self.keyword.lower() in element_text.lower():
                        self.send_notification(f"Keyword Match! Found '{self.keyword}' in element text.")

            except Exception as e:
                logger.error(f"An error occurred during check: {e}")
            finally:
                browser.close()

    def run(self):
        """Main loop."""
        logger.info("Starting Monitor... Press Ctrl+C to stop.")
        if self.target_price:
            logger.info(f"Mode: Price Monitor (< {self.target_price})")
        if self.keyword:
            logger.info(f"Mode: Keyword Monitor (Contains '{self.keyword}')")
            
        while True:
            self.check_site()
            logger.info(f"Sleeping for {self.interval} seconds...")
            time.sleep(self.interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-commerce Restock and Price Monitor")
    
    # Required Args
    parser.add_argument("--url", required=True, help="The URL to monitor")
    parser.add_argument("--selector", required=True, help="CSS Selector of the price or status text (e.g., '.price', '#stock-status')")
    
    # Optional Logic Args (At least one recommended)
    parser.add_argument("--max-price", type=float, help="Trigger alert if price is below this value")
    parser.add_argument("--keyword", type=str, help="Trigger alert if this text is found (e.g., 'In Stock')")
    
    # Config Args
    parser.add_argument("--webhook", type=str, help="Discord Webhook URL for notifications")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between checks (default: 60)")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (for debugging)")

    args = parser.parse_args()

    if not args.max_price and not args.keyword:
        print("ERROR: You must provide either --max-price OR --keyword to define a trigger condition.")
        sys.exit(1)

    monitor = RestockMonitor(
        url=args.url,
        selector=args.selector,
        target_price=args.max_price,
        keyword=args.keyword,
        webhook=args.webhook,
        interval=args.interval,
        headless=not args.visible
    )

    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\nMonitor stopped by user.")