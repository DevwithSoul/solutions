#aiwebarchitects
import os
import json
import time
import logging
import argparse
import re
import schedule
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rental_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RentalAlertBot:
    def __init__(self, config):
        """
        Initialize the bot with configuration settings.
        """
        self.url = config['url']
        self.max_price = config['max_price']
        self.webhook_url = config['webhook_url']
        self.interval = config['interval']
        self.history_file = 'seen_listings.json'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # CSS Selectors - THESE MUST BE UPDATED BASED ON THE TARGET WEBSITE
        # Defaulting to generic class names often found in templates
        self.selectors = {
            'listing_container': config.get('container_sel', 'article'), # The card wrapping the listing
            'title': config.get('title_sel', 'h2'), # The title element
            'price': config.get('price_sel', '.price'), # The price element
            'link': config.get('link_sel', 'a') # The link to the detail page
        }

        self.seen_listings = self.load_seen_listings()

    def load_seen_listings(self):
        """Load previously seen listing IDs to avoid duplicate alerts."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                return set()
        return set()

    def save_seen_listings(self):
        """Save seen listing IDs to disk."""
        try:
            with open(self.history_file, 'w') as f:
                # Convert set to list for JSON serialization
                json.dump(list(self.seen_listings), f)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def parse_price(self, price_str):
        """Clean price string and convert to float."""
        try:
            # Remove currency symbols, commas, and whitespace
            clean_str = re.sub(r'[^0-9.]', '', price_str)
            return float(clean_str) if clean_str else 0.0
        except ValueError:
            return 0.0

    def send_discord_alert(self, listing):
        """Send a rich embed notification to Discord via Webhook."""
        if not self.webhook_url:
            logger.info(f"[Alert Skipped - No Webhook] Found: {listing['title']} - ${listing['price']}")
            return

        payload = {
            "username": "Rental Hunter Bot",
            "embeds": [{
                "title": "🏠 New Affordable Rental Found!",
                "description": listing['title'],
                "url": listing['link'],
                "color": 5763719,  # Green color
                "fields": [
                    {
                        "name": "Price",
                        "value": f"${listing['price']}",
                        "inline": True
                    },
                    {
                        "name": "Found At",
                        "value": datetime.now().strftime("%H:%M:%S"),
                        "inline": True
                    }
                ],
                "footer": {
                    "text": "Rental Alert System"
                }
            }]
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 204:
                logger.info(f"Alert sent for: {listing['title']}")
            else:
                logger.error(f"Failed to send webhook: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")

    def scrape(self):
        """Main scraping logic."""
        logger.info(f"Checking {self.url} for rentals under ${self.max_price}...")
        
        try:
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            listings_found = soup.select(self.selectors['listing_container'])
            new_count = 0

            for item in listings_found:
                try:
                    # Extract Title
                    title_el = item.select_one(self.selectors['title'])
                    title = title_el.get_text(strip=True) if title_el else "Unknown Title"

                    # Extract Link
                    link_el = item.select_one(self.selectors['link'])
                    if link_el and link_el.has_attr('href'):
                        link = link_el['href']
                        # Handle relative URLs
                        if not link.startswith('http'):
                            from urllib.parse import urljoin
                            link = urljoin(self.url, link)
                    else:
                        continue # Skip if no link found (unique identifier)

                    # Check duplicates
                    if link in self.seen_listings:
                        continue

                    # Extract Price
                    price_el = item.select_one(self.selectors['price'])
                    price_str = price_el.get_text(strip=True) if price_el else "0"
                    price = self.parse_price(price_str)

                    # Filter logic
                    if 0 < price <= self.max_price:
                        listing_obj = {
                            'title': title,
                            'price': price,
                            'link': link
                        }
                        
                        self.send_discord_alert(listing_obj)
                        self.seen_listings.add(link)
                        new_count += 1

                except Exception as inner_e:
                    logger.warning(f"Error parsing individual listing: {inner_e}")
                    continue
            
            if new_count > 0:
                self.save_seen_listings()
                logger.info(f"Found and alerted {new_count} new listings.")
            else:
                logger.info("No new listings found meeting criteria.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error scraping {self.url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def start(self):
        """Start the scheduler."""
        logger.info("Rental Alert System Started. Press Ctrl+C to stop.")
        
        # Run once immediately
        self.scrape()
        
        # Schedule future runs
        schedule.every(self.interval).minutes.do(self.scrape)
        
        while True:
            schedule.run_pending()
            time.sleep(1)

# --- Simulation Mode for Demonstration ---
def run_simulation(webhook_url, max_price):
    """Generates fake data to prove the alert system works without a real website."""
    logger.info("--- STARTING SIMULATION MODE ---")
    bot = RentalAlertBot({
        'url': 'http://mock-rental-site.local',
        'max_price': max_price,
        'webhook_url': webhook_url,
        'interval': 1
    })
    
    # Simulate finding a listing
    fake_listing = {
        'title': 'Sunny Downtown Apartment (SIMULATION)',
        'price': max_price - 50,
        'link': f'http://mock-rental-site.local/view/{int(time.time())}'
    }
    
    logger.info(f"Simulating found listing: {fake_listing['title']} at ${fake_listing['price']}")
    bot.send_discord_alert(fake_listing)
    logger.info("Simulation alert sent. Check your Discord!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Rental Alert Bot")
    
    parser.add_argument('--url', type=str, help='Target URL to scrape')
    parser.add_argument('--max-price', type=float, default=2000.0, help='Maximum affordable price')
    parser.add_argument('--webhook', type=str, default='', help='Discord Webhook URL for notifications')
    parser.add_argument('--interval', type=int, default=10, help='Check interval in minutes')
    parser.add_argument('--test', action='store_true', help='Run a test simulation to verify Discord alerts')
    
    # CSS Selector Overrides (Optional)
    parser.add_argument('--sel-container', type=str, default='article', help='CSS selector for listing container')
    parser.add_argument('--sel-title', type=str, default='h2', help='CSS selector for title')
    parser.add_argument('--sel-price', type=str, default='.price', help='CSS selector for price')

    args = parser.parse_args()

    if args.test:
        run_simulation(args.webhook, args.max_price)
    elif not args.url:
        print("Error: --url is required unless using --test")
        parser.print_help()
    else:
        config = {
            'url': args.url,
            'max_price': args.max_price,
            'webhook_url': args.webhook,
            'interval': args.interval,
            'container_sel': args.sel_container,
            'title_sel': args.sel_title,
            'price_sel': args.sel_price
        }
        
        bot = RentalAlertBot(config)
        try:
            bot.start()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")