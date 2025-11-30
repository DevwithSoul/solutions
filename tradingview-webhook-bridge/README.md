# TradingView Webhook Bridge

This tool acts as a middleware solution to connect TradingView alerts to your brokerage account. It runs a lightweight HTTP server that listens for webhook POST requests from TradingView, validates them, and triggers order execution logic.

## Problem Description

Traders often develop strategies on TradingView but face a disconnect when trying to automate execution. TradingView offers "Webhooks" in their alerts, but brokerages (like Interactive Brokers, Alpaca, or Binance) require complex API authentication and specific payload formats. This bridge solves that by translating the simple webhook into a secure API call.

## Solution Overview

1. **Flask Server**: Listens for incoming HTTP POST requests.
2. **Security**: Validates a user-defined `passphrase` to prevent unauthorized trades.
3. **Standardization**: Accepts a simplified JSON payload from TradingView.
4. **Execution**: Contains a modular function `execute_broker_order` where you can plug in any API (Alpaca, Binance, CCXT, etc.).

## Prerequisites

- Python 3.8+
- A TradingView account (Pro/Pro+ needed for Webhooks).
- A public URL for your local script (we recommend **ngrok** for testing).

## Installation

1. Unzip the tool.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Start the Server

Run the script with a chosen secret passphrase (this acts as your password):

```bash
python tv_webhook_bridge.py --port 5000 --secret mySuperSecret123
```

### 2. Expose to Internet (For Testing)

If running locally, use ngrok to create a public URL:

```bash
ngrok http 5000
```

Copy the HTTPS URL (e.g., `https://abc-123.ngrok-free.app`).

### 3. Configure TradingView Alert

1. Go to your TradingView chart.
2. Create an Alert.
3. Check **Webhook URL** and paste your address with the endpoint:  
   `https://abc-123.ngrok-free.app/webhook`
4. In the **Message** box, paste the following JSON:

```json
{
    "passphrase": "mySuperSecret123",
    "symbol": "{{ticker}}",
    "side": "{{strategy.order.action}}",
    "qty": {{strategy.order.contracts}},
    "price": {{close}}
}
```
*Note: The {{placeholders}} are automatically filled by TradingView if using a Strategy. If using a simple Alert, hardcode the values (e.g., "side": "buy").*

## Configuration

Open `tv_webhook_bridge.py` to configure your Broker API.

Currently, the code runs in **Simulation Mode** (it logs the trade but doesn't send money). To make it live:

1. Locate `execute_broker_order` in the code.
2. Uncomment the `requests.post` logic.
3. Set your API Keys as Environment Variables or edit the `CONFIG` dictionary.

## Recommendations

- **Production**: Do not run this locally for real money. Deploy this script to a VPS (DigitalOcean, AWS EC2) or a Cloud Function (AWS Lambda, Google Cloud Run) to ensure 24/7 uptime.
- **Security**: Always use HTTPS (SSL) when sending webhooks.