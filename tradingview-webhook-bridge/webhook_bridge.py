#aiwebarchitects
import argparse
import json
import sys
from flask import Flask, request, jsonify
import ccxt

# -----------------------------------------------------------------------------
# TradingView Webhook Bridge
# -----------------------------------------------------------------------------
# This script runs a lightweight HTTP server using Flask.
# It listens for POST requests from TradingView alerts.
# It uses the CCXT library to connect to over 100+ cryptocurrency exchanges.
#
# SECURITY WARNING: 
# This is a simplified version. In a true production environment, use a WSGI 
# server like Gunicorn, use HTTPS (SSL), and manage secrets via Environment Variables.
# -----------------------------------------------------------------------------

app = Flask(__name__)

# Global variables for exchange connection and security
exchange_client = None
webhook_passphrase = None

def setup_exchange(exchange_id, api_key, secret, test_mode=False):
    """
    Initializes the CCXT exchange client.
    """
    try:
        # check if exchange exists in ccxt
        if exchange_id not in ccxt.exchanges:
            raise ValueError(f"Exchange '{exchange_id}' not found in CCXT library.")

        exchange_class = getattr(ccxt, exchange_id)
        client = exchange_class({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        })
        
        if test_mode:
            client.set_sandbox_mode(True)
            print(f"[INFO] {exchange_id} Sandbox/Testnet mode enabled.")

        # Verify connection by fetching balance (lightweight check)
        # Note: Some exchanges require specific permissions to fetch balance.
        # We wrap this in a try-catch specifically for connection verification.
        try:
            client.load_markets()
            print(f"[SUCCESS] Connected to {exchange_id} successfully.")
        except Exception as e:
            print(f"[WARNING] Could not load markets (API keys might be invalid or restricted): {e}")
        
        return client
    except Exception as e:
        print(f"[ERROR] Failed to setup exchange: {e}")
        sys.exit(1)

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint to receive TradingView Alerts.
    Expected JSON payload:
    {
        "passphrase": "your_configured_passphrase",
        "symbol": "BTC/USDT",
        "side": "buy",
        "type": "market",
        "amount": 0.001,
        "price": 20000 (optional, for limit orders)
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    # 1. Security Check
    if webhook_passphrase and data.get('passphrase') != webhook_passphrase:
        print("[ALERT] Unauthorized access attempt.")
        return jsonify({"status": "error", "message": "Invalid passphrase"}), 401

    # 2. Parse Order Details
    try:
        symbol = data.get('symbol')
        side = data.get('side').lower() # 'buy' or 'sell'
        order_type = data.get('type', 'market').lower() # 'market' or 'limit'
        amount = float(data.get('amount'))
        price = data.get('price') # Can be None for market orders

        if not symbol or not side or not amount:
            return jsonify({"status": "error", "message": "Missing required fields (symbol, side, amount)"}), 400

        print(f"[SIGNAL RECEIVED] {side.upper()} {amount} {symbol} ({order_type})")

        # 3. Execute Order
        # Note: CCXT unifies the API calls, but error handling is crucial.
        order = None
        if order_type == 'market':
            order = exchange_client.create_market_order(symbol, side, amount)
        elif order_type == 'limit':
            if not price:
                return jsonify({"status": "error", "message": "Price required for limit order"}), 400
            order = exchange_client.create_limit_order(symbol, side, amount, float(price))
        else:
            return jsonify({"status": "error", "message": "Unsupported order type"}), 400

        print(f"[ORDER EXECUTED] ID: {order.get('id', 'Unknown')}")
        return jsonify({"status": "success", "order_id": order.get('id'), "details": order}), 200

    except ccxt.NetworkError as e:
        print(f"[NETWORK ERROR] {e}")
        return jsonify({"status": "error", "message": "Exchange Network Error"}), 503
    except ccxt.ExchangeError as e:
        print(f"[EXCHANGE ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "exchange": exchange_client.id if exchange_client else "disconnected"}), 200

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TradingView Webhook Bridge via CCXT")
    
    # Server Configuration
    parser.add_argument('--port', type=int, default=5000, help="Port to run the Flask server on (default: 5000)")
    parser.add_argument('--passphrase', type=str, required=True, help="Secret string to verify webhook authenticity")
    
    # Exchange Configuration
    parser.add_argument('--exchange', type=str, required=True, help="Exchange ID (e.g., binance, kraken, coinbase)")
    parser.add_argument('--api-key', type=str, required=True, help="Exchange API Key")
    parser.add_argument('--secret', type=str, required=True, help="Exchange API Secret")
    parser.add_argument('--sandbox', action='store_true', help="Use Exchange Sandbox/Testnet if available")

    args = parser.parse_args()

    # Initialize Global Config
    webhook_passphrase = args.passphrase
    
    print("--------------------------------------------------")
    print("Starting TradingView Webhook Bridge")
    print(f"Exchange: {args.exchange}")
    print(f"Port: {args.port}")
    print("--------------------------------------------------")

    # Setup Exchange
    exchange_client = setup_exchange(args.exchange, args.api_key, args.secret, args.sandbox)

    # Start Server
    # host='0.0.0.0' allows external connections (required for receiving webhooks from the internet)
    app.run(host='0.0.0.0', port=args.port)