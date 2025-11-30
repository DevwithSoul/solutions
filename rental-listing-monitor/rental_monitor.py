#aiwebarchitects
import requests
from bs4 import BeautifulSoup
import time
import json
import os
import argparse
import logging
import random
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rental_monitor.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

class RentalMonitor:
    def __init__(self, url, webhook_url, selectors, history_file='seen_listings.json', interval=300):
        self.url = url
        self.webhook_url = webhook_url
        self.selectors = selectors
        self.history_file = history_file
        self.interval = interval
        self.seen_listings = self.load_history()
        
        # List of User-Agents to rotate to avoid basic anti-bot blocking
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]

    def load_history(self):
        """Load previously seen listing IDs from a JSON file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return set(json.load(f))
            except json.JSONDecodeError:
                logging.warning("History file corrupted. Starting fresh.")
                return set()
        return set()

    def save_history(self):
        """Save seen listing IDs to a JSON file."""
        try:
            with open(self.history_file, 'w') as f:
                # Convert set to list for JSON serialization
                json.dump(list(self.seen_listings), f)
        except Exception as e:
            logging.error(f"Failed to save history: {e}")

    def get_headers(self):
        """Return headers with a random User-Agent."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

    def send_discord_notification(self, listing):
        """Send a formatted message to Discord via Webhook."""
        embed = {
            "title": f"🏠 New Rental Alert: {listing['title']}",
            "description": f"**Price:** {listing['price']}\n**Location:** {listing.get('location', 'N/A')}",
            "url": listing['link'],
            "color": 5620992,  # Greenish color
            "footer": {
                "text": f"Detected at {datetime.now().strftime('%H:%M:%S')}"
            }
        }
        
        payload = {
            "username": "Rental Bot",
            "embeds": [embed]
        }

        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 204:
                logging.info(f"Notification sent for: {listing['title']}")
            else:
                logging.error(f"Failed to send Discord notification: {response.status_code} - {response.text}")
        except Exception as e:
            logging.error(f"Error sending notification: {e}")

    def scrape(self):
        """Fetch and parse the rental website."""
        logging.info(f"Scraping {self.url}...")
        try:
            response = requests.get(self.url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Network error: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        new_listings = []

        # Find all listing containers based on the provided selector
        containers = soup.select(self.selectors['container'])
        logging.info(f"Found {len(containers)} potential listings.")

        for item in containers:
            try:
                # Extract Title
                title_elem = item.select_one(self.selectors['title'])
                title = title_elem.get_text(strip=True) if title_elem else "No Title"

                # Extract Price
                price_elem = item.select_one(self.selectors['price'])
                price = price_elem.get_text(strip=True) if price_elem else "N/A"

                # Extract Link
                link_elem = item.select_one(self.selectors['link'])
                if link_elem and link_elem.has_attr('href'):
                    link = link_elem['href']
                    # Handle relative URLs
                    if not link.startswith('http'):
                        from urllib.parse import urljoin
                        link = urljoin(self.url, link)
                else:
                    continue  # Skip if no link found

                # Generate a unique ID for the listing (URL is usually a good unique ID)
                listing_id = link

                if listing_id not in self.seen_listings:
                    listing_data = {
                        'id': listing_id,
                        'title': title,
                        'price': price,
                        'link': link,
                        'location': 'See Link' # Placeholder as location structure varies wildly
                    }
                    new_listings.append(listing_data)
                    self.seen_listings.add(listing_id)
            
            except Exception as e:
                logging.error(f"Error parsing an item: {e}")
                continue

        return new_listings

    def run(self):
        """Main loop."""
        logging.info("Starting Rental Monitor...")
        logging.info("Press Ctrl+C to stop.")
        
        try:
            while True:
                found_listings = self.scrape()
                
                if found_listings:
                    logging.info(f"Found {len(found_listings)} new listings!")
                    for listing in found_listings:
                        self.send_discord_notification(listing)
                        # Small delay between notifications to avoid rate limits
                        time.sleep(1)
                    self.save_history()
                else:
                    logging.info("No new listings found.")

                # Add a bit of jitter to the interval to behave less like a bot
                sleep_time = self.interval + random.uniform(0, 10)
                logging.info(f"Sleeping for {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            logging.info("Stopping monitor.")
            self.save_history()
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Rental Listing Monitor")
    
    parser.add_argument("--url", required=True, help="The URL of the rental search page to monitor")
    parser.add_argument("--webhook", required=True, help="Discord Webhook URL for notifications")
    
    # CSS Selectors arguments
    parser.add_argument("--container", required=True, help="CSS selector for the listing container (e.g. '.listing-card')")
    parser.add_argument("--title", required=True, help="CSS selector for the title inside the container (e.g. '.title')")
    parser.add_argument("--price", required=True, help="CSS selector for the price inside the container (e.g. '.price')")
    parser.add_argument("--link", required=True, help="CSS selector for the link inside the container (e.g. 'a.details')")
    
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300)")

    args = parser.parse_args()

    selectors = {
        'container': args.container,
        'title': args.title,
        'price': args.price,
        'link': args.link
    }

    monitor = RentalMonitor(
        url=args.url,
        webhook_url=args.webhook,
        selectors=selectors,
        interval=args.interval
    )

    monitor.run()