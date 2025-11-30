#aiwebarchitects
import asyncio
import argparse
import logging
import sys
from playwright.async_api import async_playwright
import requests

# Configure structured logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class SPAMonitor:
    def __init__(self, url, selector, webhook_url=None):
        """
        Initialize the monitor.
        :param url: The URL of the SPA to monitor.
        :param selector: The CSS selector to extract data from.
        :param webhook_url: Optional URL to POST alerts to.
        """
        self.url = url
        self.selector = selector
        self.webhook_url = webhook_url
        self.last_data = None
        self.browser = None
        self.context = None

    async def start_browser(self, p):
        """Launches the headless browser instance."""
        logger.info("Launching headless chromium browser...")
        # headless=True ensures it runs on servers without a GUI
        self.browser = await p.chromium.launch(headless=True)
        # Create a context with a real user agent to avoid basic bot detection
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

    async def check_page(self):
        """
        Navigates to the page, waits for the dynamic element, and extracts text.
        Returns the text content or None if an error occurs.
        """
        page = await self.context.new_page()
        try:
            logger.info(f"Navigating to {self.url}")
            # networkidle ensures most initial JS requests have finished
            await page.goto(self.url, wait_until="networkidle", timeout=60000)
            
            # Critical: Wait for the specific element to appear in the DOM
            # This handles the 'skeleton HTML' problem of SPAs
            logger.info(f"Waiting for selector: {self.selector}")
            await page.wait_for_selector(self.selector, state="visible", timeout=30000)
            
            # Extract text content from the first matching element
            element = page.locator(self.selector).first
            content = await element.inner_text()
            return content.strip()
            
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            return None
        finally:
            # Always close the page to free up memory
            await page.close()

    def trigger_alert(self, new_data):
        """Triggers an alert via Logger and optional Webhook."""
        msg = f"CHANGE DETECTED! New Data: '{new_data}'"
        logger.warning(msg)
        
        if self.webhook_url:
            try:
                # Standard JSON payload compatible with Slack/Discord/Teams incoming webhooks
                payload = {"text": msg, "content": msg}
                resp = requests.post(self.webhook_url, json=payload, timeout=10)
                if resp.status_code in [200, 201, 204]:
                    logger.info("Webhook alert sent successfully.")
                else:
                    logger.error(f"Failed to send webhook: Status {resp.status_code}")
            except Exception as e:
                logger.error(f"Error sending webhook: {e}")

    async def monitor_loop(self, interval):
        """Main execution loop."""
        async with async_playwright() as p:
            await self.start_browser(p)
            
            logger.info(f"Starting monitor loop every {interval} seconds.")
            logger.info("Press Ctrl+C to stop.")
            
            try:
                while True:
                    current_data = await self.check_page()
                    
                    if current_data:
                        logger.info(f"Scraped Value: '{current_data}'")
                        
                        # First run: establish baseline
                        if self.last_data is None:
                            self.last_data = current_data
                            logger.info("Initial data baseline set.")
                        
                        # Subsequent runs: compare for changes
                        elif current_data != self.last_data:
                            self.trigger_alert(current_data)
                            self.last_data = current_data
                        else:
                            logger.info("No change detected.")
                    else:
                        logger.warning("Failed to retrieve data this cycle.")
                    
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("Task cancelled.")
            finally:
                await self.browser.close()

if __name__ == "__main__":
    # CLI Argument Parsing
    parser = argparse.ArgumentParser(description="Headless SPA Monitor for Dynamic Content")
    parser.add_argument("--url", required=True, help="Target URL to monitor")
    parser.add_argument("--selector", required=True, help="CSS Selector of the element to watch (e.g., '.price', '#stock-count')")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (default: 60)")
    parser.add_argument("--webhook", help="Optional URL for webhook alerts (e.g., Slack/Discord)")

    args = parser.parse_args()

    monitor = SPAMonitor(args.url, args.selector, args.webhook)
    
    try:
        asyncio.run(monitor.monitor_loop(args.interval))
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
        sys.exit(0)