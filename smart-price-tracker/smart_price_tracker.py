#aiwebarchitects
import asyncio
import argparse
import re
import sys
import time
import logging
import requests
from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SmartPriceTracker:
    """
    A class to handle headless browsing, price scraping, and notification delivery.
    """
    def __init__(self, url, price_selector, target_price, webhook_url, stock_selector=None, interval=None):
        self.url = url
        self.price_selector = price_selector
        self.target_price = target_price
        self.webhook_url = webhook_url
        self.stock_selector = stock_selector
        self.interval = interval
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

    def parse_price(self, price_str):
        """
        Cleans a price string and converts it to a float.
        Removes currency symbols and commas.
        Example: '$1,299.99' -> 1299.99
        """
        if not price_str:
            return None
        # Remove non-numeric characters except period
        clean_str = re.sub(r'[^0-9.]', '', price_str)
        try:
            return float(clean_str)
        except ValueError:
            logger.error(f"Could not parse price string: {price_str}")
            return None

    def send_notification(self, current_price, in_stock=True):
        """
        Sends a notification via a Webhook (e.g., Discord, Slack).
        """
        message = (
            f"🚨 **Price Alert!** 🚨\n"
            f"**Product:** {self.url}\n"
            f"**Current Price:** ${current_price}\n"
            f"**Target Price:** ${self.target_price}\n"
            f"**Status:** {'In Stock' if in_stock else 'Out of Stock'}"
        )
        
        payload = {"content": message, "text": message} # 'content' for Discord, 'text' for Slack

        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code in [200, 204]:
                logger.info("Notification sent successfully.")
            else:
                logger.error(f"Failed to send notification. Status Code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    async def check_product(self):
        """
        Launches browser, navigates to URL, and extracts data.
        """
        async with async_playwright() as p:
            # Launch browser (headless=True for production, False for debugging)
            browser = await p.chromium.launch(headless=True)
            
            # Create context with custom user agent to mimic a real user
            context = await browser.new_context(user_agent=self.user_agent)
            page = await context.new_page()

            try:
                logger.info(f"Navigating to {self.url}...")
                await page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait for the price selector to appear
                logger.info("Waiting for price element...")
                await page.wait_for_selector(self.price_selector, timeout=10000)

                # Extract Price
                price_text = await page.inner_text(self.price_selector)
                current_price = self.parse_price(price_text)
                
                # Check Stock (if selector provided)
                in_stock = True
                if self.stock_selector:
                    try:
                        # If selector exists, we check text. Logic depends on site specific text.
                        # Here we assume if the element exists and doesn't say 'Out of Stock', it's good.
                        stock_text = await page.inner_text(self.stock_selector)
                        if "out of stock" in stock_text.lower() or "unavailable" in stock_text.lower():
                            in_stock = False
                    except Exception:
                        # If selector is meant to show "Out of Stock" label and it's missing, it might be in stock
                        # Or if the selector is positive "In Stock", handle accordingly.
                        # For this generic tool, we log warning but proceed.
                        logger.warning("Stock selector not found or ambiguous.")

                logger.info(f"Found Price: {current_price} | Target: {self.target_price}")

                # Logic: Alert if price is below target AND item is in stock
                if current_price is not None and current_price <= self.target_price:
                    if in_stock:
                        logger.info("Target met! Sending alert...")
                        self.send_notification(current_price, in_stock)
                    else:
                        logger.info("Price met but item is Out of Stock.")
                else:
                    logger.info("Price is above target.")

            except Exception as e:
                logger.error(f"An error occurred during scraping: {e}")
                # Optional: Send error notification to webhook if critical
            finally:
                await browser.close()

    async def run(self):
        """
        Main loop. Runs once or continuously based on interval.
        """
        if self.interval:
            logger.info(f"Starting monitoring with {self.interval}s interval.")
            while True:
                await self.check_product()
                await asyncio.sleep(self.interval)
        else:
            await self.check_product()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Price Tracker & Inventory Alert System")
    
    # Required Arguments
    parser.add_argument("--url", required=True, help="The URL of the product to track")
    parser.add_argument("--price-selector", required=True, help="CSS Selector for the price element (e.g., '.price', '#product-price')")
    parser.add_argument("--target-price", required=True, type=float, help="The maximum price you are willing to pay")
    parser.add_argument("--webhook-url", required=True, help="Discord or Slack Webhook URL for notifications")
    
    # Optional Arguments
    parser.add_argument("--stock-selector", help="CSS Selector to check stock status (optional)")
    parser.add_argument("--interval", type=int, help="Time in seconds between checks (if omitted, runs once)")

    args = parser.parse_args()

    tracker = SmartPriceTracker(
        url=args.url,
        price_selector=args.price_selector,
        target_price=args.target_price,
        webhook_url=args.webhook_url,
        stock_selector=args.stock_selector,
        interval=args.interval
    )

    try:
        asyncio.run(tracker.run())
    except KeyboardInterrupt:
        logger.info("Stopping tracker...")
        sys.exit(0)
