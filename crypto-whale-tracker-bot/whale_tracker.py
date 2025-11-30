#aiwebarchitects
import requests
import time
import argparse
import logging
from datetime import datetime

# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class WhaleTracker:
    def __init__(self, etherscan_key, telegram_token, chat_id, wallets, threshold, interval):
        self.etherscan_key = etherscan_key
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        # Clean and split wallet addresses
        self.wallets = [w.strip() for w in wallets.split(',') if w.strip()]
        self.threshold = float(threshold)
        self.interval = int(interval)
        self.base_url = "https://api.etherscan.io/api"
        
        # Dictionary to store the last seen transaction hash for each wallet
        self.last_seen_tx = {wallet: None for wallet in self.wallets}

    def get_latest_transactions(self, address):
        """
        Fetch the last 5 transactions for a specific address from Etherscan.
        We limit to 5 to minimize data transfer, as we poll frequently.
        """
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': 5,  # Fetch small batch
            'sort': 'desc', # Newest first
            'apikey': self.etherscan_key
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if data['status'] == '1' and data['message'] == 'OK':
                return data['result']
            elif data['message'] == 'No transactions found':
                return []
            else:
                logging.warning(f"Etherscan API returned warning for {address}: {data['message']}")
                return []
        except Exception as e:
            logging.error(f"Network error fetching data for {address}: {e}")
            return []

    def send_telegram_alert(self, tx, wallet_watched):
        """
        Format transaction data and send a rich text notification to Telegram.
        """
        try:
            # Convert Wei to ETH
            value_eth = float(tx['value']) / 10**18
        except ValueError:
            value_eth = 0.0

        # Filter based on threshold
        if value_eth < self.threshold:
            return

        tx_hash = tx['hash']
        sender = tx['from']
        receiver = tx['to']
        
        # Format timestamp
        try:
            block_time = datetime.fromtimestamp(int(tx['timeStamp'])).strftime('%Y-%m-%d %H:%M:%S')
        except:
            block_time = "Unknown"

        # Determine flow direction
        if sender.lower() == wallet_watched.lower():
            direction = "OUTGOING 🔴"
            counterparty = receiver
        else:
            direction = "INCOMING 🟢"
            counterparty = sender

        # Construct HTML message
        message = (
            f"🐋 <b>Whale Alert!</b>\n"
            f"--------------------------\n"
            f"<b>Type:</b> {direction}\n"
            f"<b>Value:</b> {value_eth:,.4f} ETH\n"
            f"<b>Wallet:</b> <code>{wallet_watched}</code>\n"
            f"<b>Counterparty:</b> <code>{counterparty}</code>\n"
            f"<b>Time:</b> {block_time}\n"
            f"<b>Link:</b> <a href='https://etherscan.io/tx/{tx_hash}'>View on Etherscan</a>"
        )

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        try:
            resp = requests.post(url, data=payload, timeout=10)
            if resp.status_code == 200:
                logging.info(f"Alert sent for Tx: {tx_hash}")
            else:
                logging.error(f"Telegram API Error: {resp.text}")
        except Exception as e:
            logging.error(f"Failed to send Telegram alert: {e}")

    def initialize(self):
        """
        Fetch the latest transaction for each wallet to establish a baseline.
        This prevents the bot from alerting on old transactions when it starts.
        """
        logging.info("Initializing trackers... (This prevents alerting on historical data)")
        for wallet in self.wallets:
            txs = self.get_latest_transactions(wallet)
            if txs:
                self.last_seen_tx[wallet] = txs[0]['hash']
                logging.info(f"[{wallet[:6]}...] Baseline set to Tx: {txs[0]['hash'][:10]}...")
            else:
                logging.info(f"[{wallet[:6]}...] No history found. Waiting for first Tx.")
            # Small sleep to respect API rate limits (5 calls/sec for free tier)
            time.sleep(0.25)

    def monitor(self):
        """
        Main loop to poll for new transactions.
        """
        self.initialize()
        logging.info(f"Monitoring started for {len(self.wallets)} wallets. Threshold: {self.threshold} ETH.")

        while True:
            for wallet in self.wallets:
                txs = self.get_latest_transactions(wallet)
                
                if not txs:
                    continue

                last_known = self.last_seen_tx[wallet]
                new_txs = []

                # Identify new transactions since the last known hash
                for tx in txs:
                    if tx['hash'] == last_known:
                        break
                    new_txs.append(tx)
                
                # If new transactions exist, process them
                if new_txs:
                    # Process chronological order (oldest of the new -> newest of the new)
                    for tx in reversed(new_txs):
                        self.send_telegram_alert(tx, wallet)
                    
                    # Update state
                    self.last_seen_tx[wallet] = new_txs[0]['hash']

                # Rate limiting between wallet checks
                time.sleep(0.25)

            # Wait for the next polling interval
            time.sleep(self.interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Real-Time Crypto Whale Tracker Bot')
    
    # Required Arguments
    parser.add_argument('--etherscan_key', required=True, help='Your Etherscan API Key')
    parser.add_argument('--telegram_token', required=True, help='Your Telegram Bot Token')
    parser.add_argument('--chat_id', required=True, help='Your Telegram Chat ID')
    parser.add_argument('--wallets', required=True, help='Comma-separated list of Ethereum wallet addresses')
    
    # Optional Arguments
    parser.add_argument('--threshold', default=0.1, type=float, help='Minimum ETH value to trigger alert (default: 0.1)')
    parser.add_argument('--interval', default=30, type=int, help='Polling interval in seconds (default: 30)')

    args = parser.parse_args()

    tracker = WhaleTracker(
        args.etherscan_key,
        args.telegram_token,
        args.chat_id,
        args.wallets,
        args.threshold,
        args.interval
    )
    
    try:
        tracker.monitor()
    except KeyboardInterrupt:
        logging.info("\nStopping Whale Tracker... Goodbye!")
    except Exception as e:
        logging.critical(f"Unexpected error: {e}")