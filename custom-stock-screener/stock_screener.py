#aiwebarchitects
import argparse
import pandas as pd
import yfinance as yf
import sys
from datetime import datetime

def parse_arguments():
    """
    Parses command line arguments for the stock screener.
    """
    parser = argparse.ArgumentParser(description='Automated Custom Stock Screener')
    parser.add_argument('tickers', metavar='T', type=str, nargs='+',
                        help='List of stock tickers to screen (e.g., AAPL MSFT TSLA)')
    parser.add_argument('--output', type=str, default='screener_results.csv',
                        help='Output CSV filename (default: screener_results.csv)')
    return parser.parse_args()

def fetch_stock_data(ticker):
    """
    Fetches fundamental data for a single ticker using yfinance.
    Returns a dictionary of raw metrics or None if failed.
    """
    try:
        print(f"Fetching data for: {ticker}...")
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # We return a dictionary with keys mapping to standard financial metrics
        # Using .get() handles cases where data might be missing for a specific company
        return {
            'Ticker': ticker.upper(),
            'Price': info.get('currentPrice'),
            'Market Cap': info.get('marketCap'),
            'PE Ratio': info.get('trailingPE'),
            'Forward PE': info.get('forwardPE'),
            'PEG Ratio': info.get('pegRatio'),
            'Price to Book': info.get('priceToBook'),
            'Debt to Equity': info.get('debtToEquity'),
            'Free Cash Flow': info.get('freeCashflow'),
            'Revenue Growth': info.get('revenueGrowth'),
            'Sector': info.get('sector'),
            'Industry': info.get('industry')
        }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def calculate_custom_metrics(df):
    """
    Applies custom logic to calculate bespoke valuation metrics.
    This mimics the 'programmable' aspect of the problem description.
    """
    if df.empty:
        return df

    # Example Custom Metric 1: Value Score
    # Simple logic: Higher score is better. penalize high PE, reward revenue growth.
    # This is a demonstration of logic injection.
    def value_score(row):
        score = 0
        # PE Check
        if pd.notnull(row['PE Ratio']):
            if row['PE Ratio'] < 15: score += 2
            elif row['PE Ratio'] < 25: score += 1
        
        # Growth Check
        if pd.notnull(row['Revenue Growth']):
            if row['Revenue Growth'] > 0.20: score += 2
            elif row['Revenue Growth'] > 0.10: score += 1
            
        # Debt Check
        if pd.notnull(row['Debt to Equity']):
             if row['Debt to Equity'] < 50: score += 1
             
        return score

    print("Calculating custom valuation metrics...")
    df['Custom Value Score'] = df.apply(value_score, axis=1)
    
    # Example Custom Metric 2: Enterprise Value approximation (simplified)
    # Note: yfinance usually provides EV, but calculating it manually demonstrates capability.
    # EV = Market Cap + Total Debt - Cash (Not fully available in this simple view, but we can manipulate columns)
    
    return df

def main():
    args = parse_arguments()
    
    results = []
    
    # Iterate through provided tickers
    for ticker in args.tickers:
        data = fetch_stock_data(ticker)
        if data:
            results.append(data)
    
    if not results:
        print("No data found for provided tickers.")
        sys.exit(1)
        
    # Convert to DataFrame for manipulation
    df = pd.DataFrame(results)
    
    # Apply custom logic
    df_enriched = calculate_custom_metrics(df)
    
    # Sort by Custom Value Score descending
    df_final = df_enriched.sort_values(by='Custom Value Score', ascending=False)
    
    # Export results
    try:
        df_final.to_csv(args.output, index=False)
        print(f"\nSuccess! Analysis saved to '{args.output}'")
        print("\nTop 3 Picks based on Custom Value Score:")
        print(df_final[['Ticker', 'Price', 'PE Ratio', 'Custom Value Score']].head(3).to_string(index=False))
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    main()