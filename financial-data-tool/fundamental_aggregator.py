#aiwebarchitects
import argparse
import sys
import pandas as pd
import yfinance as yf
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_roic(ticker_obj):
    """
    Calculates Return on Invested Capital (ROIC) manually based on financial statements.
    Formula: NOPAT / Invested Capital
    NOPAT = EBIT * (1 - Effective Tax Rate)
    Invested Capital = Total Equity + Total Debt - Cash & Equivalents
    """
    try:
        # Fetch annual financials and balance sheet
        financials = ticker_obj.financials
        balance_sheet = ticker_obj.balance_sheet

        if financials.empty or balance_sheet.empty:
            return None

        # We use the most recent year (column 0)
        # Note: Keys in yfinance can vary slightly, using standard keys usually found
        
        # 1. Get EBIT
        # Try 'EBIT' or 'Net Income' + 'Interest Expense' + 'Tax Provision' if EBIT missing
        if 'EBIT' in financials.index:
            ebit = financials.loc['EBIT'].iloc[0]
        elif 'Operating Income' in financials.index:
             ebit = financials.loc['Operating Income'].iloc[0]
        else:
            return None

        # 2. Calculate Effective Tax Rate
        # Tax Rate = Tax Provision / Pretax Income
        try:
            tax_provision = financials.loc['Tax Provision'].iloc[0]
            pretax_income = financials.loc['Pretax Income'].iloc[0]
            tax_rate = tax_provision / pretax_income if pretax_income != 0 else 0.21 # Fallback to standard corp rate
        except KeyError:
            tax_rate = 0.21 # Assumption if data missing

        nopat = ebit * (1 - tax_rate)

        # 3. Calculate Invested Capital
        # Invested Capital = (Total Assets - Current Liabilities) + Short Term Debt - Cash ?? 
        # Simpler definition: Total Debt + Total Equity - Cash
        try:
            total_equity = balance_sheet.loc['Stockholders Equity'].iloc[0]
            
            # Total Debt might be split
            total_debt = 0
            if 'Total Debt' in balance_sheet.index:
                 total_debt = balance_sheet.loc['Total Debt'].iloc[0]
            elif 'Long Term Debt' in balance_sheet.index:
                 total_debt = balance_sheet.loc['Long Term Debt'].iloc[0]
            
            cash = 0
            if 'Cash And Cash Equivalents' in balance_sheet.index:
                cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
            
            invested_capital = total_equity + total_debt - cash
        except KeyError:
            return None

        if invested_capital == 0:
            return None

        roic = (nopat / invested_capital) * 100 # Return as percentage
        return round(roic, 2)

    except Exception as e:
        logger.debug(f"Could not calculate ROIC: {e}")
        return None

def fetch_fundamental_data(tickers):
    """
    Iterates through a list of tickers and aggregates fundamental data.
    """
    results = []
    
    logger.info(f"Processing {len(tickers)} tickers...")
    
    for symbol in tickers:
        symbol = symbol.strip().upper()
        if not symbol:
            continue
            
        try:
            logger.info(f"Fetching data for: {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract metrics directly from Info (if available)
            current_price = info.get('currentPrice')
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            
            # EV / EBITDA is usually calculated by Yahoo
            ev_ebitda = info.get('enterpriseToEbitda')
            
            # PE Ratio
            pe_ratio = info.get('trailingPE')
            
            # Calculate ROIC manually as it's often missing in 'info'
            roic = calculate_roic(ticker)
            
            data_point = {
                'Ticker': symbol,
                'Price': current_price,
                'Sector': sector,
                'Industry': industry,
                'EV/EBITDA': round(ev_ebitda, 2) if ev_ebitda else None,
                'ROIC (%)': roic,
                'P/E Ratio': round(pe_ratio, 2) if pe_ratio else None,
                'Market Cap': info.get('marketCap'),
                'Beta': info.get('beta')
            }
            results.append(data_point)
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")
            
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Automated Fundamental Data Aggregator")
    
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='List of stock tickers (e.g., AAPL MSFT GOOG)'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='Path to a text file containing tickers (one per line)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='fundamental_analysis.csv',
        help='Output CSV filename (default: fundamental_analysis.csv)'
    )

    args = parser.parse_args()

    # Validate input
    ticker_list = []
    if args.tickers:
        ticker_list.extend(args.tickers)
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                lines = f.readlines()
                ticker_list.extend([line.strip() for line in lines if line.strip()])
        except FileNotFoundError:
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
            
    if not ticker_list:
        logger.error("No tickers provided. Use --tickers or --file.")
        parser.print_help()
        sys.exit(1)

    # Remove duplicates
    ticker_list = list(set(ticker_list))

    # Fetch Data
    df = fetch_fundamental_data(ticker_list)

    if not df.empty:
        # Display to console
        print("\n--- Analysis Results ---")
        print(df.to_string(index=False))
        
        # Save to CSV
        df.to_csv(args.output, index=False)
        logger.info(f"\nData saved successfully to {args.output}")
    else:
        logger.warning("No data retrieved.")

if __name__ == "__main__":
    main()