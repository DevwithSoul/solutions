#aiwebarchitects
import os
import json
import logging
import argparse
import sys
from flask import Flask, request, jsonify
import ccxt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TV-Bridge")

app = Flask(__name__)

# Global configuration placeholder
CONFIG = {
    "WEBHOOK_PASSPHRASE": None,
    "API_KEY": None,
    "API_SECRET": None,
    "TEST_MODE": False
}

def get_exchange_instance(exchange_id, api_key, api_secret, test_mode=False):
    """
    Factory to create a CCXT exchange instance dynamically.
    """
    if not hasattr(ccxt, exchange_id):
        raise ValueError(f"Exchange '{exchange_id}' not found in CCXT library.")
    
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })
    
    # If the exchange supports a sandbox/testnet and test_mode is on, use it
    if test_mode:
        if 'test' in exchange.urls:
            exchange.urls['api'] = exchange.urls['test']
            logger.info(f"Enabled TEST/SANDBOX mode for {exchange_id}")
        else:
            logger.warning(f"{exchange_id} does not have a standard sandbox URL in CCXT.")
            
    return exchange

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "online", "message": "TradingView Bridge is running"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main endpoint to receive TradingView alerts.
    Expected JSON Payload:
    {
        "passphrase": "YOUR_SECRET_PASSPHRASE",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "side": "buy",
        "type": "market",
        "amount": 0.001,
        "price": 25000 (optional, for limit orders)
    }
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Empty payload"}), 400

        # 1. Security Check
        received_passphrase = data.get('passphrase')
        if CONFIG['WEBHOOK_PASSPHRASE'] and received_passphrase != CONFIG['WEBHOOK_PASSPHRASE']:
            logger.warning("Unauthorized access attempt.")
            return jsonify({"error": "Unauthorized"}), 401

        # 2. Parse Trade Details
        exchange_id = data.get('exchange', 'binance').lower()
        symbol = data.get('symbol')
        side = data.get('side') # 'buy' or 'sell'
        order_type = data.get('type', 'market') # 'market' or 'limit'
        amount = data.get('amount')
        price = data.get('price', None)

        if not all([symbol, side, amount]):
            return jsonify({"error": "Missing required fields: symbol, side, or amount"}), 400

        logger.info(f"Received Alert: {side.upper()} {amount} {symbol} on {exchange_id} ({order_type})")

        # 3. Execute Trade via CCXT
        try:
            exchange = get_exchange_instance(
                exchange_id, 
                CONFIG['API_KEY'], 
                CONFIG['API_SECRET'],
                CONFIG['TEST_MODE']
            )
            
            # Load markets to ensure symbol validity
            # (Optional optimization: cache this if high frequency)
            exchange.load_markets()
            
            if symbol not in exchange.markets:
                return jsonify({"error": f"Symbol {symbol} not found on {exchange_id}"}), 400

            order = None
            if order_type == 'limit':
                if not price:
                    return jsonify({"error": "Price required for limit orders"}), 400
                order = exchange.create_order(symbol, order_type, side, amount, price)
            else:
                # Market order
                order = exchange.create_order(symbol, order_type, side, amount)

            logger.info(f"Order executed successfully: {order['id']}")
            return jsonify({"status": "success", "order_id": order['id'], "details": order}), 200

        except ccxt.NetworkError as e:
            logger.error(f"Network Error: {e}")
            return jsonify({"error": "Exchange Network Error"}), 503
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange Error: {e}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Execution Error: {e}")
            return jsonify({"error": str(e)}), 500

    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

def parse_arguments():
    parser = argparse.ArgumentParser(description='TradingView to Exchange Bridge (CCXT)')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the Flask server on')
    parser.add_argument('--passphrase', type=str, required=True, help='Secret passphrase for webhook authentication')
    parser.add_argument('--api-key', type=str, required=True, help='Exchange API Key')
    parser.add_argument('--api-secret', type=str, required=True, help='Exchange API Secret')
    parser.add_argument('--test-mode', action='store_true', help='Enable Test/Sandbox mode if supported by exchange')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_arguments()
    
    # Set Configuration
    CONFIG['WEBHOOK_PASSPHRASE'] = args.passphrase
    CONFIG['API_KEY'] = args.api_key
    CONFIG['API_SECRET'] = args.api_secret
    CONFIG['TEST_MODE'] = args.test_mode

    print("="*50)
    print(f"Starting TradingView Bridge on port {args.port}")
    print(f"Test Mode: {args.test_mode}")
    print(f"Webhook Endpoint: http://YOUR_IP:{args.port}/webhook")
    print("="*50)
    
    # Run Flask
    # Note: separate 'debug=True' for production usage, use Gunicorn/uWSGI
    app.run(host='0.0.0.0', port=args.port)