#aiwebarchitects
"""
Automated Dividend Income Tracker

This script fetches financial data for a list of stock tickers using the Yahoo Finance API.
It retrieves the Ex-Dividend Date, Dividend Rate, Yield, and Payment Date (if available).
The output is saved to a CSV file, which can be easily imported into Excel or Google Sheets.

Usage:
    python dividend_tracker.py --tickers AAPL MSFT KO O --output my_dividends.csv
    python dividend_tracker.py --file portfolio.txt

Dependencies:
    pip install yfinance pandas
"""

import argparse
import sys
import os
from datetime import datetime
import pandas as pd
import yfinance as yf

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='Fetch dividend data for stock tickers.')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--tickers', nargs='+', help='List of stock tickers (e.g., AAPL MSFT)')
    group.add_argument('--file', type=str, help='Path to a text file containing tickers (one per line)')
    
    parser.add_argument('--output', type=str, default='dividend_report.csv', help='Output CSV filename')
    
    return parser.parse_args()

def get_tickers_from_file(filepath):
    """
    Read tickers from a text file.
    """
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
        
    with open(filepath, 'r') as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
    return tickers

def format_timestamp(ts):
    """
    Convert a Unix timestamp to a readable YYYY-MM-DD string.
    Returns 'N/A' if timestamp is None.
    """
    if not ts:
        return "N/A"
    try:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    except Exception:
        return "N/A"

def fetch_dividend_data(ticker_symbol):
    """
    Fetch dividend specific data for a single ticker.
    """
    print(f"Fetching data for: {ticker_symbol}...")
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # Extract relevant data with safe defaults
        # Note: 'exDividendDate' in yfinance info is usually a unix timestamp
        ex_div_date = format_timestamp(info.get('exDividendDate'))
        
        # Dividend Rate (Annual)
        div_rate = info.get('dividendRate', 0)
        
        # Dividend Yield (Percentage)
        div_yield = info.get('dividendYield', 0)
        if div_yield:
            div_yield = f"{div_yield * 100:.2f}%"
        else:
            div_yield = "0.00%"
            
        # Payout Ratio
        payout_ratio = info.get('payoutRatio', 0)
        if payout_ratio:
            payout_ratio = f"{payout_ratio * 100:.2f}%"
        else:
            payout_ratio = "N/A"

        # Last Dividend Value
        last_div = info.get('lastDividendValue', 'N/A')

        return {
            'Ticker': ticker_symbol,
            'Company Name': info.get('longName', ticker_symbol),
            'Current Price': info.get('currentPrice', 'N/A'),
            'Ex-Dividend Date': ex_div_date,
            'Annual Dividend Rate': div_rate,
            'Dividend Yield': div_yield,
            'Payout Ratio': payout_ratio,
            'Sector': info.get('sector', 'N/A'),
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
        return {
            'Ticker': ticker_symbol,
            'Company Name': 'Error Fetching Data',
            'Current Price': 'N/A',
            'Ex-Dividend Date': 'N/A',
            'Annual Dividend Rate': 'N/A',
            'Dividend Yield': 'N/A',
            'Payout Ratio': 'N/A',
            'Sector': 'N/A',
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

def main():
    args = parse_arguments()
    
    # Determine source of tickers
    if args.file:
        tickers = get_tickers_from_file(args.file)
    else:
        tickers = [t.upper() for t in args.tickers]
        
    if not tickers:
        print("No tickers provided. Exiting.")
        sys.exit(1)
        
    print(f"Processing {len(tickers)} tickers...")
    print("-" * 40)
    
    results = []
    for ticker in tickers:
        data = fetch_dividend_data(ticker)
        results.append(data)
        
    # Create DataFrame and Export
    if results:
        df = pd.DataFrame(results)
        
        # Reorder columns for better readability
        cols = ['Ticker', 'Company Name', 'Ex-Dividend Date', 'Annual Dividend Rate', 
                'Dividend Yield', 'Current Price', 'Payout Ratio', 'Sector', 'Last Updated']
        df = df[cols]
        
        try:
            df.to_csv(args.output, index=False)
            print("-" * 40)
            print(f"Success! Data saved to '{args.output}'")
            print("You can now open this file in Excel or Google Sheets.")
        except PermissionError:
            print(f"Error: Could not write to '{args.output}'. Is the file open in another program?")
    else:
        print("No data retrieved.")

if __name__ == "__main__":
    main()