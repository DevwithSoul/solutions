#aiwebarchitects
import argparse
import requests
import pandas as pd
import sys
import time
from datetime import datetime

class FundamentalScreener:
    """
    A class to fetch financial statements, clean data, and calculate fundamental metrics.
    Uses Financial Modeling Prep (FMP) API as the data source.
    """
    
    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key):
        self.api_key = api_key
        self.results = []

    def get_json_response(self, endpoint, ticker):
        """
        Helper method to perform GET requests to the API.
        """
        url = f"{self.BASE_URL}/{endpoint}/{ticker}?limit=1&apikey={self.api_key}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if not data:
                print(f"[WARN] No data found for {ticker} at endpoint {endpoint}")
                return None
            return data[0] # Return the most recent annual report
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API request failed for {ticker}: {e}")
            return None

    def analyze_ticker(self, ticker):
        """
        Fetches Income Statement and Balance Sheet to calculate ROIC and other metrics.
        """
        print(f"[INFO] Analyzing {ticker}...")
        
        # 1. Fetch Income Statement (for EBIT, Tax, Net Income)
        income_stmt = self.get_json_response("income-statement", ticker)
        if not income_stmt:
            return

        # 2. Fetch Balance Sheet (for Debt, Equity, Cash)
        balance_sheet = self.get_json_response("balance-sheet-statement", ticker)
        if not balance_sheet:
            return

        try:
            # -- Extract Raw Data --
            revenue = income_stmt.get('revenue', 0)
            net_income = income_stmt.get('netIncome', 0)
            operating_income = income_stmt.get('operatingIncome', 0)
            income_tax_expense = income_stmt.get('incomeTaxExpense', 0)
            income_before_tax = income_stmt.get('incomeBeforeTax', 0)
            
            total_equity = balance_sheet.get('totalStockholdersEquity', 0)
            total_debt = balance_sheet.get('totalDebt', 0)
            cash_and_equivalents = balance_sheet.get('cashAndCashEquivalents', 0)

            # -- Calculate Custom Metrics --
            
            # 1. Effective Tax Rate
            # Avoid division by zero
            tax_rate = (income_tax_expense / income_before_tax) if income_before_tax != 0 else 0.21
            
            # 2. NOPAT (Net Operating Profit After Tax)
            nopat = operating_income * (1 - tax_rate)
            
            # 3. Invested Capital (Simplified: Equity + Debt - Cash)
            invested_capital = total_equity + total_debt - cash_and_equivalents
            
            # 4. ROIC (Return on Invested Capital)
            roic = (nopat / invested_capital * 100) if invested_capital != 0 else 0.0

            # 5. Net Profit Margin
            net_margin = (net_income / revenue * 100) if revenue != 0 else 0.0

            # -- Store Result --
            self.results.append({
                'Ticker': ticker,
                'Date': income_stmt.get('date'),
                'Revenue ($B)': round(revenue / 1e9, 2),
                'Net Income ($B)': round(net_income / 1e9, 2),
                'Operating Income ($B)': round(operating_income / 1e9, 2),
                'Invested Capital ($B)': round(invested_capital / 1e9, 2),
                'ROIC (%)': round(roic, 2),
                'Net Margin (%)': round(net_margin, 2)
            })
            
        except Exception as e:
            print(f"[ERROR] Failed to calculate metrics for {ticker}: {e}")

    def save_to_csv(self, filename="screener_results.csv"):
        """
        Exports the aggregated data to a CSV file.
        """
        if not self.results:
            print("[WARN] No results to save.")
            return
        
        df = pd.DataFrame(self.results)
        
        # Sort by ROIC descending to highlight best quality companies
        df = df.sort_values(by='ROIC (%)', ascending=False)
        
        df.to_csv(filename, index=False)
        print(f"\n[SUCCESS] Analysis complete. Results saved to '{filename}'")
        print(df.to_string(index=False))

    def run(self, tickers):
        """
        Main execution loop.
        """
        for ticker in tickers:
            self.analyze_ticker(ticker.upper())
            # Sleep briefly to respect API rate limits (mostly for free tiers)
            time.sleep(0.25) 
        
        self.save_to_csv()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Fundamental Stock Screener")
    
    parser.add_argument(
        '--api-key',
        type=str,
        required=True,
        help="Your Financial Modeling Prep (FMP) API Key"
    )
    
    parser.add_argument(
        '--tickers',
        type=str,
        required=True,
        help="Comma-separated list of stock tickers (e.g., AAPL,MSFT,GOOGL)"
    )

    args = parser.parse_args()

    # Parse ticker string into list
    ticker_list = [t.strip() for t in args.tickers.split(',')]

    screener = FundamentalScreener(args.api_key)
    screener.run(ticker_list)
