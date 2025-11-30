# TradingView-to-Exchange Bridge

## Problem Description
Traders using TradingView often develop profitable Pine Script strategies but struggle to automate the execution. TradingView's webhook alerts send raw JSON, but cryptocurrency exchanges (like Binance, Bybit, Kraken) require complex API request signing (HMAC SHA256) and specific header formatting. This disconnect prevents direct automation.

## Solution Overview
This tool acts as a **Middleware Bridge**. It runs a lightweight Python Flask server that:
1. Listens for Webhook POST requests from TradingView.
2. Validates a security passphrase.
3. Uses the **CCXT** library (CryptoCurrency eXchange Trading Library) to handle the complex authentication and API communication with over 100+ supported exchanges.
4. Executes the trade and returns the result.

## Prerequisites
1. **Python 3.8+** installed.
2. **Public IP Address** or a tunneling service like **Ngrok** (to expose your local server to the internet).
3. **API Keys** from your chosen exchange (e.g., Binance, Kraken) with "Spot Trading" or "Futures Trading" permissions enabled.

## Installation

1. **Unzip the tool**:
   ```bash
   unzip tradingview-exchange-bridge.zip
   cd tradingview-exchange-bridge
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Start the server by providing your API keys and a custom passphrase (this password protects your bot from random internet requests).

```bash
python tradingview_bridge.py --passphrase "my_super_secret_password" --api-key "YOUR_EXCHANGE_API_KEY" --api-secret "YOUR_EXCHANGE_SECRET" --port 5000
```

### Optional Flags
- `--test-mode`: Attempts to use the exchange's sandbox/testnet URL if available.
- `--port`: Change the listening port (default 5000).

## Configuration (TradingView Side)

1. Go to your TradingView Alert.
2. In the **Webhook URL** field, enter your server's address:
   - `http://YOUR_PUBLIC_IP:5000/webhook`
   - OR if using Ngrok: `https://random-id.ngrok.io/webhook`
3. In the **Message** field, paste the following JSON (customize the values):

```json
{
    "passphrase": "my_super_secret_password",
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "side": "buy",
    "type": "market",
    "amount": 0.001
}
```

### JSON Parameters
- `passphrase`: Must match the one you started the server with.
- `exchange`: The ID of the exchange (e.g., `binance`, `kraken`, `coinbasepro`). Must be supported by CCXT.
- `symbol`: The trading pair (e.g., `BTC/USDT`, `ETH/USD`).
- `side`: `buy` or `sell`.
- `type`: `market` or `limit`.
- `amount`: The quantity to trade.
- `price`: (Required only for `limit` orders) The limit price.

## Recommendations
- **Security**: Do not run this on a public server without SSL (HTTPS). For production, use a reverse proxy like Nginx with Let's Encrypt.
- **Testing**: Always test with minimal amounts or `--test-mode` first.
- **Latency**: Host this script on a VPS (like AWS EC2 or DigitalOcean) close to the exchange's servers for faster execution.