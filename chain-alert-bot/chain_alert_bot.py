# aiwebarchitects
import asyncio
import json
import logging
import argparse
import sys
from datetime import datetime

# External libraries
from web3 import AsyncWeb3
from web3.providers import AsyncWebsocketProvider
from web3.exceptions import Web3Exception
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants for Uniswap V2 Factory (Ethereum Mainnet)
# This is the contract that generates 'PairCreated' events when new liquidity pools are added.
UNISWAP_V2_FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"

# Minimal ABI for the Factory to listen to PairCreated events
FACTORY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "token0", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "token1", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "pair", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "name": "PairCreated",
        "type": "event"
    }
]

# Minimal ABI for ERC20 Tokens to fetch symbols (e.g., "ETH", "USDT")
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

class ChainAlertBot:
    def __init__(self, rpc_url, bot_token, chat_id):
        self.rpc_url = rpc_url
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.w3 = None
        self.factory_contract = None
        self.last_block = None

    async def send_telegram_alert(self, message):
        """
        Sends a notification to the specified Telegram Chat ID.
        """
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Telegram notification sent successfully.")
                    else:
                        logger.error(f"Failed to send Telegram notification: {await response.text()}")
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")

    async def get_token_info(self, token_address):
        """
        Fetches the symbol of an ERC20 token. Returns 'UNKNOWN' if it fails.
        """
        try:
            # Create contract instance for the token
            token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            symbol = await token_contract.functions.symbol().call()
            return symbol
        except Exception as e:
            logger.warning(f"Could not fetch info for {token_address}: {e}")
            return "UNKNOWN"

    async def handle_event(self, event):
        """
        Process the decoded event data and trigger an alert.
        """
        try:
            args = event['args']
            token0_address = args['token0']
            token1_address = args['token1']
            pair_address = args['pair']
            
            logger.info(f"New Pair Detected: {pair_address}")

            # Fetch symbols asynchronously
            symbol0, symbol1 = await asyncio.gather(
                self.get_token_info(token0_address),
                self.get_token_info(token1_address)
            )

            # Construct the alert message
            message = (
                f"🚨 *New Liquidity Pool Detected* 🚨\n\n"
                f"**Pair:** {symbol0} / {symbol1}\n"
                f"**Address:** `{pair_address}`\n"
                f"**Token 0:** `{token0_address}`\n"
                f"**Token 1:** `{token1_address}`\n"
                f"\n[View on Etherscan](https://etherscan.io/address/{pair_address})"
            )

            await self.send_telegram_alert(message)

        except Exception as e:
            logger.error(f"Error handling event: {e}")

    async def listen_loop(self):
        """
        Main loop that subscribes to new blocks and checks for events.
        Note: While 'subscribe' is ideal, 'get_logs' on new blocks is often more stable 
        across different RPC providers for a general-purpose bot.
        """
        logger.info(f"Connecting to RPC: {self.rpc_url}")
        
        # Initialize AsyncWeb3 with WebSocket
        self.w3 = AsyncWeb3(AsyncWebsocketProvider(self.rpc_url))
        
        if not await self.w3.is_connected():
            logger.error("Failed to connect to WebSocket Provider. Check your URL.")
            return

        logger.info("Connected to Blockchain. Initializing Contract...")
        
        self.factory_contract = self.w3.eth.contract(
            address=UNISWAP_V2_FACTORY_ADDRESS, 
            abi=FACTORY_ABI
        )

        logger.info("Listening for 'PairCreated' events... Press Ctrl+C to stop.")

        # Create an event filter for the PairCreated event
        # We loop and poll the filter for changes. This is robust for most WSS implementations.
        from_block = self.last_block + 1 if self.last_block is not None else 'latest'
        event_filter = await self.factory_contract.events.PairCreated.create_filter(from_block=from_block)

        while True:
            try:
                # Fetch new entries
                new_entries = await event_filter.get_new_entries()
                
                for event in new_entries:
                    await self.handle_event(event)
                    if hasattr(event, 'blockNumber') and event.blockNumber is not None:
                        if self.last_block is None or event.blockNumber > self.last_block:
                            self.last_block = event.blockNumber
                
                # Sleep to prevent spamming the node
                await asyncio.sleep(2)
                
            except Web3Exception as w3e:
                logger.error(f"Web3 Connection Error: {w3e}. Reconnecting...")
                await asyncio.sleep(5)
                # Re-instantiate filter on error using last known block to avoid missing events
                from_block = self.last_block + 1 if self.last_block is not None else 'latest'
                event_filter = await self.factory_contract.events.PairCreated.create_filter(from_block=from_block)
            except asyncio.CancelledError:
                logger.info("Bot stopped by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)

async def main():
    parser = argparse.ArgumentParser(description="Real-Time On-Chain Alert Bot")
    parser.add_argument("--rpc", required=True, help="WebSocket RPC URL (e.g., wss://mainnet.infura.io/ws/v3/...)")
    parser.add_argument("--token", required=True, help="Telegram Bot Token")
    parser.add_argument("--chat", required=True, help="Telegram Chat ID to send alerts to")
    
    args = parser.parse_args()
    
    bot = ChainAlertBot(args.rpc, args.token, args.chat)
    await bot.listen_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
