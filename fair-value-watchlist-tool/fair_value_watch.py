#aiwebarchitects
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time
import sys

# ==========================================
# CONFIGURATION
# ==========================================
# List of tickers to monitor
TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
    "JPM", "JNJ", "PG", "KO", "NVDA", "INTC"
]

# Margin of Safety (0.20 = 20% discount required to buy)
MARGIN_OF_SAFETY = 0.20

# Output filename format
OUTPUT_FILENAME = f"fair_value_report_{datetime.now().strftime('%Y-%m-%d')}.csv"

def get_financial_metrics(ticker_symbol):
    """
    Fetches raw financial data from Yahoo Finance via yfinance.
    Returns a dictionary of metrics or None if data is unavailable.
    """
    try:
        print(f"Fetching data for {ticker_symbol}...")
        stock = yf.Ticker(ticker_symbol)
        info = stock.info

        # Extract necessary data points with fallbacks
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        trailing_eps = info.get('trailingEps', 0)
        book_value = info.get('bookValue', 0)
        target_mean_price = info.get('targetMeanPrice', 0) # Analyst consensus
        sector = info.get('sector', 'Unknown')
        
        # Return structured data
        return {
            "symbol": ticker_symbol,
            "sector": sector,
            "current_price": current_price,
            "eps": trailing_eps,
            "book_value": book_value,
            "analyst_target": target_mean_price
        }
    except Exception as e:
        print(f"Error fetching {ticker_symbol}: {e}")
        return None

def calculate_intrinsic_value(metrics):
    """
    Applies valuation formulas to determine Fair Value.
    
    Strategy 1: Graham Number (Classic Value Investing)
    Formula: Sqrt(22.5 * EPS * Book Value)
    Note: Only works if EPS and Book Value are positive.
    
    Strategy 2: Analyst Consensus
    Uses the mean target price set by professional analysts.
    """
    if not metrics:
        return None

    # 1. Calculate Graham Number
    eps = metrics['eps']
    bv = metrics['book_value']
    
    graham_number = 0
    if eps > 0 and bv > 0:
        graham_number = np.sqrt(22.5 * eps * bv)
    
    # 2. Use Analyst Target as a secondary proxy for growth stocks
    analyst_target = metrics['analyst_target']
    
    # Determine the 'Fair Value' to use for comparison
    # If Graham Number is valid (Value stock), use it. Otherwise fallback to Analyst Target.
    # This logic can be customized based on user preference.
    if graham_number > 0:
        fair_value = graham_number
        valuation_method = "Graham Number"
    elif analyst_target > 0:
        fair_value = analyst_target
        valuation_method = "Analyst Target"
    else:
        fair_value = 0
        valuation_method = "N/A"

    metrics['fair_value'] = round(fair_value, 2)
    metrics['valuation_method'] = valuation_method
    metrics['graham_number'] = round(graham_number, 2)
    
    return metrics

def analyze_buy_signal(metrics):
    """
    Compares Current Price to Fair Value with Margin of Safety.
    """
    if not metrics or metrics['fair_value'] == 0:
        metrics['buy_signal'] = "NO DATA"
        metrics['margin_gap'] = 0
        return metrics

    current_price = metrics['current_price']
    fair_value = metrics['fair_value']
    
    # Calculate the Buy Price threshold (Fair Value minus Margin of Safety)
    buy_threshold = fair_value * (1 - MARGIN_OF_SAFETY)
    
    # Calculate percentage difference
    if current_price > 0:
        diff_percent = ((fair_value - current_price) / current_price) * 100
    else:
        diff_percent = 0

    metrics['buy_threshold'] = round(buy_threshold, 2)
    metrics['potential_upside_%'] = round(diff_percent, 2)

    # Determine Signal
    if current_price < buy_threshold:
        metrics['buy_signal'] = "STRONG BUY"
    elif current_price < fair_value:
        metrics['buy_signal'] = "WATCH (Undervalued)"
    else:
        metrics['buy_signal'] = "HOLD/SELL (Overvalued)"
        
    return metrics

def main():
    print("--- Automated Fair Value Stock Watchlist --- #aiwebarchitects")
    print(f"Processing {len(TICKERS)} tickers...")
    
    results = []
    
    for ticker in TICKERS:
        # 1. Fetch Data
        raw_data = get_financial_metrics(ticker)
        
        if raw_data:
            # 2. Calculate Valuation
            valued_data = calculate_intrinsic_value(raw_data)
            
            # 3. Analyze Signal
            final_analysis = analyze_buy_signal(valued_data)
            
            results.append(final_analysis)
        
        # Be polite to the API
        time.sleep(0.5)
        
    # 4. Create DataFrame and Export
    if results:
        df = pd.DataFrame(results)
        
        # Reorder columns for readability
        cols = [
            "symbol", "buy_signal", "current_price", "fair_value", 
            "potential_upside_%", "valuation_method", "buy_threshold", 
            "graham_number", "analyst_target", "sector"
        ]
        df = df[cols]
        
        # Sort by highest upside potential
        df = df.sort_values(by="potential_upside_%", ascending=False)
        
        # Save to CSV
        try:
            df.to_csv(OUTPUT_FILENAME, index=False)
            print(f"\nSuccess! Report generated: {OUTPUT_FILENAME}")
            print("\nTop 3 Undervalued Picks:")
            print(df.head(3)[['symbol', 'buy_signal', 'potential_upside_%']].to_string(index=False))
        except PermissionError:
            print(f"\nError: Could not save to {OUTPUT_FILENAME}. Is the file open in Excel?")
    else:
        print("No data processing occurred.")

if __name__ == "__main__":
    main()