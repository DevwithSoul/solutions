#aiwebarchitects
import argparse
import pandas as pd
import yfinance as yf
import sys
import os
from datetime import datetime

def validate_csv(df):
    """
    Validates that the input CSV has the required columns.
    """
    required_columns = ['Symbol', 'Quantity', 'TargetPercent']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: CSV must contain columns: {required_columns}")
        sys.exit(1)
    
    # Normalize TargetPercent if user utilized 0-1 instead of 0-100
    if df['TargetPercent'].sum() <= 1.05 and df['TargetPercent'].sum() >= 0.95:
        print("Detected decimal allocation (0.0-1.0). Converting to percentage.")
        df['TargetPercent'] = df['TargetPercent'] * 100
        
    total_allocation = df['TargetPercent'].sum()
    if not (99.0 <= total_allocation <= 101.0):
        print(f"Warning: Total target allocation is {total_allocation:.2f}%. It should be close to 100%.")

    return df

def fetch_market_data(symbols):
    """
    Fetches current market prices using yfinance.
    Returns a dictionary {Symbol: Price}.
    """
    print(f"Fetching market data for: {', '.join(symbols)}...")
    prices = {}
    
    try:
        # yfinance allows downloading multiple tickers at once
        tickers_str = " ".join(symbols)
        data = yf.download(tickers_str, period="1d", progress=False)
        
        # Handle single ticker vs multiple ticker structure in yfinance
        if len(symbols) == 1:
            # For single ticker, data['Close'] is a Series, take the last value
            last_price = data['Close'].iloc[-1].item()
            prices[symbols[0]] = last_price
        else:
            # For multiple tickers, data['Close'] is a DataFrame
            current_prices = data['Close'].iloc[-1]
            for symbol in symbols:
                # Handle cases where data might be NaN (delisted, wrong symbol)
                price = current_prices.get(symbol)
                if pd.isna(price):
                    print(f"Warning: Could not fetch price for {symbol}. Assuming $0.00 for calculation.")
                    prices[symbol] = 0.0
                else:
                    prices[symbol] = price
                    
    except Exception as e:
        print(f"Error fetching market data: {e}")
        sys.exit(1)
        
    return prices

def calculate_rebalancing(df, cash_injection=0.0):
    """
    Performs the core rebalancing logic.
    """
    # 1. Calculate Current Market Value per position
    unique_symbols = df['Symbol'].unique().tolist()
    price_map = fetch_market_data(unique_symbols)
    df['CurrentPrice'] = df['Symbol'].map(price_map)
    
    df['CurrentValue'] = df['Quantity'] * df['CurrentPrice']
    
    # 2. Calculate Portfolio Totals
    total_current_value = df['CurrentValue'].sum()
    total_projected_value = total_current_value + cash_injection
    
    print(f"\n--- Portfolio Summary ---")
    print(f"Current Value: ${total_current_value:,.2f}")
    print(f"Cash Injection: ${cash_injection:,.2f}")
    print(f"Projected Value: ${total_projected_value:,.2f}")
    
    # 3. Calculate Targets
    # Target Value = (TargetPercent / 100) * Total Projected Value
    df['TargetValue'] = (df['TargetPercent'] / 100) * total_projected_value
    
    # 4. Calculate Difference (Drift)
    # Positive means Buy, Negative means Sell
    df['DifferenceValue'] = df['TargetValue'] - df['CurrentValue']
    
    # 5. Calculate Shares to Trade
    # Shares = Difference / Price
    df['SharesToTrade'] = df.apply(
        lambda row: row['DifferenceValue'] / row['CurrentPrice'] if row['CurrentPrice'] > 0 else 0, 
        axis=1
    )
    
    return df

def generate_report(df, output_file=None):
    """
    Formats and prints the rebalancing plan.
    """
    print("\n--- Rebalancing Plan ---")
    
    # Formatting for display
    display_df = df.copy()
    display_df['Action'] = display_df['SharesToTrade'].apply(lambda x: "BUY" if x > 0 else "SELL")
    display_df['TradeShares'] = display_df['SharesToTrade'].abs().round(2)
    display_df['TradeAmount'] = display_df['DifferenceValue'].abs()
    
    # Filter out negligible trades (less than $1)
    trades = display_df[display_df['TradeAmount'] > 1.0].sort_values(by='TradeAmount', ascending=False)
    
    if trades.empty:
        print("Portfolio is balanced. No significant trades needed.")
    else:
        print(f"{'ACTION':<6} | {'SYMBOL':<6} | {'SHARES':<10} | {'EST. AMOUNT':<12}")
        print("-" * 45)
        for index, row in trades.iterrows():
            print(f"{row['Action']:<6} | {row['Symbol']:<6} | {row['TradeShares']:<10.2f} | ${row['TradeAmount']:<12,.2f}")
            
    if output_file:
        df.to_csv(output_file, index=False)
        print(f"\nDetailed analysis saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Privacy-First Portfolio Rebalancer")
    parser.add_argument('input_csv', help="Path to CSV file containing portfolio (Symbol, Quantity, TargetPercent)")
    parser.add_argument('--cash', type=float, default=0.0, help="Amount of new cash to invest (default: 0)")
    parser.add_argument('--output', help="Path to save the result CSV")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_csv):
        print(f"Error: File {args.input_csv} not found.")
        sys.exit(1)
        
    try:
        print("Loading portfolio...")
        df = pd.read_csv(args.input_csv)
        df = validate_csv(df)
        
        result_df = calculate_rebalancing(df, args.cash)
        generate_report(result_df, args.output)
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()