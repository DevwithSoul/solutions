#aiwebarchitects
import time
import random
import argparse
import sys
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Constants for anti-detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

class InventorySniper:
    def __init__(self, url, search_text, css_selector, webhook_url=None, headless=True, check_interval=30):
        """
        Initialize the sniper bot.
        :param url: Target URL to monitor.
        :param search_text: Text to look for to confirm stock (e.g., "Add to Cart").
        :param css_selector: CSS Selector of the element containing the text.
        :param webhook_url: Discord Webhook URL for notifications.
        :param headless: Run browser in background.
        :param check_interval: Base time in seconds between checks.
        """
        self.url = url
        self.search_text = search_text
        self.css_selector = css_selector
        self.webhook_url = webhook_url
        self.headless = headless
        self.check_interval = check_interval
        self.driver = None

    def setup_driver(self):
        """Configures and initializes the Chrome WebDriver with anti-bot options."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        
        # Basic Anti-Scraping bypass techniques
        options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            print("[+] WebDriver initialized successfully.")
        except Exception as e:
            print(f"[-] Error initializing WebDriver: {e}")
            sys.exit(1)

    def send_notification(self, message):
        """Sends a notification via Discord Webhook or prints to console."""
        print(f"[!] ALERT: {message}")
        if self.webhook_url:
            data = {"content": f"🚨 **INVENTORY SNIPER ALERT** 🚨\n{message}\nLink: {self.url}"}
            try:
                requests.post(self.webhook_url, json=data)
            except Exception as e:
                print(f"[-] Failed to send webhook: {e}")

    def check_stock(self):
        """Performs a single check for inventory."""
        try:
            self.driver.get(self.url)
            
            # Wait for the element to be present (max 10 seconds)
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.css_selector))
            )
            
            element_text = element.text.strip().lower()
            print(f"[*] Found text: '{element_text}' (looking for '{self.search_text.lower()}')")

            if self.search_text.lower() in element_text:
                return True
            
        except Exception as e:
            print(f"[-] Check failed or element not found: {e}")
        
        return False

    def run(self):
        """Main loop to monitor inventory."""
        self.setup_driver()
        print(f"[*] Starting monitoring for {self.url}...")
        
        try:
            while True:
                in_stock = self.check_stock()
                
                if in_stock:
                    self.send_notification(f"Item detected in stock! Text '{self.search_text}' found.")
                    # Optional: Break loop if you only want to buy once, or continue monitoring
                    # break 
                else:
                    print("[-] Item not yet available.")

                # Randomize wait time to act more human-like
                wait_time = self.check_interval + random.uniform(-5, 5)
                print(f"[*] Sleeping for {wait_time:.2f} seconds...\n")
                time.sleep(max(5, wait_time))

        except KeyboardInterrupt:
            print("\n[*] Stopping Sniper...")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Inventory Sniper")
    parser.add_argument("--url", required=True, help="Target URL to monitor")
    parser.add_argument("--selector", required=True, help="CSS Selector of the button/text (e.g., 'button.add-to-cart' or '#stock-status')")
    parser.add_argument("--text", required=True, help="Text to match inside the selector (e.g., 'Add to Cart' or 'In Stock')")
    parser.add_argument("--webhook", help="Discord Webhook URL for notifications")
    parser.add_argument("--interval", type=int, default=30, help="Interval between checks in seconds")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (not headless)")

    args = parser.parse_args()

    sniper = InventorySniper(
        url=args.url,
        search_text=args.text,
        css_selector=args.selector,
        webhook_url=args.webhook,
        headless=not args.visible,
        check_interval=args.interval
    )

    sniper.run()