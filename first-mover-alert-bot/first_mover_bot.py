#aiwebarchitects
import time
import json
import os
import argparse
import requests
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class FirstMoverBot:
    def __init__(self, url, item_selector, id_selector, webhook_url, state_file, check_interval, headless):
        self.url = url
        self.item_selector = item_selector
        self.id_selector = id_selector
        self.webhook_url = webhook_url
        self.state_file = state_file
        self.check_interval = check_interval
        self.seen_items = self.load_state()
        
        # Setup Selenium WebDriver
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # Fake user agent to avoid basic bot detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("WebDriver initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def load_state(self):
        """Loads the list of previously seen IDs from a JSON file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading state file: {e}")
                return set()
        return set()

    def save_state(self):
        """Saves the current list of seen IDs to a JSON file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(list(self.seen_items), f)
        except Exception as e:
            logger.error(f"Error saving state file: {e}")

    def send_alert(self, item_text, item_link):
        """Sends a notification to the Discord Webhook."""
        if not self.webhook_url:
            logger.info(f"[ALERT - No Webhook Configured] New Item: {item_text} ({item_link})")
            return

        payload = {
            "content": f"🚨 **FIRST MOVER ALERT** 🚨\n**Found:** {item_text}\n**Link:** {item_link}"
        }
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 204:
                logger.info(f"Alert sent for: {item_text}")
            else:
                logger.warning(f"Failed to send alert. Status: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")

    def check_for_updates(self):
        """Main logic to fetch page, parse items, and alert on new ones."""
        logger.info(f"Checking {self.url}...")
        try:
            self.driver.get(self.url)
            
            # Wait for the items to be present (handles dynamic loading)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, self.item_selector))
                )
            except Exception:
                logger.warning("Timeout waiting for items to load. Page might be empty or selector is wrong.")
                return

            # Find all item containers
            elements = self.driver.find_elements(By.CSS_SELECTOR, self.item_selector)
            
            new_items_found = 0
            
            for element in elements:
                try:
                    # Extract Unique ID (Link or Text)
                    # If id_selector is provided, search inside the element. Otherwise use the element text/href.
                    if self.id_selector:
                        target_el = element.find_element(By.CSS_SELECTOR, self.id_selector)
                    else:
                        target_el = element

                    # Prefer href as ID, fallback to text
                    item_link = target_el.get_attribute('href') or self.url
                    item_text = target_el.text.strip()
                    
                    # Use the link as the unique identifier
                    unique_id = item_link

                    if unique_id not in self.seen_items:
                        self.send_alert(item_text, item_link)
                        self.seen_items.add(unique_id)
                        new_items_found += 1
                except Exception as e:
                    # Skip individual malformed items
                    continue

            if new_items_found > 0:
                logger.info(f"Found {new_items_found} new items.")
                self.save_state()
            else:
                logger.info("No new items found.")

        except Exception as e:
            logger.error(f"Error during check: {e}")

    def run(self):
        """Starts the monitoring loop."""
        logger.info("Starting First Mover Bot...")
        try:
            while True:
                self.check_for_updates()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Stopping bot (User Interrupt)...")
        finally:
            self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="First Mover Alert Bot - Monitor websites for new items.")
    
    # Required Arguments
    parser.add_argument('--url', required=True, help='The URL to monitor.')
    parser.add_argument('--selector', required=True, help='CSS Selector for the item container (e.g., "div.listing").')
    
    # Optional Arguments
    parser.add_argument('--id-selector', help='CSS Selector for the specific link/ID inside the container (e.g., "a.title").')
    parser.add_argument('--webhook', help='Discord Webhook URL for alerts.')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60).')
    parser.add_argument('--state-file', default='seen_items.json', help='JSON file to store state (default: seen_items.json).')
    parser.add_argument('--no-headless', action='store_true', help='Run Chrome in visible mode (useful for debugging).')

    args = parser.parse_args()

    # Example Usage Hint if run without args (though argparse handles required check)
    # python first_mover_bot.py --url "https://news.ycombinator.com/newest" --selector "tr.athing" --id-selector "a.titlelink"

    bot = FirstMoverBot(
        url=args.url,
        item_selector=args.selector,
        id_selector=args.id_selector,
        webhook_url=args.webhook,
        state_file=args.state_file,
        check_interval=args.interval,
        headless=not args.no_headless
    )

    bot.run()