#aiwebarchitects
import asyncio
import random
import logging
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("monitor.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class StockMonitor:
    """
    A robust, production-ready class to monitor stock and price on dynamic SPAs.
    Utilizes Playwright to render JavaScript and mimics human behavior to avoid detection.
    """

    def __init__(self, config):
        self.url = config['url']
        self.selectors = config['selectors']
        self.check_interval_range = config.get('interval_range', (60, 180)) # Seconds
        self.user_agent = config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
        self.last_price = None
        self.last_stock_status = None

    async def send_alert(self, message):
        """
        Placeholder for alerting logic (Email, SMS, Slack, Discord).
        """
        # In a real deployment, integrate with smtplib for email or requests for Webhooks.
        logger.info(f"[ALERT TRIGGERED] >>> {message}")

    async def mimic_human_behavior(self, page):
        """
        Performs random mouse movements and scrolling to mimic a human user.
        This helps in bypassing heuristic-based bot detection.
        """
        try:
            # Random mouse movement
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            # Random scroll
            await page.evaluate(f"window.scrollBy(0, {random.randint(100, 300)})")
            await asyncio.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.debug(f"Human mimicry minor error: {e}")

    async def check_product(self):
        """
        Main logic to launch browser, navigate, and scrape data.
        """
        async with async_playwright() as p:
            # Launch browser. Headless=True for server, but args help mimic real head.
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled', # Hides navigator.webdriver flag
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            # Create a context with specific user agent and viewport to look like a desktop
            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York'
            )

            page = await context.new_page()

            try:
                logger.info(f"Checking URL: {self.url}")
                
                # Navigate with a generous timeout for heavy SPAs
                await page.goto(self.url, wait_until='networkidle', timeout=60000)
                
                # Mimic human behavior before extraction
                await self.mimic_human_behavior(page)

                # Wait for the price selector to be visible (handles dynamic loading)
                try:
                    await page.wait_for_selector(self.selectors['price'], timeout=15000)
                except PlaywrightTimeoutError:
                    logger.error("Timeout waiting for price selector. Page layout might have changed or bot detection triggered.")
                    return

                # Extract Data
                price_element = await page.query_selector(self.selectors['price'])
                stock_element = await page.query_selector(self.selectors['stock_status'])

                current_price = await price_element.inner_text() if price_element else "Unknown"
                current_stock = await stock_element.inner_text() if stock_element else "Unknown"

                # Clean data (basic whitespace removal)
                current_price = current_price.strip()
                current_stock = current_stock.strip()

                logger.info(f"Scraped Data - Price: {current_price}, Stock: {current_stock}")

                # Logic for Alerting
                alert_needed = False
                msg = ""

                # Check Price Change
                if self.last_price and self.last_price != current_price:
                    msg += f"Price changed from {self.last_price} to {current_price}. "
                    alert_needed = True
                
                # Check Stock Status Change
                if self.last_stock_status and self.last_stock_status != current_stock:
                    msg += f"Stock status changed from {self.last_stock_status} to {current_stock}. "
                    alert_needed = True

                if alert_needed:
                    await self.send_alert(msg)
                
                # Update state
                self.last_price = current_price
                self.last_stock_status = current_stock

            except Exception as e:
                logger.error(f"An error occurred during the check: {str(e)}")
                # Take screenshot on error for debugging
                await page.screenshot(path=f"error_{datetime.now().strftime('%H%M%S')}.png")
            
            finally:
                await context.close()
                await browser.close()

    async def start_monitoring(self):
        """
        Continuous loop to run the check indefinitely.
        """
        logger.info("Starting Stock Monitor...")
        while True:
            await self.check_product()
            
            # Sleep for a random interval to avoid pattern detection
            sleep_time = random.randint(*self.check_interval_range)
            logger.info(f"Sleeping for {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    # --- CONFIGURATION SECTION ---
    # Replace these selectors with the specific CSS selectors for your target SPA.
    # You can find these by right-clicking elements in Chrome -> Inspect.
    config = {
        'url': 'https://webscraper.io/test-sites/e-commerce/allinone/product/553', # Example Test Site
        'selectors': {
            'price': '.caption .pull-right.price',  # CSS Selector for Price
            'stock_status': '.caption h4:nth-child(2) a'   # CSS Selector for Title/Stock (using title as proxy for example)
        },
        'interval_range': (30, 60), # Random wait between 30 and 60 seconds
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    monitor = StockMonitor(config)
    
    try:
        asyncio.run(monitor.start_monitoring())
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user.")