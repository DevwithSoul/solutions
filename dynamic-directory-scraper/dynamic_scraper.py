#aiwebarchitects
import asyncio
import argparse
import json
import csv
import time
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, BrowserContext

class DynamicScraper:
    """
    A production-ready scraper designed to handle dynamic content loading
    via infinite scroll or 'Load More' buttons.
    """

    def __init__(self, url: str, item_selector: str, output_file: str, 
                 limit: int = 100, headless: bool = True, 
                 strategy: str = 'scroll', button_selector: Optional[str] = None):
        self.url = url
        self.item_selector = item_selector
        self.output_file = output_file
        self.limit = limit
        self.headless = headless
        self.strategy = strategy  # 'scroll' or 'click'
        self.button_selector = button_selector
        self.data: List[Dict] = []

    async def scroll_to_bottom(self, page: Page):
        """Scrolls to the bottom of the page to trigger content loading."""
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        # Wait for network idle or a generic timeout to allow DOM updates
        try:
            await page.wait_for_load_state('networkidle', timeout=2000)
        except:
            await page.wait_for_timeout(2000)

    async def click_load_more(self, page: Page) -> bool:
        """
        Attempts to find and click the 'Load More' button.
        Returns True if clicked, False if not found or hidden.
        """
        if not self.button_selector:
            return False
        
        try:
            button = page.locator(self.button_selector)
            if await button.is_visible():
                await button.click()
                await page.wait_for_timeout(2000)  # Wait for content to load
                return True
        except Exception as e:
            print(f"[INFO] Could not click button: {e}")
        return False

    async def extract_current_items(self, page: Page) -> int:
        """Extracts text content from the current DOM state based on selector."""
        elements = await page.locator(self.item_selector).all()
        
        current_data = []
        for el in elements:
            text = await el.inner_text()
            # basic cleaning
            clean_text = " ".join(text.split())
            if clean_text:
                current_data.append({"content": clean_text})
        
        # Update master list, avoiding duplicates if possible (naive check here)
        # In a real DB scenario, we'd use IDs. Here we just replace the list 
        # or append. For dynamic feeds, it's safer to re-scrape everything 
        # visible if the DOM keeps existing nodes.
        self.data = current_data
        return len(self.data)

    async def run(self):
        print(f"[START] Initializing Playwright... Target: {self.url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()

            try:
                await page.goto(self.url, timeout=60000)
                print("[INFO] Page loaded. Starting extraction loop...")

                prev_count = 0
                no_change_counter = 0
                max_no_change = 3  # Stop if content doesn't grow after 3 attempts

                while len(self.data) < self.limit:
                    # 1. Extract Data
                    count = await self.extract_current_items(page)
                    print(f"[STATUS] Extracted {count} items so far...")

                    if count >= self.limit:
                        break

                    # 2. Load More Content
                    content_loaded = False
                    if self.strategy == 'scroll':
                        prev_height = await page.evaluate("document.body.scrollHeight")
                        await self.scroll_to_bottom(page)
                        new_height = await page.evaluate("document.body.scrollHeight")
                        content_loaded = new_height > prev_height
                    
                    elif self.strategy == 'click':
                        content_loaded = await self.click_load_more(page)

                    # 3. Check for termination conditions
                    if count == prev_count and not content_loaded:
                        no_change_counter += 1
                        print(f"[INFO] No new items found ({no_change_counter}/{max_no_change}).")
                    else:
                        no_change_counter = 0

                    if no_change_counter >= max_no_change:
                        print("[INFO] Reached end of content or pagination limit.")
                        break

                    prev_count = count
                    # Brief pause to be polite
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"[ERROR] An error occurred: {e}")
            finally:
                # Save Data
                self.save_data()
                await browser.close()
                print("[END] Browser closed.")

    def save_data(self):
        """Saves extracted data to JSON or CSV."""
        if not self.data:
            print("[WARN] No data to save.")
            return

        # Slice to limit
        final_data = self.data[:self.limit]

        if self.output_file.endswith('.json'):
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
        elif self.output_file.endswith('.csv'):
            keys = final_data[0].keys()
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(final_data)
        
        print(f"[SUCCESS] Saved {len(final_data)} items to {self.output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dynamic Directory Scraper using Playwright")
    
    # Default defaults setup for a known infinite scroll sandbox
    parser.add_argument("--url", type=str, default="http://quotes.toscrape.com/scroll", help="Target URL")
    parser.add_argument("--selector", type=str, default=".quote", help="CSS selector for the item container")
    parser.add_argument("--output", type=str, default="results.json", help="Output file (.json or .csv)")
    parser.add_argument("--limit", type=int, default=50, help="Max number of items to extract")
    parser.add_argument("--headless", action='store_true', help="Run in headless mode (default: False for debug)")
    parser.add_argument("--strategy", type=str, choices=['scroll', 'click'], default='scroll', help="Pagination strategy")
    parser.add_argument("--button", type=str, default=None, help="CSS selector for 'Load More' button (if strategy is click)")

    args = parser.parse_args()
    
    # Invert headless default for CLI logic (argparse store_true means default is False)
    # We want default to be Headless=False for visibility unless specified, 
    # or commonly Headless=True for servers. Let's stick to explicit flag.
    # To make it run headless by default: use store_false or handle logic manually.
    # Here: If user runs script without args, it runs visible (easier to debug). 
    # Use --headless to hide it.
    
    scraper = DynamicScraper(
        url=args.url,
        item_selector=args.selector,
        output_file=args.output,
        limit=args.limit,
        headless=args.headless,
        strategy=args.strategy,
        button_selector=args.button
    )

    asyncio.run(scraper.run())