#aiwebarchitects
import argparse
import pandas as pd
import yfinance as yf
import time
import sys
from datetime import datetime

def parse_arguments():
    """
    Parses command line arguments for the script.
    """
    parser = argparse.ArgumentParser(description='Automated Bulk Stock Financials Extractor')
    parser.add_argument('--tickers', type=str, help='Comma-separated list of stock tickers (e.g., AAPL,MSFT,GOOGL)', required=False)
    parser.add_argument('--file', type=str, help='Path to a text file containing tickers (one per line)', required=False)
    parser.add_argument('--output', type=str, default='financial_report.xlsx', help='Output Excel file name (default: financial_report.xlsx)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay in seconds between requests to avoid rate limiting (default: 0.5)')
    
    args = parser.parse_args()
    
    if not args.tickers and not args.file:
        print("Error: You must provide either --tickers or --file.")
        parser.print_help()
        sys.exit(1)
        
    return args

def get_tickers_list(args):
    """
    Normalizes input into a list of ticker strings.
    """
    tickers = []
    if args.tickers:
        # Split by comma, strip whitespace, and ensure uppercase
        tickers.extend([t.strip().upper() for t in args.tickers.split(',') if t.strip()])
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                lines = f.readlines()
                tickers.extend([line.strip().upper() for line in lines if line.strip()])
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
            
    # Remove duplicates
    return list(set(tickers))

def fetch_financials(ticker_symbol):
    """
    Fetches financial data for a single ticker using yfinance.
    Returns a dictionary of annual data points.
    """
    print(f"Processing: {ticker_symbol}...")
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Fetch statements
        # Note: yfinance returns DataFrames where columns are Dates and index are Metrics
        financials = stock.financials
        cashflow = stock.cashflow
        
        if financials.empty or cashflow.empty:
            print(f"  - Warning: No financial data found for {ticker_symbol}")
            return []

        data_extracted = []
        
        # Get common dates (columns)
        # We take the intersection of dates available in both statements to ensure alignment
        dates = financials.columns.intersection(cashflow.columns)
        
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            
            # Extract Revenue
            # yfinance keys can vary slightly, usually 'Total Revenue'
            revenue = None
            if 'Total Revenue' in financials.index:
                revenue = financials.loc['Total Revenue', date]
            elif 'Operating Revenue' in financials.index:
                 revenue = financials.loc['Operating Revenue', date]
            
            # Extract Free Cash Flow
            # yfinance often calculates this, or we can try (Operating Cash Flow - CapEx)
            fcf = None
            if 'Free Cash Flow' in cashflow.index:
                fcf = cashflow.loc['Free Cash Flow', date]
            elif 'Operating Cash Flow' in cashflow.index and 'Capital Expenditure' in cashflow.index:
                # Manual Calc fallback
                fcf = cashflow.loc['Operating Cash Flow', date] + cashflow.loc['Capital Expenditure', date] # CapEx is usually negative
            
            data_extracted.append({
                'Ticker': ticker_symbol,
                'Date': date_str,
                'Total Revenue': revenue,
                'Free Cash Flow': fcf
            })
            
        return data_extracted

    except Exception as e:
        print(f"  - Error fetching {ticker_symbol}: {e}")
        return []

def main():
    args = parse_arguments()
    tickers = get_tickers_list(args)
    
    print(f"Starting extraction for {len(tickers)} tickers.")
    print("="*50)
    
    all_data = []
    
    for ticker in tickers:
        stock_data = fetch_financials(ticker)
        if stock_data:
            all_data.extend(stock_data)
        
        # Polite delay
        time.sleep(args.delay)
        
    print("="*50)
    
    if not all_data:
        print("No data extracted. Exiting.")
        return

    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Sort by Ticker and Date (descending)
    df.sort_values(by=['Ticker', 'Date'], ascending=[True, False], inplace=True)
    
    # Format numbers for better readability in console (optional, Excel handles formatting differently)
    # We will export raw numbers to Excel for calculation purposes.
    
    print(f"Exporting data to {args.output}...")
    
    try:
        # Create a Summary Pivot (Latest Year)
        # We convert Date to datetime to find max easily
        df['DateObj'] = pd.to_datetime(df['Date'])
        latest_indices = df.groupby('Ticker')['DateObj'].idxmax()
        summary_df = df.loc[latest_indices].drop(columns=['DateObj'])
        
        with pd.ExcelWriter(args.output, engine='openpyxl') as writer:
            # Sheet 1: Detailed Data (All years fetched)
            df.drop(columns=['DateObj'], errors='ignore').to_excel(writer, sheet_name='Historical Data', index=False)
            
            # Sheet 2: Summary (Latest available year)
            summary_df.to_excel(writer, sheet_name='Latest Summary', index=False)
            
        print("Success! Extraction complete.")
        print(f"File saved: {args.output}")
        
    except PermissionError:
        print(f"Error: Could not write to {args.output}. Is the file open in Excel?")
    except Exception as e:
        print(f"Unexpected error during export: {e}")

if __name__ == "__main__":
    main()