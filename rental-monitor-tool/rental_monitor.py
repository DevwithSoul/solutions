#aiwebarchitects
import requests
import time
import random
import sqlite3
import logging
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# CONFIGURATION SECTION
# ==========================================

# The URL of the legacy rental website you want to monitor
TARGET_URL = "https://example-rental-site.com/listings"

# Discord Webhook URL (Get this from Server Settings -> Integrations -> Webhooks)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/your-webhook-id/your-webhook-token"

# CSS Selectors to extract data from the HTML.
# You must inspect the target website (Right click -> Inspect) to find these classes/ids.
SELECTORS = {
    "container": "div.listing-item",      # The HTML element wrapping a single ad
    "title": "h2.title",                  # The title of the listing
    "price": "span.price",                # The price element
    "link": "a.details-link",             # The link to the specific listing
    "id_attribute": "data-listing-id"     # Optional: specific attribute for ID, else uses link
}

# Bot Behavior Configuration
CHECK_INTERVAL_MIN = 60   # Minimum seconds between checks
CHECK_INTERVAL_MAX = 180  # Maximum seconds between checks (randomized to avoid detection)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
DB_FILE = "rental_history.db"

# CLI args to override config
import argparse
_parser = argparse.ArgumentParser(description="Rental Listing Monitor")
_parser.add_argument("--target-url", help="URL of the rental site to monitor")
_parser.add_argument("--webhook-url", help="Discord webhook URL for alerts")
_parser.add_argument("--min-interval", type=int, help="Min check interval in seconds")
_parser.add_argument("--max-interval", type=int, help="Max check interval in seconds")
_parser.add_argument("--db-file", help="SQLite database file path")
_args, _ = _parser.parse_known_args()
if _args.target_url:
    TARGET_URL = _args.target_url
if _args.webhook_url:
    DISCORD_WEBHOOK_URL = _args.webhook_url
if _args.min_interval:
    CHECK_INTERVAL_MIN = _args.min_interval
if _args.max_interval:
    CHECK_INTERVAL_MAX = _args.max_interval
if _args.db_file:
    DB_FILE = _args.db_file

# ==========================================
# SETUP & LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RentalMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        self.init_db()

    def init_db(self):
        """Initialize SQLite database to track seen listings."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS listings (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    price TEXT,
                    url TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            exit(1)

    def is_listing_seen(self, listing_id):
        """Check if a listing ID already exists in the database."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM listings WHERE id = ?", (listing_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def save_listing(self, listing_data):
        """Save a new listing to the database."""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO listings (id, title, price, url) VALUES (?, ?, ?, ?)",
                (listing_data['id'], listing_data['title'], listing_data['price'], listing_data['link'])
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Already exists, ignore
            pass
        finally:
            conn.close()

    def send_discord_alert(self, listing):
        """Send a rich embed notification to Discord."""
        if not DISCORD_WEBHOOK_URL or "your-webhook" in DISCORD_WEBHOOK_URL:
            logger.warning("Discord Webhook URL not configured. Skipping notification.")
            return

        embed = {
            "title": f"\ud83c\udfe0 New Rental Alert: {listing['title']}",
            "description": f"**Price:** {listing['price']}\n**Link:** [View Listing]({listing['link']})",
            "color": 5763719,  # Green color
            "footer": {
                "text": f"Detected at {datetime.now().strftime('%H:%M:%S')}"
            }
        }

        payload = {
            "username": "RentalScout",
            "embeds": [embed]
        }

        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if response.status_code == 204:
                logger.info(f"Notification sent for {listing['id']}")
            else:
                logger.error(f"Failed to send Discord alert: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")

    def fetch_listings(self):
        """Fetch and parse the target website."""
        try:
            logger.info(f"Fetching {TARGET_URL}...")
            response = self.session.get(TARGET_URL, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Server returned status code {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select(SELECTORS["container"])
            
            parsed_listings = []

            for item in items:
                try:
                    # Extract Title
                    title_elem = item.select_one(SELECTORS["title"])
                    title = title_elem.get_text(strip=True) if title_elem else "No Title"

                    # Extract Price
                    price_elem = item.select_one(SELECTORS["price"])
                    price = price_elem.get_text(strip=True) if price_elem else "N/A"

                    # Extract Link
                    link_elem = item.select_one(SELECTORS["link"])
                    link = link_elem['href'] if link_elem else ""
                    if link and not link.startswith("http"):
                        # Handle relative URLs
                        base_domain = "/".join(TARGET_URL.split("/")[:3])
                        link = base_domain + link

                    # Generate Unique ID
                    # Prefer a data-attribute, fallback to URL hash, fallback to title+price hash
                    listing_id = None
                    if SELECTORS.get("id_attribute") and item.has_attr(SELECTORS["id_attribute"]):
                        listing_id = item[SELECTORS["id_attribute"]]
                    elif link:
                        listing_id = link
                    else:
                        listing_id = str(hash(title + price))

                    parsed_listings.append({
                        "id": listing_id,
                        "title": title,
                        "price": price,
                        "link": link
                    })
                except Exception as parse_err:
                    logger.error(f"Error parsing an item: {parse_err}")
                    continue
            
            return parsed_listings

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return []

    def start(self):
        """Main execution loop."""
        logger.info("Starting Rental Monitor...")
        
        # Initial run flag to prevent spamming on startup
        first_run = True
        
        while True:
            listings = self.fetch_listings()
            
            if listings:
                new_count = 0
                for listing in listings:
                    if not self.is_listing_seen(listing['id']):
                        self.save_listing(listing)
                        
                        # Don't alert on the very first run, just populate DB
                        if not first_run:
                            self.send_discord_alert(listing)
                            new_count += 1
                        else:
                            logger.info(f"Initial indexing: {listing['title']} added to DB.")
                
                if first_run:
                    logger.info(f"Initial scan complete. {len(listings)} listings indexed. Monitoring for new items...")
                    first_run = False
                elif new_count > 0:
                    logger.info(f"Found {new_count} new listings!")
                else:
                    logger.info("No new listings found.")
            else:
                logger.info("No listings found on page or parse failed.")

            # Random sleep to avoid bot detection (Humanizing the behavior)
            sleep_time = random.randint(CHECK_INTERVAL_MIN, CHECK_INTERVAL_MAX)
            logger.info(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)

if __name__ == "__main__":
    monitor = RentalMonitor()
    try:
        monitor.start()
    except KeyboardInterrupt:
        logger.info("Stopping Scraper...")
