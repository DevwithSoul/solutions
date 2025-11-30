#aiwebarchitects
import asyncio
import json
import logging
import argparse
import sys
from datetime import datetime
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class CryptoArbitrageBot:
    def __init__(self, threshold_percent: float, symbol: str = 'BTC'):
        """
        Initialize the bot.
        
        :param threshold_percent: The percentage difference required to trigger an alert.
        :param symbol: The asset to monitor (default BTC against USDT).
        """
        self.threshold = threshold_percent
        self.symbol = symbol
        # Shared state to store latest prices: { 'exchange_name': {'bid': float, 'ask': float} }
        self.prices = {}
        self.lock = asyncio.Lock()

    async def update_price(self, exchange: str, bid: float, ask: float):
        """
        Update the price for a specific exchange and trigger the arbitrage check.
        """
        async with self.lock:
            self.prices[exchange] = {
                'bid': bid,
                'ask': ask,
                'timestamp': datetime.now()
            }
            await self.check_arbitrage()

    async def check_arbitrage(self):
        """
        Compare prices across available exchanges in the state.
        Logic: If Exchange A's Bid (Buy Price) > Exchange B's Ask (Sell Price), profit exists.
        """
        exchanges = list(self.prices.keys())
        if len(exchanges) < 2:
            return

        # Simple O(N^2) comparison - fine for small number of exchanges
        for i in range(len(exchanges)):
            for j in range(len(exchanges)):
                if i == j:
                    continue
                
                ex_buy = exchanges[i] # We sell here (hit the bid)
                ex_sell = exchanges[j] # We buy here (hit the ask)
                
                price_sell_to_market = self.prices[ex_buy]['bid']
                price_buy_from_market = self.prices[ex_sell]['ask']

                if price_buy_from_market == 0: continue

                # Calculate spread percentage
                diff = price_sell_to_market - price_buy_from_market
                spread_pct = (diff / price_buy_from_market) * 100

                if spread_pct > self.threshold:
                    logger.warning(
                        f"\nARBITRAGE OPPORTUNITY DETECTED!\n"
                        f"Buy {self.symbol} on {ex_sell} @ {price_buy_from_market}\n"
                        f"Sell {self.symbol} on {ex_buy}  @ {price_sell_to_market}\n"
                        f"Spread: {spread_pct:.4f}% (Diff: ${diff:.2f})"
                    )
                else:
                    # Debug log to show it's working even without arb
                    logger.debug(f"Spread {ex_sell}->{ex_buy}: {spread_pct:.4f}%")

    async def connect_binance(self):
        """
        Connect to Binance WebSocket Stream (Book Ticker).
        Docs: https://binance-docs.github.io/apidocs/spot/en/#individual-symbol-book-ticker-streams
        """
        uri = "wss://stream.binance.com:9443/ws/btcusdt@bookTicker"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    logger.info("Connected to Binance WS")
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        # Binance format: 'b' = bid price, 'a' = ask price
                        bid = float(data['b'])
                        ask = float(data['a'])
                        await self.update_price('Binance', bid, ask)
            except Exception as e:
                logger.error(f"Binance connection error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def connect_kraken(self):
        """
        Connect to Kraken WebSocket Stream.
        Docs: https://docs.kraken.com/websockets/
        """
        uri = "wss://ws.kraken.com"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    logger.info("Connected to Kraken WS")
                    
                    # Subscribe to ticker
                    subscribe_msg = {
                        "event": "subscribe",
                        "pair": ["XBT/USDT"], # Kraken uses XBT for Bitcoin
                        "subscription": {"name": "ticker"}
                    }
                    await websocket.send(json.dumps(subscribe_msg))

                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        # Kraken sends heartbeats and event status messages
                        if isinstance(data, list):
                            # Data format: [channelID, {b: [price, ...], a: [price, ...]}, channelName, pair]
                            ticker_data = data[1]
                            if 'b' in ticker_data and 'a' in ticker_data:
                                # Kraken: 'b': [price, whole_lot_volume, lot_volume]
                                bid = float(ticker_data['b'][0])
                                ask = float(ticker_data['a'][0])
                                await self.update_price('Kraken', bid, ask)
            except Exception as e:
                logger.error(f"Kraken connection error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def start(self):
        """
        Start all exchange connectors concurrently.
        """
        logger.info(f"Starting Arbitrage Monitor for {self.symbol}/USDT with threshold {self.threshold}%")
        await asyncio.gather(
            self.connect_binance(),
            self.connect_kraken()
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time Crypto Arbitrage Monitor")
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=0.1, 
        help="Minimum price difference percentage to trigger alert (default: 0.1%)"
    )
    
    args = parser.parse_args()
    
    bot = CryptoArbitrageBot(threshold_percent=args.threshold)
    
    try:
        # Run the asyncio event loop
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        sys.exit(0)