#aiwebarchitects

import requests
import argparse
from datetime import datetime, timedelta
import json


def get_stock_price(ticker, api_key):
    """Get last trading day's closing price for a stock"""
    for i in range(5):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        url = f"https://api.polygon.io/v1/open-close/{ticker}/{date}?adjusted=true&apiKey={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                return data['close']
        elif response.status_code != 404:
            raise Exception(f"API error: {response.status_code} - {response.text}")
    
    raise Exception("Could not retrieve stock price for last 5 days")


def get_nearest_expiration(ticker, api_key):
    """Get nearest options expiration date"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api.polygon.io/v1/options/contracts/{ticker}?expiration_date.gte={today}&limit=1&apiKey={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['expiration_date']
    
    raise Exception("No option contracts found")


def get_option_chain(ticker, expiration, api_key):
    """Get option chain for specific expiration date"""
    url = f"https://api.polygon.io/v1/options/contracts/{ticker}?expiration_date={expiration}&apiKey={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data['results']
    
    raise Exception(f"Error fetching option chain: {response.status_code}")


def get_atm_strike(stock_price, option_chain):
    """Find ATM strike price from option chain"""
    call_options = [opt for opt in option_chain if opt['contract_type'] == 'call']
    if not call_options:
        raise Exception("No call options found")
    
    closest_strike = min(call_options, key=lambda x: abs(x['strike_price'] - stock_price))
    return closest_strike['strike_price']


def get_option_iv(ticker, expiration, strike, api_key):
    """Get IV for specific option contract"""
    url = f"https://api.polygon.io/v2/reference/stocks/{ticker}/iv?contract_type=call&expiration_date={expiration}&strike_price={strike}&apiKey={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        return data['results']['implied_volatility']
    
    raise Exception(f"Error fetching IV: {response.status_code}")


def main():
    parser = argparse.ArgumentParser(description='IV Monitor for Options')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('--threshold-low', type=float, required=True, help='Low IV threshold')
    parser.add_argument('--threshold-high', type=float, required=True, help='High IV threshold')
    parser.add_argument('--api-key', type=str, required=True, help='Polygon.io API key')
    args = parser.parse_args()

    try:
        # Get stock price
        stock_price = get_stock_price(args.ticker, args.api_key)
        print(f"Current stock price: ${stock_price:.2f}")
        
        # Get nearest expiration
        expiration = get_nearest_expiration(args.ticker, args.api_key)
        print(f"Nearest expiration: {expiration}")
        
        # Get option chain
        option_chain = get_option_chain(args.ticker, expiration, args.api_key)
        
        # Get ATM strike
        atm_strike = get_atm_strike(stock_price, option_chain)
        print(f"ATM strike: ${atm_strike}")
        
        # Get option IV
        iv = get_option_iv(args.ticker, expiration, atm_strike, args.api_key)
        print(f"Current IV: {iv:.4f}")
        
        # Check thresholds
        if iv < args.threshold_low:
            print(f"ALERT: IV below threshold ({args.threshold_low}) - Consider selling premium")
        if iv > args.threshold_high:
            print(f"ALERT: IV above threshold ({args.threshold_high}) - Consider buying premium")
            
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()