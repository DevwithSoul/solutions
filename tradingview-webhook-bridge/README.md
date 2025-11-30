# TradingView Webhook Bridge

## Problem Description
Traders often develop sophisticated strategies on TradingView using Pine Script. However, automating the execution of these strategies is difficult because TradingView only sends alerts (emails, popups, or webhooks) and does not natively connect to most crypto exchanges for automated trading. Traders need a middleware solution to translate these alerts into actual API orders.

## Solution Overview
This tool acts as a bridge server. It listens for HTTP POST requests (Webhooks) from TradingView and uses the `ccxt` library to execute orders on your chosen cryptocurrency exchange (Binance, Kraken, Bybit, Coinbase, etc.).

**Features:**
- **Multi-Exchange Support:** Works with any exchange supported by CCXT.
- **Security:** Validates payloads using a custom passphrase.
- **Order Types:** Supports Market and Limit orders.
- **Lightweight:** Built on Flask and Python.

## Prerequisites
1. **Python 3.8+** installed.
2. **Public IP or Tunneling:** TradingView needs to reach your computer. If running locally, use [Ngrok](https://ngrok.com/) to expose your localhost to the internet.
3. **Exchange API Keys:** Create an API Key and Secret on your exchange with "Spot Trading" permissions.
4. **TradingView Account:** A plan that supports Webhooks (Essential/Pro or higher).

## Installation

1. **Unzip the tool:**
   Extract `tradingview-webhook-bridge.zip`.

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the server using the command line. Replace the placeholders with your actual API credentials.

```bash
python webhook_bridge.py --exchange binance --api-key YOUR_API_KEY --secret YOUR_API_SECRET --passphrase mySecretPassword123 --port 5000
```

*Add `--sandbox` if you want to use the exchange's testnet (if supported by the exchange).*

If successful, you will see:
```
[SUCCESS] Connected to binance successfully.
 * Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
```

## Configuration (TradingView)

1. **Create an Alert** in your TradingView chart.
2. In the **Webhook URL** field, enter your server address:
   - If using Ngrok: `https://your-ngrok-id.ngrok.io/webhook`
   - If using a VPS: `http://YOUR_VPS_IP:5000/webhook`
3. In the **Message** field, paste the following JSON (ensure you modify the symbol and amount):

```json
{
  "passphrase": "mySecretPassword123",
  "symbol": "BTC/USDT",
  "side": "buy",
  "type": "market",
  "amount": 0.001
}
```

For a **Sell** signal, change side to `"sell"`.

## Recommendations
- **Hosting:** For 24/7 trading, host this script on a cloud VPS (AWS EC2, DigitalOcean, etc.) rather than your local laptop.
- **HTTPS:** TradingView prefers HTTPS. Use a reverse proxy (Nginx) with Let's Encrypt or use Ngrok for secure tunneling.
- **Logs:** Monitor the console output to verify trades are executing correctly.