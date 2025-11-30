#aiwebarchitects
import requests
import time
import argparse
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class WhaleWatcher:
    def __init__(self, address, api_key, webhook_url, threshold, interval):
        self.address = address
        self.api_key = api_key
        self.webhook_url = webhook_url
        self.threshold = float(threshold)
        self.interval = int(interval)
        self.last_seen_hash = None
        self.base_url = "https://api.etherscan.io/api"

    def wei_to_ether(self, wei_value):
        """Converts Wei (integer) to Ether (float). 1 Ether = 10^18 Wei."""
        try:
            return float(wei_value) / 10**18
        except (ValueError, TypeError):
            return 0.0

    def get_transactions(self):
        """
        Fetches the last 20 transactions for the address from Etherscan.
        Sorts by descending to get the newest first.
        """
        params = {
            "module": "account",
            "action": "txlist",
            "address": self.address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": 20,  # Only fetch last 20 to save bandwidth
            "sort": "desc",
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data["status"] == "1" and data["message"] == "OK":
                return data["result"]
            elif data["message"] == "No transactions found":
                return []
            else:
                logger.error(f"API Error: {data.get('message', 'Unknown error')}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network Error: {e}")
            return None

    def send_alert(self, tx):
        """Sends a formatted embed to Discord via Webhook."""
        ether_value = self.wei_to_ether(tx['value'])
        
        # Determine direction (Inbound or Outbound)
        if tx['to'].lower() == self.address.lower():
            direction = "🟢 INCOMING"
            color = 5763719  # Green
        else:
            direction = "🔴 OUTGOING"
            color = 15548997 # Red

        # Prepare Discord Embed
        payload = {
            "embeds": [{
                "title": f"{direction} WHALE ALERT",
                "description": f"High value transaction detected on monitored address.",
                "color": color,
                "fields": [
                    {"name": "Amount", "value": f"{ether_value:,.4f} ETH", "inline": True},
                    {"name": "Time", "value": datetime.fromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S'), "inline": True},
                    {"name": "From", "value": f"`{tx['from']}`", "inline": False},
                    {"name": "To", "value": f"`{tx['to']}`", "inline": False},
                    {"name": "Transaction Hash", "value": f"[{tx['hash']}](https://etherscan.io/tx/{tx['hash']})", "inline": False}
                ],
                "footer": {"text": "Real-Time Whale Watcher Bot"}
            }]
        }

        try:
            res = requests.post(self.webhook_url, json=payload)
            if res.status_code == 204:
                logger.info(f"Alert sent for TX: {tx['hash']}")
            else:
                logger.error(f"Failed to send Discord alert: {res.status_code} {res.text}")
        except Exception as e:
            logger.error(f"Webhook Error: {e}")

    def start_monitoring(self):
        logger.info(f"Starting monitor for address: {self.address}")
        logger.info(f"Threshold: {self.threshold} ETH | Interval: {self.interval}s")
        
        # Initial fetch to set the baseline (don't alert on old history)
        initial_txs = self.get_transactions()
        if initial_txs and len(initial_txs) > 0:
            self.last_seen_hash = initial_txs[0]['hash']
            logger.info(f"Baseline established. Last TX: {self.last_seen_hash}")
        else:
            logger.info("No history found or API error. Starting fresh.")

        while True:
            try:
                time.sleep(self.interval)
                transactions = self.get_transactions()

                if not transactions:
                    continue

                new_txs = []
                
                # Identify new transactions since last_seen_hash
                if self.last_seen_hash:
                    for tx in transactions:
                        if tx['hash'] == self.last_seen_hash:
                            break
                        new_txs.append(tx)
                else:
                    # If we didn't have a baseline, treat the most recent as the baseline for next time
                    # (To avoid spamming the first time script runs on an active address)
                    if transactions:
                        self.last_seen_hash = transactions[0]['hash']
                    continue

                # Process new transactions (Reverse to alert oldest-new first)
                if new_txs:
                    logger.info(f"Found {len(new_txs)} new transactions.")
                    for tx in reversed(new_txs):
                        ether_val = self.wei_to_ether(tx['value'])
                        
                        if ether_val >= self.threshold:
                            self.send_alert(tx)
                        else:
                            logger.info(f"Skipping TX {tx['hash']} (Value {ether_val:.4f} < {self.threshold})")
                    
                    # Update pointer to the absolute newest
                    self.last_seen_hash = transactions[0]['hash']
                
            except KeyboardInterrupt:
                logger.info("Stopping Whale Watcher...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in loop: {e}")
                time.sleep(5) # Prevent tight loop on crash

def main():
    parser = argparse.ArgumentParser(description="Real-Time Whale Watcher Bot")
    
    parser.add_argument("--address", required=True, help="Ethereum wallet address to monitor")
    parser.add_argument("--api-key", required=True, help="Etherscan API Key")
    parser.add_argument("--webhook", required=True, help="Discord Webhook URL")
    parser.add_argument("--threshold", default=0.1, type=float, help="Minimum ETH value to trigger alert (default: 0.1)")
    parser.add_argument("--interval", default=60, type=int, help="Polling interval in seconds (default: 60)")

    args = parser.parse_args()

    bot = WhaleWatcher(
        address=args.address,
        api_key=args.api_key,
        webhook_url=args.webhook,
        threshold=args.threshold,
        interval=args.interval
    )

    bot.start_monitoring()

if __name__ == "__main__":
    main()