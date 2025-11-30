#aiwebarchitects
import time
import sys
import argparse
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from datetime import datetime

"""
Real-Time Crypto Whale Tracker Bot

Description:
    This script connects to an Ethereum-compatible blockchain node (RPC),
    monitors the latest blocks for transactions involving a watchlist of addresses,
    and sends real-time alerts to a Discord Webhook.

Features:
    - Monitors native currency transfers (ETH, BNB, MATIC, etc.).
    - Filters by minimum value (Whale threshold).
    - Push notifications to Discord.
    - Auto-reconnect logic.

Usage Example:
    python crypto_whale_tracker.py --rpc "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY" --wallets "0x123...,0x456..." --webhook "https://discord.com/api/webhooks/..." --threshold 1.5
"""

class WhaleTracker:
    def __init__(self, rpc_url, watchlist, webhook_url, threshold=0.0):
        self.rpc_url = rpc_url
        self.watchlist = [w.lower() for w in watchlist]
        self.webhook_url = webhook_url
        self.threshold = threshold
        self.w3 = None
        self.last_processed_block = 0

    def connect(self):
        """Establish connection to the Blockchain Node."""
        print(f"[*] Connecting to RPC: {self.rpc_url}")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Inject middleware for PoA chains (like BSC or Polygon) just in case
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if self.w3.is_connected():
            print("[+] Connection Successful!")
            print(f"[+] Monitoring {len(self.watchlist)} wallets for > {self.threshold} ETH transactions.")
            return True
        else:
            print("[-] Connection Failed. Please check your RPC URL.")
            return False

    def send_discord_alert(self, tx_hash, from_addr, to_addr, value_eth, block_num):
        """Sends a formatted alert to Discord."""
        print(f"[!] WHALE ALERT: {value_eth} ETH detected from {from_addr} to {to_addr}")
        
        # Determine if it's an Inflow or Outflow relative to watchlist
        direction = "UNKNOWN"
        if from_addr in self.watchlist and to_addr in self.watchlist:
            direction = "INTERNAL TRANSFER ↔️"
        elif from_addr in self.watchlist:
            direction = "OUTFLOW 🔴"
        elif to_addr in self.watchlist:
            direction = "INFLOW 🟢"

        # Create Discord Embed Payload
        payload = {
            "username": "Whale Tracker Bot",
            "embeds": [{
                "title": f"{direction} Transaction Detected",
                "color": 3066993,  # Greenish
                "fields": [
                    {"name": "Amount", "value": f"{value_eth:.4f} ETH", "inline": True},
                    {"name": "Block", "value": str(block_num), "inline": True},
                    {"name": "From", "value": f"`{from_addr}`", "inline": False},
                    {"name": "To", "value": f"`{to_addr}`", "inline": False},
                    {"name": "Transaction Hash", "value": f"[View on Etherscan](https://etherscan.io/tx/{tx_hash})", "inline": False}
                ],
                "footer": {
                    "text": f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }]
        }

        try:
            requests.post(self.webhook_url, json=payload)
        except Exception as e:
            print(f"[-] Failed to send webhook: {e}")

    def process_block(self, block_number):
        """Fetches a block and iterates through its transactions."""
        try:
            # Get block with full transaction objects
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            
            for tx in block.transactions:
                # Extract transaction details
                # Note: Some transactions might not have a 'to' address (contract creation)
                tx_to = tx.get('to')
                tx_from = tx.get('from')
                tx_hash = tx.get('hash').hex()
                value_wei = tx.get('value')
                
                if not tx_to or not tx_from:
                    continue

                # Normalize addresses
                tx_to = tx_to.lower()
                tx_from = tx_from.lower()

                # Check if transaction involves watchlist
                if tx_to in self.watchlist or tx_from in self.watchlist:
                    # Convert Wei to Ether
                    value_eth = float(self.w3.from_wei(value_wei, 'ether'))

                    # Check threshold
                    if value_eth >= self.threshold:
                        self.send_discord_alert(tx_hash, tx_from, tx_to, value_eth, block_number)

        except Exception as e:
            print(f"[-] Error processing block {block_number}: {e}")

    def start_monitoring(self):
        """Main loop to poll for new blocks."""
        if not self.w3 or not self.w3.is_connected():
            if not self.connect():
                return

        # Start from the latest block
        self.last_processed_block = self.w3.eth.block_number
        print(f"[*] Starting monitor from block: {self.last_processed_block}")

        while True:
            try:
                current_block = self.w3.eth.block_number

                # If new block(s) found
                if current_block > self.last_processed_block:
                    # Process all missed blocks (in case logic is slower than chain)
                    for block_num in range(self.last_processed_block + 1, current_block + 1):
                        print(f"[*] Scanning Block {block_num}...")
                        self.process_block(block_num)
                    
                    self.last_processed_block = current_block
                
                # Sleep briefly to avoid spamming the RPC node (approx block time is 12s for ETH)
                time.sleep(5)

            except KeyboardInterrupt:
                print("\n[*] Stopping Whale Tracker.")
                sys.exit(0)
            except Exception as e:
                print(f"[-] Connection error: {e}. Retrying in 10s...")
                time.sleep(10)
                self.connect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-Time Crypto Whale Tracker")
    
    parser.add_argument('--rpc', required=True, help="RPC URL (e.g., Infura, Alchemy, or local node)")
    parser.add_argument('--wallets', required=True, help="Comma-separated list of wallet addresses to monitor")
    parser.add_argument('--webhook', required=True, help="Discord Webhook URL for alerts")
    parser.add_argument('--threshold', type=float, default=0.0, help="Minimum ETH value to trigger alert (default: 0)")

    args = parser.parse_args()

    # Parse wallets string into list
    wallet_list = [w.strip() for w in args.wallets.split(',') if w.strip()]

    if not wallet_list:
        print("Error: No valid wallets provided.")
        sys.exit(1)

    tracker = WhaleTracker(
        rpc_url=args.rpc,
        watchlist=wallet_list,
        webhook_url=args.webhook,
        threshold=args.threshold
    )

    tracker.start_monitoring()