#aiwebarchitects
import time
import argparse
import logging
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebMonitorBot:
    """
    A bot that monitors a specific URL for the presence (or absence) of text.
    When the condition is met, it sends a notification via Discord Webhook.
    """

    def __init__(self, url, search_text, webhook_url, interval=30, negative_search=False):
        """
        Initialize the monitor.
        :param url: The website URL to check.
        :param search_text: The text to look for (e.g., "Add to Cart").
        :param webhook_url: Discord Webhook URL for notifications.
        :param interval: Time in seconds between checks.
        :param negative_search: If True, alerts when text is GONE (e.g., "Out of Stock" disappears).
        """
        self.url = url
        self.search_text = search_text.lower()
        self.webhook_url = webhook_url
        self.interval = interval
        self.negative_search = negative_search
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.last_status = None  # To prevent spamming notifications if status hasn't changed

    def send_notification(self, message):
        """
        Sends a payload to the Discord Webhook.
        """
        if not self.webhook_url:
            logger.warning("No webhook URL provided. Notification skipped.")
            return

        data = {
            "content": f"🚨 **ALERT** 🚨\n{message}\n\n🔗 [Link to Product]({self.url})"
        }
        
        try:
            response = requests.post(self.webhook_url, json=data)
            if response.status_code == 204:
                logger.info("Notification sent successfully.")
            else:
                logger.error(f"Failed to send notification: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def check_site(self):
        """
        Fetches the site and checks for the keyword.
        """
        try:
            logger.info(f"Checking {self.url}...")
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text().lower()
            
            found = self.search_text in text_content
            
            # LOGIC: 
            # If negative_search is False (default): Alert when text IS found (e.g., "In Stock").
            # If negative_search is True: Alert when text is NOT found (e.g., "Out of Stock" is gone).
            
            alert_condition = found if not self.negative_search else not found
            
            status_msg = "MATCH FOUND" if alert_condition else "NO MATCH"
            logger.info(f"Result: {status_msg} | Searching for: '{self.search_text}'")

            if alert_condition:
                # Only notify if this is a new development to avoid spamming every 30s
                if self.last_status != 'triggered':
                    logger.info("Condition met! Sending notification...")
                    msg = f"Monitor successful! Logic: " + \
                          (f"'{self.search_text}' FOUND." if not self.negative_search else f"'{self.search_text}' DISAPPEARED.")
                    self.send_notification(msg)
                    self.last_status = 'triggered'
            else:
                # Reset status if condition is lost, so we can notify again if it comes back
                self.last_status = 'waiting'

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

    def start(self):
        """
        Main loop.
        """
        logger.info("Starting Web Monitor Bot...")
        logger.info(f"Target: {self.url}")
        logger.info(f"Keyword: '{self.search_text}'")
        logger.info(f"Mode: {'Negative Search (Alert when text gone)' if self.negative_search else 'Standard Search (Alert when text found)'}")
        
        try:
            while True:
                self.check_site()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("\nStopping bot. Goodbye!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="The Instant Web Monitor Bot")
    
    parser.add_argument("--url", required=True, help="The URL to monitor")
    parser.add_argument("--text", required=True, help="The text to search for (e.g., 'Add to Cart')")
    parser.add_argument("--webhook", required=False, help="Discord Webhook URL for notifications")
    parser.add_argument("--interval", type=int, default=30, help="Check interval in seconds (default: 30)")
    parser.add_argument("--missing", action="store_true", help="If set, alerts when text is MISSING (good for checking if 'Out of Stock' disappears)")

    args = parser.parse_args()

    bot = WebMonitorBot(
        url=args.url,
        search_text=args.text,
        webhook_url=args.webhook,
        interval=args.interval,
        negative_search=args.missing
    )

    bot.start()