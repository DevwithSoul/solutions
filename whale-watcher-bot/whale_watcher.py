#aiwebarchitects
import time
import requests
import argparse
import logging
import sys
from datetime import datetime

# Configure logging to standard output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class WhaleWatcher:
    """
    A bot to monitor an Ethereum wallet address for new transactions.
    Uses Etherscan API for data and Discord Webhooks for alerts.
    """
    
    def __init__(self, address, api_key, webhook_url, threshold_eth=0.0, poll_interval=60):
        self.address = address.lower()
        self.api_key = api_key
        self.webhook_url = webhook_url
        self.threshold_eth = threshold_eth
        self.poll_interval = poll_interval
        self.last_tx_hash = None
        self.base_url = "https://api.etherscan.io/api"

    def get_latest_transactions(self):
        """
        Fetches the list of transactions for the wallet from Etherscan.
        Returns the list of transactions or None if request fails.
        """
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': self.address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': 5,  # Only get last 5 to save bandwidth
            'sort': 'desc',
            'apikey': self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['status'] == '1' and data['result']:
                return data['result']
            elif data['message'] == 'No transactions found':
                return []
            else:
                logger.warning(f"API Error: {data.get('message', 'Unknown error')}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching transactions: {e}")
            return None

    def wei_to_eth(self, wei_value):
        """Converts Wei (integer string) to Ether (float)."""
        try:
            return float(wei_value) / 10**18
        except (ValueError, TypeError):
            return 0.0

    def send_discord_alert(self, tx):
        """
        Formats transaction data and sends a rich embed to Discord.
        """
        eth_value = self.wei_to_eth(tx['value'])
        
        # Determine direction
        if tx['to'].lower() == self.address:
            direction = "🟢 INCOMING"
            color = 5763719 # Green
        else:
            direction = "🔴 OUTGOING"
            color = 15548997 # Red

        # Skip if below threshold
        if eth_value < self.threshold_eth:
            return

        embed = {
            "title": "🐋 Whale Activity Detected!",
            "url": f"https://etherscan.io/tx/{tx['hash']}",
            "color": color,
            "fields": [
                {"name": "Type", "value": direction, "inline": True},
                {"name": "Amount", "value": f"{eth_value:.4f} ETH", "inline": True},
                {"name": "From", "value": f"[{tx['from'][:8]}...](https://etherscan.io/address/{tx['from']})", "inline": True},
                {"name": "To", "value": f"[{tx['to'][:8]}...](https://etherscan.io/address/{tx['to']})", "inline": True},
                {"name": "Time", "value": datetime.fromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S'), "inline": False}
            ],
            "footer": {
                "text": "Whale Watcher Bot #aiwebarchitects"
            }
        }

        payload = {
            "embeds": [embed],
            "username": "Whale Watcher"
        }

        try:
            res = requests.post(self.webhook_url, json=payload)
            if res.status_code in [200, 204]:
                logger.info(f"Alert sent for TX: {tx['hash']}")
            else:
                logger.error(f"Failed to send Discord alert: {res.status_code} {res.text}")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")

    def start_monitoring(self):
        """
        Main loop to monitor the wallet.
        """
        logger.info(f"Starting monitoring for address: {self.address}")
        logger.info(f"Poll interval: {self.poll_interval}s | Threshold: {self.threshold_eth} ETH")

        # Initial fetch to set state without alerting
        initial_txs = self.get_latest_transactions()
        if initial_txs:
            self.last_tx_hash = initial_txs[0]['hash']
            logger.info(f"Initial state set. Last TX: {self.last_tx_hash}")
        else:
            logger.info("No history found or API error. Starting fresh.")

        while True:
            try:
                time.sleep(self.poll_interval)
                
                transactions = self.get_latest_transactions()
                
                if not transactions:
                    continue

                latest_tx = transactions[0]
                
                # Check if we have a new transaction
                if latest_tx['hash'] != self.last_tx_hash:
                    
                    # Handle case where multiple txs happened during sleep
                    # We iterate backwards until we find the last seen hash
                    new_txs = []
                    for tx in transactions:
                        if tx['hash'] == self.last_tx_hash:
                            break
                        new_txs.append(tx)
                    
                    # If self.last_tx_hash is None (first run was empty), just take the latest
                    if self.last_tx_hash is None:
                        new_txs = [latest_tx]

                    # Process new transactions (oldest to newest)
                    for tx in reversed(new_txs):
                        logger.info(f"New transaction detected: {tx['hash']}")
                        self.send_discord_alert(tx)
                    
                    # Update state
                    self.last_tx_hash = latest_tx['hash']
                
            except KeyboardInterrupt:
                logger.info("Stopping Whale Watcher...")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(10) # Sleep a bit before retrying

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Whale Watcher Bot - Monitor Crypto Wallets')
    
    parser.add_argument('--address', required=True, help='Ethereum Wallet Address to monitor')
    parser.add_argument('--apikey', required=True, help='Etherscan API Key')
    parser.add_argument('--webhook', required=True, help='Discord Webhook URL')
    parser.add_argument('--threshold', type=float, default=0.0, help='Minimum ETH amount to alert (default: 0)')
    parser.add_argument('--interval', type=int, default=60, help='Polling interval in seconds (default: 60)')

    args = parser.parse_args()

    bot = WhaleWatcher(
        address=args.address,
        api_key=args.apikey,
        webhook_url=args.webhook,
        threshold_eth=args.threshold,
        poll_interval=args.interval
    )

    bot.start_monitoring()