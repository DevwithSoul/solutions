#aiwebarchitects
import time
import argparse
import logging
import sys
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
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class InventoryMonitor:
    def __init__(self, url, selector, selector_type, check_interval, headless):
        """
        Initialize the monitor with target details.
        
        :param url: The URL to monitor.
        :param selector: The DOM selector (ID, Class, XPath) to identify the stock element.
        :param selector_type: The type of selector ('id', 'css', 'xpath').
        :param check_interval: Time in seconds between checks.
        :param headless: Boolean to run browser in headless mode.
        """
        self.url = url
        self.selector = selector
        self.selector_type = selector_type.lower()
        self.check_interval = check_interval
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        """Sets up the Chrome WebDriver with options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # Basic options for stability in container/server environments
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Initialize the driver using WebDriver Manager for automatic binary management
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_by_strategy(self):
        """Maps the string selector type to Selenium By strategy."""
        if self.selector_type == 'id':
            return By.ID
        elif self.selector_type == 'xpath':
            return By.XPATH
        elif self.selector_type == 'css':
            return By.CSS_SELECTOR
        else:
            raise ValueError(f"Unsupported selector type: {self.selector_type}")

    def check_stock(self):
        """Performs a single check of the inventory status."""
        try:
            logger.info(f"Checking URL: {self.url}")
            self.driver.get(self.url)
            
            # Wait for the element to be present (handles dynamic loading)
            wait = WebDriverWait(self.driver, 10)
            by_strategy = self.get_by_strategy()
            
            element = wait.until(EC.presence_of_element_located((by_strategy, self.selector)))
            
            # Extract text to determine status
            text = element.text.strip()
            logger.info(f"Found element text: '{text}'")
            
            # Logic to determine if 'In Stock' (Customize based on target site)
            # This is a generic check; in production, you might check for 'Add to Cart' button existence
            if "out of stock" not in text.lower() and "sold out" not in text.lower():
                logger.info(">>> POTENTIAL STOCK DETECTED! <<<")
                # Here you would trigger an alert (Email, SMS, Webhook)
                return True
            else:
                logger.info("Item appears to be out of stock.")
                return False
                
        except Exception as e:
            logger.error(f"Error during check: {e}")
            return False

    def start(self):
        """Starts the monitoring loop."""
        logger.info("Starting Inventory Monitor...")
        self.setup_driver()
        try:
            while True:
                found = self.check_stock()
                if found:
                    logger.info("Stock found! Stopping monitor (or continue based on preference).")
                    # Uncomment break to stop on first find
                    # break 
                
                logger.info(f"Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Stopping monitor...")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Dynamic Inventory Monitor")
    
    parser.add_argument('--url', required=True, help='Target URL to monitor')
    parser.add_argument('--selector', required=True, help='Selector for the stock status element')
    parser.add_argument('--type', default='css', choices=['css', 'xpath', 'id'], help='Type of selector')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    monitor = InventoryMonitor(
        url=args.url,
        selector=args.selector,
        selector_type=args.type,
        check_interval=args.interval,
        headless=args.headless
    )
    
    monitor.start()