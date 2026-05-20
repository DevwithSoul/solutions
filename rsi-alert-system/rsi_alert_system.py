#aiwebarchitects
"""
Automated Multi-Ticker RSI Alert System
Scans multiple tickers for RSI signals and sends Discord notifications.
"""

import argparse
import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime

# RSI Calculation Function
def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI) for a series of prices.
    RSI = 100 - (100 / (1 + RS))
    where RS = Average Gain / Average Loss
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to fetch data for a single ticker with error handling
def fetch_ticker_data(ticker, interval='5m', period='2d'):
    """
    Fetch OHLCV data for a single ticker.
    interval: 5m for 5-minute candles
    period: 2d for 2 days of data
    """
    try:
        data = yf.download(ticker, interval=interval, period=period, progress=False)
        if data.empty:
            return None
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

# Function to check RSI conditions and generate alerts
def check_rsi_alerts(data, ticker, rsi_period=14, overbought=70, oversold=30):
    """
    Calculate RSI and check if it meets alert conditions.
    Returns alert information if conditions are met.
    """
    # Calculate RSI
    data['RSI'] = calculate_rsi(data['Close'], rsi_period)
    
    # Get current RSI value
    current_rsi = data['RSI'].iloc[-1]
    previous_rsi = data['RSI'].iloc[-2] if len(data) > 1 else current_rsi
    
    alerts = []
    
    # Check for overbought condition
    if current_rsi > overbought:
        alerts.append({
            'ticker': ticker,
            'rsi': current_rsi,
            'type': 'OVERBOUGHT',
            'message': f"🔴 RSI Alert: {ticker} is OVERBOUGHT (RSI: {current_rsi:.2f})"
        })
    
    # Check for oversold condition
    elif current_rsi < oversold:
        alerts.append({
            'ticker': ticker,
            'rsi': current_rsi,
            'type': 'OVERSOLD',
            'message': f"🟢 RSI Alert: {ticker} is OVERSOLD (RSI: {current_rsi:.2f})"
        })
    
    # Check for RSI crossover (bullish/bearish)
    if previous_rsi < oversold and current_rsi >= oversold:
        alerts.append({
            'ticker': ticker,
            'rsi': current_rsi,
            'type': 'RSI_CROSSED_UP',
            'message': f"📈 RSI Alert: {ticker} RSI crossed above oversold (RSI: {current_rsi:.2f})"
        })
    elif previous_rsi > overbought and current_rsi <= overbought:
        alerts.append({
            'ticker': ticker,
            'rsi': current_rsi,
            'type': 'RSI_CROSSED_DOWN',
            'message': f"📉 RSI Alert: {ticker} RSI crossed below overbought (RSI: {current_rsi:.2f})"
        })
    
    return alerts, data

# Function to send Discord notification
def send_discord_alert(webhook_url, alert, ticker_data=None):
    """
    Send a formatted Discord notification via webhook.
    """
    try:
        # Format the message
        embed = {
            "embeds": [
                {
                    "title": f"RSI Alert - {alert['ticker']}",
                    "description": alert['message'],
                    "color": 16711680 if alert['type'] == 'OVERBOUGHT' else 65280,
                    "fields": [
                        {
                            "name": "RSI Value",
                            "value": f"{alert['rsi']:.2f}",
                            "inline": True
                        },
                        {
                            "name": "Alert Type",
                            "value": alert['type'],
                            "inline": True
                        },
                        {
                            "name": "Timeframe",
                            "value": "5-minute",
                            "inline": True
                        }
                    ],
                    "timestamp": datetime.utcnow().isoformat(),
                    "footer": {
                        "text": "RSI Alert System"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=embed)
        if response.status_code == 204:
            print(f"✅ Alert sent for {alert['ticker']}")
        else:
            print(f"❌ Failed to send alert: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error sending Discord alert: {e}")

# Main scanning function
def scan_tickers(tickers, discord_webhook, rsi_period=14, overbought=70, oversold=30, scan_interval=300):
    """
    Main scanning loop.
    - Fetches data for all tickers
    - Checks RSI conditions
    - Sends Discord alerts
    - Respects rate limits with delays
    """
    print(f"🚀 Starting RSI Scanner...")
    print(f"📊 Monitoring {len(tickers)} tickers")
    print(f"⏱️  Scan interval: {scan_interval} seconds")
    print(f"📈 RSI Period: {rsi_period}")
    print(f"🔴 Overbought: {overbought}")
    print(f"🟢 Oversold: {oversold}")
    print("-" * 50)
    
    while True:
        print(f"\n📅 Scan at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        for i, ticker in enumerate(tickers):
            print(f"  Fetching {ticker}...", end=" ")
            
            # Fetch data with rate limiting
            data = fetch_ticker_data(ticker, interval='5m', period='2d')
            
            if data is None or data.empty:
                print("⚠️  No data")
                continue
            
            # Check RSI alerts
            alerts, _ = check_rsi_alerts(data, ticker, rsi_period, overbought, oversold)
            
            # Send alerts
            for alert in alerts:
                print(f"🔔 Alert: {alert['type']}")
                send_discord_alert(discord_webhook, alert)
            
            if not alerts:
                print("✅ No alerts")
            
            # Rate limiting delay between tickers
            if i < len(tickers) - 1:
                time.sleep(1)
        
        print(f"\n⏳ Waiting {scan_interval} seconds until next scan...")
        time.sleep(scan_interval)

# Example usage and main function
def main():
    parser = argparse.ArgumentParser(
        description='Automated Multi-Ticker RSI Alert System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python rsi_alert_system.py --tickers AAPL,GOOGL,MSFT,TSLA --webhook YOUR_DISCORD_WEBHOOK_URL
  python rsi_alert_system.py --tickers AAPL,GOOGL --webhook https://discord.com/api/webhooks/xxx/yyy --period 14 --overbought 70 --oversold 30 --interval 300
        """
    )
    
    parser.add_argument(
        '--tickers',
        required=True,
        help='Comma-separated list of ticker symbols (e.g., AAPL,GOOGL,MSFT)'
    )
    parser.add_argument(
        '--webhook',
        required=True,
        help='Discord webhook URL (create in Discord server > Integrations > Webhooks)'
    )
    parser.add_argument(
        '--period',
        type=int,
        default=14,
        help='RSI calculation period (default: 14)'
    )
    parser.add_argument(
        '--overbought',
        type=int,
        default=70,
        help='Overbought threshold (default: 70)'
    )
    parser.add_argument(
        '--oversold',
        type=int,
        default=30,
        help='Oversold threshold (default: 30)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Scan interval in seconds (default: 300)'
    )
    
    args = parser.parse_args()
    
    # Parse tickers
    tickers = [t.strip().upper() for t in args.tickers.split(',')]
    
    # Start scanning
    scan_tickers(
        tickers=tickers,
        discord_webhook=args.webhook,
        rsi_period=args.period,
        overbought=args.overbought,
        oversold=args.oversold,
        scan_interval=args.interval
    )

if __name__ == "__main__":
    main()
