# TradingView-to-Exchange Bridge

## Problem Description
Traders often develop profitable strategies using Pine Script on TradingView. However, TradingView's alert system only sends basic webhooks (HTTP requests). It cannot directly sign requests cryptographically or manage the complex headers required by cryptocurrency exchanges (like Binance, Kraken, or Bybit). This creates a gap between signal generation and trade execution.

## Solution Overview
This project provides a lightweight, production-ready middleware server written in Python. It acts as a bridge:
1.  **Listens** for webhook POST requests from TradingView.
2.  **Authenticates** the request using a custom passphrase.
3.  **Translates** the alert payload into a valid exchange order.
4.  **Executes** the trade using the `ccxt` library (supporting 100+ exchanges).

## Prerequisites
*   Python 3.8+
*   An account on a crypto exchange (e.g., Binance, KuCoin, Kraken).
*   API Key and Secret from your exchange (Enable "Spot Trading", Disable "Withdrawal").
*   A TradingView account (Pro/Premium needed for Webhooks).
*   A public IP or a tunneling service (like Ngrok) to expose your local server to the internet.

## Installation

1.  **Extract the tool**:
    ```bash
    unzip tradingview-exchange-bridge.zip
    cd tradingview-exchange-bridge
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the server via command line. You must provide your API credentials.

### Basic Start (Binance example)
```bash
python tradingview_bridge.py --key "YOUR_API_KEY" --secret "YOUR_API_SECRET" --passphrase "MySecurePass123"
```

### Advanced Options
```bash
python tradingview_bridge.py \
  --port 8080 \
  --key "YOUR_KEY" \
  --secret "YOUR_SECRET" \
  --exchange kraken \
  --passphrase "MySecurePass123" \
  --testnet
```

*   `--testnet`: Attempts to use the exchange's sandbox environment (if supported by ccxt).
*   `--exchange`: Specify default exchange ID (see [ccxt supported exchanges](https://github.com/ccxt/ccxt)).

## Configuration (TradingView Setup)

1.  **Expose Server**: Ensure your server is reachable. If running locally, use Ngrok: `ngrok http 5000`.
2.  **Create Alert**: In TradingView, create an Alert.
3.  **Webhook URL**: Paste your URL: `http://your-server-ip:5000/webhook`.
4.  **Message**: Paste the following JSON format into the "Message" box:

```json
{
    "passphrase": "MySecurePass123",
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "side": "buy",
    "type": "market",
    "amount": 0.001
}
```

*   **Dynamic Values**: You can use TradingView placeholders like `{{ticker}}`, `{{close}}`, etc., but strict JSON syntax is safer for this bridge.

## Recommendations
*   **Security**: NEVER expose this server publicly without SSL (HTTPS) in a real production environment. Use a reverse proxy like Nginx with Let's Encrypt.
*   **Latency**: Host this script on a VPS (AWS, DigitalOcean) close to the exchange's servers for faster execution.
*   **Error Handling**: The script logs errors to the console. Monitor these logs to ensure trades are firing correctly.