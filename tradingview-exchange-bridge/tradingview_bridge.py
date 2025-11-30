#aiwebarchitects
import os
import json
import logging
import argparse
from flask import Flask, request, jsonify
import ccxt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_exchange_instance(exchange_id, api_key, api_secret, testnet=False):
    """
    Factory function to create a CCXT exchange instance.
    """
    if exchange_id not in ccxt.exchanges:
        raise ValueError(f"Exchange '{exchange_id}' not found in CCXT library.")
    
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'} # Default to spot, can be adjusted for futures
    })
    
    if testnet:
        if 'test' in exchange.urls:
            exchange.set_sandbox_mode(True)
            logger.info(f"Enabled Testnet/Sandbox mode for {exchange_id}")
        else:
            logger.warning(f"Exchange {exchange_id} does not support sandbox mode via CCXT standard methods.")
            
    return exchange

@app.route('/', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({"status": "online", "message": "TradingView Bridge is running"}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main endpoint to receive TradingView alerts.
    Expected JSON Payload in TradingView Alert Message:
    {
        "passphrase": "YOUR_SECRET_PASSPHRASE",
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "side": "buy",
        "type": "limit",
        "amount": 0.001,
        "price": 50000
    }
    """
    try:
        # 1. Parse Data
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Empty payload"}), 400

        # 2. Security Check
        configured_passphrase = app.config.get('WEBHOOK_PASSPHRASE')
        if configured_passphrase and data.get('passphrase') != configured_passphrase:
            logger.warning("Unauthorized access attempt (Invalid Passphrase)")
            return jsonify({"error": "Unauthorized"}), 401

        # 3. Extract Trade Parameters
        exchange_id = data.get('exchange', app.config.get('DEFAULT_EXCHANGE'))
        symbol = data.get('symbol')
        side = data.get('side', '').lower()  # buy or sell
        order_type = data.get('type', 'market').lower()
        amount = data.get('amount')
        price = data.get('price') # Optional for market orders

        # Basic Validation
        if not exchange_id or not symbol or not side or not amount:
            return jsonify({"error": "Missing required fields (exchange, symbol, side, amount)"}), 400

        # 4. Initialize Exchange
        # Note: In a high-traffic env, we would cache these instances
        api_key = app.config.get('EXCHANGE_API_KEY')
        api_secret = app.config.get('EXCHANGE_API_SECRET')
        
        if not api_key or not api_secret:
            return jsonify({"error": "Server API credentials not configured"}), 500

        exchange = get_exchange_instance(
            exchange_id, 
            api_key, 
            api_secret, 
            testnet=app.config.get('TESTNET')
        )

        # 5. Execute Order
        logger.info(f"Executing {side.upper()} {order_type} on {exchange_id} for {amount} {symbol}")
        
        order = None
        try:
            if order_type == 'limit':
                if not price:
                    return jsonify({"error": "Price required for limit orders"}), 400
                order = exchange.create_order(symbol, order_type, side, amount, price)
            elif order_type == 'market':
                order = exchange.create_order(symbol, order_type, side, amount)
            else:
                return jsonify({"error": "Unsupported order type. Use limit or market."}), 400
        except Exception as e:
            logger.error(f"Exchange Error: {str(e)}")
            return jsonify({"error": f"Exchange execution failed: {str(e)}"}), 500

        # 6. Success Response
        logger.info(f"Order Placed Successfully: {order.get('id')}")
        return jsonify({
            "message": "Order executed",
            "order_id": order.get('id'),
            "status": order.get('status')
        }), 200

    except Exception as e:
        logger.error(f"Internal Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TradingView to Crypto Exchange Bridge')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--key', type=str, required=True, help='Exchange API Key')
    parser.add_argument('--secret', type=str, required=True, help='Exchange API Secret')
    parser.add_argument('--passphrase', type=str, default='secret123', help='Security passphrase for Webhooks')
    parser.add_argument('--exchange', type=str, default='binance', help='Default Exchange ID (ccxt compatible)')
    parser.add_argument('--testnet', action='store_true', help='Use Exchange Testnet/Sandbox if available')
    
    args = parser.parse_args()

    # Store config in Flask app context
    app.config['EXCHANGE_API_KEY'] = args.key
    app.config['EXCHANGE_API_SECRET'] = args.secret
    app.config['WEBHOOK_PASSPHRASE'] = args.passphrase
    app.config['DEFAULT_EXCHANGE'] = args.exchange
    app.config['TESTNET'] = args.testnet

    print(f"\n🚀 TradingView Bridge Started on Port {args.port}")
    print(f"🔒 Webhook Passphrase: {args.passphrase}")
    print(f"🏦 Default Exchange: {args.exchange}")
    print(f"🧪 Testnet Mode: {args.testnet}\n")

    app.run(host='0.0.0.0', port=args.port)