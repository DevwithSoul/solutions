#aiwebarchitects
import asyncio
import argparse
import sys
import time
import json
from datetime import datetime
from playwright.async_api import async_playwright

class SPAWatcher:
    """
    A class to monitor Single Page Applications (SPAs) for changes in specific DOM elements.
    Uses Playwright to render JavaScript and handle dynamic content loading.
    """

    def __init__(self, url, selector, interval, webhook_url=None, headless=True):
        self.url = url
        self.selector = selector
        self.interval = interval
        self.webhook_url = webhook_url
        self.headless = headless
        self.last_content = None
        self.browser = None
        self.context = None

    def log(self, message, level="INFO"):
        """Helper to print timestamped logs."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    async def send_alert(self, new_content):
        """Sends a webhook alert if configured, otherwise just logs to console."""
        alert_msg = f"Change detected! New Content: '{new_content.strip()}'"
        self.log(alert_msg, "ALERT")

        if self.webhook_url:
            try:
                # Using the browser context to send a request to avoid external dependencies like 'requests'
                api_request_context = self.context.request
                payload = {
                    "text": alert_msg,
                    "source": self.url,
                    "timestamp": datetime.now().isoformat()
                }
                await api_request_context.post(self.webhook_url, json=payload)
                self.log(f"Webhook sent to {self.webhook_url}")
            except Exception as e:
                self.log(f"Failed to send webhook: {e}", "ERROR")

    async def check_page(self, page):
        """
        Navigates to the page, waits for the selector, and extracts content.
        """
        try:
            self.log(f"Checking {self.url}...")
            
            # Go to the URL
            # waitUntil='networkidle' is useful for SPAs to ensure initial requests finish
            await page.goto(self.url, wait_until='domcontentloaded')
            
            # Wait for the specific element to appear in the DOM (handles async rendering)
            try:
                await page.wait_for_selector(self.selector, timeout=10000)
            except Exception:
                self.log(f"Timeout waiting for selector '{self.selector}'", "WARNING")
                return

            # Extract text content
            content = await page.text_content(self.selector)
            
            if content is None:
                self.log("Selector found but content is empty.", "WARNING")
                return

            # Compare with previous state
            if self.last_content is not None and content != self.last_content:
                await self.send_alert(content)
            elif self.last_content is None:
                self.log(f"Initial content captured: '{content.strip()}'")
            else:
                self.log("No change detected.")

            self.last_content = content

        except Exception as e:
            self.log(f"Error during check: {e}", "ERROR")

    async def run(self):
        """Main execution loop."""
        async with async_playwright() as p:
            self.log("Launching headless browser...")
            self.browser = await p.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            page = await self.context.new_page()

            self.log(f"Starting monitoring loop for selector: '{self.selector}'")
            self.log(f"Check interval: {self.interval} seconds")
            self.log("Press Ctrl+C to stop.")

            try:
                while True:
                    await self.check_page(page)
                    await asyncio.sleep(self.interval)
            except KeyboardInterrupt:
                self.log("Stopping watcher...", "INFO")
            finally:
                await self.browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dynamic SPA Watcher: Monitor async web elements.")
    
    parser.add_argument("--url", required=True, help="The URL of the Single Page Application to monitor.")
    parser.add_argument("--selector", required=True, help="The CSS selector of the element to watch (e.g., '.price', '#stock-status').")
    parser.add_argument("--interval", type=int, default=60, help="Time in seconds between checks (default: 60).")
    parser.add_argument("--webhook", help="Optional URL to POST JSON data when a change is detected.")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (not headless) for debugging.")

    args = parser.parse_args()

    watcher = SPAWatcher(
        url=args.url,
        selector=args.selector,
        interval=args.interval,
        webhook_url=args.webhook,
        headless=not args.visible
    )

    try:
        asyncio.run(watcher.run())
    except KeyboardInterrupt:
        pass  # Handled inside run