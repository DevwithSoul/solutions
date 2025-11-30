#aiwebarchitects
import time
import sys
import argparse
import logging
import requests
from web3 import Web3
from web3.exceptions import BlockNotFound

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def send_telegram_alert(token, chat_id, message):
    """
    Sends a message to a Telegram user or group via the Bot API.
    """
    if not token or not chat_id:
        logger.warning("Telegram credentials not provided. Skipping alert.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")

def monitor_blockchain(rpc_url, threshold_eth, telegram_token, chat_id, poll_interval):
    """
    Main loop to monitor the blockchain for whale transactions.
    """
    # 1. Connect to Ethereum Node
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            logger.error("Failed to connect to RPC URL. Please check your provider.")
            sys.exit(1)
        logger.info(f"Connected to Ethereum Node via {rpc_url}")
    except Exception as e:
        logger.error(f"Connection error: {e}")
        sys.exit(1)

    logger.info(f"Tracking transactions > {threshold_eth} ETH")
    
    last_processed_block = w3.eth.block_number - 1

    while True:
        try:
            current_block_number = w3.eth.block_number

            # If we are caught up, sleep and wait
            if current_block_number <= last_processed_block:
                time.sleep(poll_interval)
                continue

            # Process all new blocks (in case we missed one due to latency)
            for block_num in range(last_processed_block + 1, current_block_number + 1):
                try:
                    # Fetch block with full transactions
                    block = w3.eth.get_block(block_num, full_transactions=True)
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(block['timestamp']))
                    
                    logger.info(f"Scanning Block #{block_num} ({len(block['transactions'])} txs)...")

                    for tx in block['transactions']:
                        # Convert Wei to Ether
                        value_eth = float(w3.from_wei(tx['value'], 'ether'))

                        # Filter logic: Check if value exceeds threshold
                        if value_eth >= threshold_eth:
                            
                            # Basic Decoding Logic
                            tx_hash = tx['hash'].hex()
                            sender = tx['from']
                            receiver = tx['to']
                            
                            # Determine Transaction Type based on Input Data
                            input_data = tx['input'].hex()
                            tx_type = "Native ETH Transfer"
                            
                            # Simple heuristic for ERC-20 Transfer (Method ID: 0xa9059cbb)
                            if input_data.startswith('0xa9059cbb'):
                                tx_type = "ERC-20 Token Transfer (Contract Call)"
                            elif input_data != '0x':
                                tx_type = "Smart Contract Interaction"

                            # Construct Message
                            msg = (
                                f"\U0001F433 *WHALE ALERT* \U0001F433\n"
                                f"*Value:* {value_eth:.2f} ETH\n"
                                f"*Type:* {tx_type}\n"
                                f"*Block:* {block_num}\n"
                                f"*From:* `{sender}`\n"
                                f"*To:* `{receiver}`\n"
                                f"[View on Etherscan](https://etherscan.io/tx/{tx_hash})"
                            )

                            logger.info(f"Whale detected: {value_eth} ETH in block {block_num}")
                            send_telegram_alert(telegram_token, chat_id, msg)

                    last_processed_block = block_num

                except BlockNotFound:
                    logger.warning(f"Block {block_num} not found yet, retrying...")
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error processing block {block_num}: {e}")
            
        except KeyboardInterrupt:
            logger.info("Stopping Whale Tracker...")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Global loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Argument Parsing for CLI usage
    parser = argparse.ArgumentParser(description="Real-Time Crypto Whale Tracker")
    
    parser.add_argument("--rpc", type=str, required=True, 
                        help="Ethereum HTTP RPC URL (e.g., Infura, Alchemy, or public node)")
    
    parser.add_argument("--threshold", type=float, default=10.0, 
                        help="Minimum ETH value to trigger alert (default: 10.0)")
    
    parser.add_argument("--telegram-token", type=str, default="", 
                        help="Telegram Bot API Token (optional)")
    
    parser.add_argument("--chat-id", type=str, default="", 
                        help="Telegram Chat ID (optional)")
    
    parser.add_argument("--interval", type=int, default=10, 
                        help="Polling interval in seconds (default: 10)")

    args = parser.parse_args()

    print("="*50)
    print("   CRYPTO WHALE TRACKER STARTED")
    print("="*50)
    
    monitor_blockchain(
        rpc_url=args.rpc,
        threshold_eth=args.threshold,
        telegram_token=args.telegram_token,
        chat_id=args.chat_id,
        poll_interval=args.interval
    )
