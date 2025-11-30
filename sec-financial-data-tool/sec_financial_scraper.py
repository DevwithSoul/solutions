#aiwebarchitects
import requests
import json
import pandas as pd
import argparse
import sys
import time
from datetime import datetime

# Constants for SEC EDGAR API
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

class SECFinancialScraper:
    def __init__(self, user_email):
        """
        Initialize the scraper with the required User-Agent header.
        The SEC requires a User-Agent in the format: 'AppName ContactEmail'
        """
        self.headers = {
            "User-Agent": f"FinancialDataScraper {user_email}",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        }
        self.ticker_map = {}

    def load_tickers(self):
        """
        Fetches the mapping of Ticker symbols to CIK numbers from the SEC.
        """
        print("Fetching ticker mapping from SEC...")
        try:
            # Note: Tickers endpoint is on www.sec.gov, not data.sec.gov
            response = requests.get(SEC_TICKERS_URL, headers={"User-Agent": self.headers["User-Agent"]})
            response.raise_for_status()
            data = response.json()
            
            # Convert dictionary of dictionaries to a simple Ticker -> CIK map
            # The SEC format is { "0": {"cik_str": 320193, "ticker": "AAPL", ...}, ... }
            for entry in data.values():
                self.ticker_map[entry['ticker'].upper()] = str(entry['cik_str']).zfill(10)
            
            print(f"Loaded {len(self.ticker_map)} tickers.")
        except Exception as e:
            print(f"Error fetching tickers: {e}")
            sys.exit(1)

    def get_cik(self, ticker):
        """
        Returns the 10-digit CIK string for a given ticker.
        """
        ticker = ticker.upper()
        if not self.ticker_map:
            self.load_tickers()
        return self.ticker_map.get(ticker)

    def fetch_company_facts(self, ticker):
        """
        Fetches the full XBRL company facts JSON for a specific ticker.
        """
        cik = self.get_cik(ticker)
        if not cik:
            print(f"Error: Ticker {ticker} not found in SEC database.")
            return None

        url = SEC_FACTS_URL.format(cik=cik)
        print(f"Fetching financial data for {ticker} (CIK: {cik})...")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Error: No data found for {ticker}. The company may not report using XBRL.")
            elif e.response.status_code == 403:
                print("Error: Access forbidden. Check your User-Agent email.")
            else:
                print(f"HTTP Error: {e}")
            return None
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def extract_financial_metrics(self, data, concepts):
        """
        Parses the raw JSON to extract specific US-GAAP concepts into a DataFrame.
        
        Args:
            data (dict): Raw JSON from SEC.
            concepts (list): List of US-GAAP concept names (e.g., 'Assets', 'NetIncomeLoss').
        """
        if not data or 'facts' not in data or 'us-gaap' not in data['facts']:
            print("Invalid data structure or no US-GAAP data available.")
            return pd.DataFrame()

        all_records = []
        us_gaap_data = data['facts']['us-gaap']

        for concept in concepts:
            if concept in us_gaap_data:
                # The data is usually stored under units, e.g., 'USD' or 'USD/shares'
                # We iterate through all unit types found
                for unit_key, records in us_gaap_data[concept]['units'].items():
                    for record in records:
                        # We only care about 10-K (Annual) and 10-Q (Quarterly) usually
                        form = record.get('form', 'Unknown')
                        if form in ['10-K', '10-Q']:
                            row = {
                                'Concept': concept,
                                'Form': form,
                                'Frame': record.get('frame', ''), # Often contains CY2023, etc.
                                'End Date': record.get('end'),
                                'Value': record.get('val'),
                                'Unit': unit_key,
                                'Filing Date': record.get('filed')
                            }
                            all_records.append(row)
            else:
                print(f"Warning: Concept '{concept}' not found for this company.")

        df = pd.DataFrame(all_records)
        if not df.empty:
            # Sort by date for cleaner output
            df['End Date'] = pd.to_datetime(df['End Date'])
            df = df.sort_values(by=['Concept', 'End Date'], ascending=[True, False])
        
        return df

def main():
    parser = argparse.ArgumentParser(description="SEC Financial Data Scraper (XBRL/JSON)")
    parser.add_argument("--ticker", type=str, required=True, help="Stock Ticker Symbol (e.g., AAPL, TSLA)")
    parser.add_argument("--email", type=str, required=True, help="Your email address for SEC User-Agent compliance")
    parser.add_argument("--output", type=str, default="financial_data.csv", help="Output CSV filename")
    
    args = parser.parse_args()

    # 1. Initialize Scraper
    scraper = SECFinancialScraper(args.email)

    # 2. Fetch Data
    raw_data = scraper.fetch_company_facts(args.ticker)

    if raw_data:
        # 3. Define metrics to extract
        # These are standard US-GAAP tags. 
        # 'Assets': Total Assets
        # 'StockholdersEquity': Equity
        # 'Revenues': Revenue
        # 'NetIncomeLoss': Net Income
        target_concepts = [
            'Assets', 
            'StockholdersEquity', 
            'Revenues', 
            'NetIncomeLoss', 
            'OperatingIncomeLoss'
        ]

        print(f"Extracting metrics: {', '.join(target_concepts)}...")
        df = scraper.extract_financial_metrics(raw_data, target_concepts)

        if not df.empty:
            # 4. Save to CSV
            print(f"Success! Extracted {len(df)} records.")
            df.to_csv(args.output, index=False)
            print(f"Data saved to {args.output}")
            
            # Preview
            print("\nLatest 5 records:")
            print(df.head().to_string())
        else:
            print("No matching financial records found in the extracted data.")
    else:
        print("Failed to retrieve data.")

if __name__ == "__main__":
    main()