#aiwebarchitects
import argparse
import time
import sys
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

"""
Inventory Sniper - Real-Time Stock Monitor

This script monitors a specific URL for changes in HTML content (specifically looking for 'Add to Cart' buttons
or the absence of 'Out of Stock' labels). It uses Playwright to render the page, ensuring that
dynamic JavaScript content (React/Vue/Angular) is loaded before checking.

Dependencies:
    pip install playwright requests
    playwright install chromium

Usage Example:
    python inventory_sniper.py \
        --url "https://example.com/product/ps5" \
        --selector "button.add-to-cart" \
        --webhook "https://discord.com/api/webhooks/..." \
        --interval 30
"""

def send_discord_notification(webhook_url, product_url, screenshot_path=None):
    """
    Sends a push notification to a Discord channel via Webhook.
    """
    data = {
        "content": f"@everyone \ud83d\udea8 **STOCK DETECTED!** \ud83d\udea8\n\nTarget: {product_url}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "username": "Inventory Sniper Bot"
    }
    
    # If we have a screenshot, we need to send multipart/form-data
    if screenshot_path:
        try:
            with open(screenshot_path, 'rb') as f:
                files = {
                    'file': (screenshot_path, f, 'image/png')
                }
                # Payload_json is required when sending files with JSON data
                response = requests.post(webhook_url, data={'payload_json': str(data).replace("'", '"')}, files=files)
        except Exception as e:
            print(f"[!] Failed to upload screenshot: {e}")
            # Fallback to text only
            requests.post(webhook_url, json=data)
    else:
        try:
            response = requests.post(webhook_url, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[!] Error sending Discord notification: {e}")

def check_stock(url, selector, text_match, headless):
    """
    Uses Playwright to load the page and check for the element.
    Returns: (bool: is_in_stock, str: screenshot_path or None)
    """
    with sync_playwright() as p:
        # Launch browser (Chromium is standard)
        browser = p.chromium.launch(headless=headless)
        
        # Create a new context with a user agent to avoid basic bot detection
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()

        try:
            print(f"[*] Checking: {url}")
            # Wait for network idle to ensure JS finished loading
            page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Check if the selector exists
            # If text_match is provided, we filter by that text
            is_available = False
            
            if text_match:
                # Look for selector strictly containing the text (case-insensitive usually requires regex, keeping simple here)
                # We use :has-text pseudo-class from Playwright
                locator = page.locator(f"{selector}:has-text('{text_match}')")
            else:
                locator = page.locator(selector)

            # Check if at least one matching element is visible
            if locator.count() > 0 and locator.first.is_visible():
                is_available = True
            
            screenshot_path = None
            if is_available:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                screenshot_path = f"success_{timestamp}.png"
                page.screenshot(path=screenshot_path)
                print(f"[+] Target FOUND! Screenshot saved to {screenshot_path}")
            else:
                print("[-] Target not found or element not visible.")

            return is_available, screenshot_path

        except PlaywrightTimeoutError:
            print("[!] Timeout waiting for page to load. Retrying next cycle.")
            return False, None
        except Exception as e:
            print(f"[!] Unexpected error: {e}")
            return False, None
        finally:
            browser.close()

def main():
    parser = argparse.ArgumentParser(description="Real-Time Inventory Sniper")
    
    parser.add_argument("--url", required=True, help="The URL to monitor")
    parser.add_argument("--selector", required=True, help="CSS Selector for the 'Add to Cart' button or stock text")
    parser.add_argument("--text", help="Optional: Specific text the selector must contain (e.g., 'Add to Cart')", default=None)
    parser.add_argument("--webhook", required=True, help="Discord Webhook URL")
    parser.add_argument("--interval", type=int, default=60, help="Seconds to wait between checks")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode (no UI)")
    parser.add_argument("--no-headless", dest="headless", action="store_false")
    parser.set_defaults(headless=True)

    args = parser.parse_args()

    print("--- Inventory Sniper Started ---")
    print(f"Target: {args.url}")
    print(f"Looking for: {args.selector} " + (f"containing '{args.text}'" if args.text else ""))
    print(f"Interval: {args.interval} seconds")
    print("--------------------------------")

    try:
        while True:
            in_stock, screenshot = check_stock(args.url, args.selector, args.text, args.headless)
            
            if in_stock:
                print(">>> TRIGGERING ALERT <<<")
                send_discord_notification(args.webhook, args.url, screenshot)
                # Optional: Exit after success to avoid spamming, or sleep longer
                print("Alert sent. Pausing for 5 minutes to avoid webhook spam.")
                time.sleep(300)
            
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[!] Sniper stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()