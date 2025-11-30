#aiwebarchitects
import json
import time
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging to track the scraping process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class InfiniteScrollScraper:
    """
    A production-ready scraper designed to handle websites with infinite scrolling.
    It simulates user behavior to trigger JavaScript data loading and extracts content.
    """

    def __init__(self, headless=True, scroll_delay=2000):
        """
        Initialize the scraper settings.
        
        :param headless: Boolean to run browser in headless mode (no UI).
        :param scroll_delay: Time in milliseconds to wait after scrolling for content to load.
        """
        self.headless = headless
        self.scroll_delay = scroll_delay
        self.data = []

    def scrape(self, url, item_selector, data_extraction_fn, max_items=100):
        """
        Main scraping logic.

        :param url: The target URL to scrape.
        :param item_selector: CSS selector for individual data items (e.g., '.post', '.product-card').
        :param data_extraction_fn: A callback function to extract data from a single element handle.
        :param max_items: Safety limit to stop scraping after gathering N items.
        :return: List of extracted data dictionaries.
        """
        with sync_playwright() as p:
            # Launch the browser
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()

            logging.info(f"Navigating to {url}...")
            try:
                page.goto(url, timeout=60000) # 60s timeout for heavy pages
            except Exception as e:
                logging.error(f"Failed to load page: {e}")
                return []

            items_collected = 0
            last_height = page.evaluate("document.body.scrollHeight")
            
            while items_collected < max_items:
                # 1. Extract currently visible items
                # We re-query the DOM every iteration because new items are added and old refs might go stale
                elements = page.query_selector_all(item_selector)
                
                # Optimization: Only process new items if we were tracking IDs, 
                # but for simplicity, we extract all current DOM state and deduplicate later if needed.
                # Here, we just check the count to see if we are progressing.
                current_count = len(elements)
                logging.info(f"Items found in DOM: {current_count}")

                # 2. Scroll to the bottom to trigger new data load
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                # 3. Wait for the network to idle or specific time for JS to render
                # Using fixed sleep is safer for generic infinite scrolls than waiting for network idle
                # which might never happen on streaming sites.
                page.wait_for_timeout(self.scroll_delay)

                # 4. Check if we reached the bottom (no height change)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    logging.info("Reached end of page or content stopped loading.")
                    break
                last_height = new_height

                # Update loop condition based on DOM presence
                if current_count >= max_items:
                    logging.info(f"Reached max item limit of {max_items}.")
                    break
            
            # Final Extraction Pass
            logging.info("Starting data extraction...")
            final_elements = page.query_selector_all(item_selector)
            
            for i, element in enumerate(final_elements):
                if i >= max_items:
                    break
                try:
                    record = data_extraction_fn(element)
                    if record:
                        self.data.append(record)
                except Exception as e:
                    logging.warning(f"Error extracting item {i}: {e}")

            browser.close()
            logging.info(f"Scraping complete. Extracted {len(self.data)} records.")
            return self.data

    def save_to_json(self, filename='data.json'):
        """
        Exports collected data to a JSON file.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
            logging.info(f"Data saved to {filename}")
        except IOError as e:
            logging.error(f"Failed to save file: {e}")

# --- Usage Example ---

def extract_quote_data(element):
    """
    Custom extraction logic for 'quotes.toscrape.com/scroll'.
    Adjust this function based on the specific website structure.
    """
    try:
        text = element.query_selector('.text').inner_text()
        author = element.query_selector('.author').inner_text()
        tags = [tag.inner_text() for tag in element.query_selector_all('.tag')]
        return {
            "quote": text,
            "author": author,
            "tags": tags
        }
    except AttributeError:
        return None

if __name__ == "__main__":
    # Target: A famous sandbox for infinite scrolling
    TARGET_URL = "http://quotes.toscrape.com/scroll"
    TARGET_SELECTOR = ".quote"
    
    scraper = InfiniteScrollScraper(headless=False, scroll_delay=1000)
    
    # Run the scraper
    data = scraper.scrape(
        url=TARGET_URL,
        item_selector=TARGET_SELECTOR,
        data_extraction_fn=extract_quote_data,
        max_items=50  # Limiting to 50 for demonstration speed
    )
    
    # Save results
    scraper.save_to_json('scraped_quotes.json')
