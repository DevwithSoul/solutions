#aiwebarchitects
import requests
import pandas as pd
import argparse
import time
import sys
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION & CONSTANTS
# -----------------------------------------------------------------------------

# The SEC requires a User-Agent in the format: "Company Name email@example.com"
# We will enforce this via CLI arguments to comply with SEC fair access policies.
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"

# Metrics to fetch (US-GAAP Tags)
# Note: 'Revenues' is a common tag, but some modern companies use 
# 'RevenueFromContractWithCustomerExcludingAssessedTax'. We will try a simplified approach.
METRICS = {
    "Revenues": "Revenues",
    "NetIncome": "NetIncomeLoss"
}

def get_headers(email):
    """
    Constructs the headers required by SEC EDGAR.
    """
    return {
        "User-Agent": f"IndividualInvestor {email}",
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov"
    }

def get_cik_mapping(headers):
    """
    Fetches the mapping of Ticker symbols to CIK numbers from the SEC.
    """
    try:
        print("[*] Fetching Ticker-CIK mapping from SEC...")
        response = requests.get(SEC_TICKERS_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Transform dictionary of dictionaries into a dictionary: { 'AAPL': '0000320193' }
        ticker_to_cik = {}
        for entry in data.values():
            ticker = entry['ticker'].upper()
            # CIK must be 10 digits, padded with zeros
            cik = str(entry['cik_str']).zfill(10)
            ticker_to_cik[ticker] = cik
            
        return ticker_to_cik
    except Exception as e:
        print(f"[!] Error fetching CIK mapping: {e}")
        sys.exit(1)

def fetch_metric(cik, tag, headers):
    """
    Fetches all historical data for a specific US-GAAP tag for a given CIK.
    """
    url = SEC_CONCEPT_URL.format(cik=cik, tag=tag)
    try:
        # Rate limiting: SEC allows 10 requests/sec. We sleep briefly to be safe.
        time.sleep(0.15)
        response = requests.get(url, headers=headers)
        if response.status_code == 404:
            return []
        response.raise_for_status()
        data = response.json()
        
        # The structure is usually data['units']['USD'] -> list of filings
        # Some companies report in other currencies, but we focus on USD for simplicity.
        if 'units' in data and 'USD' in data['units']:
            return data['units']['USD']
        return []
    except Exception as e:
        # print(f"[!] Warning: Could not fetch {tag} for CIK {cik}: {e}")
        return []

def process_filings(ticker, cik, headers):
    """
    Aggregates Revenue and Net Income for the last few years (Annual 10-K only).
    """
    print(f"[*] Processing {ticker} (CIK: {cik})...")
    
    financial_data = {}
    
    for metric_name, us_gaap_tag in METRICS.items():
        raw_data = fetch_metric(cik, us_gaap_tag, headers)
        
        # Filter for 10-K filings (Annual reports) to avoid seasonality noise
        # 'form' field usually contains '10-K'
        # 'fp' (Fiscal Period) should be 'FY' (Fiscal Year)
        annual_data = [
            d for d in raw_data 
            if d.get('form') == '10-K' and d.get('fp') == 'FY'
        ]
        
        # Sort by year descending and take unique years
        # Using a dictionary to overwrite duplicates (keeping latest filed)
        by_year = {}
        for entry in annual_data:
            year = entry.get('fy')
            val = entry.get('val')
            if year and val is not None:
                by_year[year] = val
        
        financial_data[metric_name] = by_year

    # Flatten data for DataFrame
    # We want rows like: Ticker, Year, Revenue, NetIncome
    rows = []
    
    # Find all unique years found across metrics
    all_years = set()
    for m in financial_data:
        all_years.update(financial_data[m].keys())
    
    sorted_years = sorted(list(all_years), reverse=True)
    
    # Keep only the last 5 years to keep the sheet clean
    for year in sorted_years[:5]:
        row = {
            'Ticker': ticker,
            'Year': year,
            'Revenue': financial_data['Revenues'].get(year, None),
            'Net Income': financial_data['NetIncome'].get(year, None)
        }
        rows.append(row)
        
    return rows

def main():
    parser = argparse.ArgumentParser(description="SEC EDGAR Financial Scraper")
    parser.add_argument("--tickers", type=str, required=True, help="Comma-separated list of stock tickers (e.g., AAPL,MSFT,TSLA)")
    parser.add_argument("--email", type=str, required=True, help="Your email address (Required for SEC API User-Agent)")
    parser.add_argument("--output", type=str, default="financial_data.csv", help="Output filename (CSV)")
    
    args = parser.parse_args()
    
    # 1. Setup Headers
    headers = get_headers(args.email)
    
    # 2. Get CIK Map
    ticker_map = get_cik_mapping(headers)
    
    target_tickers = [t.strip().upper() for t in args.tickers.split(",")]
    all_rows = []
    
    # 3. Loop through tickers
    for ticker in target_tickers:
        if ticker not in ticker_map:
            print(f"[!] Ticker {ticker} not found in SEC database. Skipping.")
            continue
            
        cik = ticker_map[ticker]
        try:
            company_rows = process_filings(ticker, cik, headers)
            all_rows.extend(company_rows)
        except Exception as e:
            print(f"[!] Error processing {ticker}: {e}")
            
    # 4. Export Data
    if all_rows:
        df = pd.DataFrame(all_rows)
        # Reorder columns
        df = df[['Ticker', 'Year', 'Revenue', 'Net Income']]
        
        print("\n[-] Extracted Data Preview:")
        print(df.head(10))
        
        df.to_csv(args.output, index=False)
        print(f"\n[+] Success! Data saved to {args.output}")
    else:
        print("\n[!] No data extracted. Check tickers or internet connection.")

if __name__ == "__main__":
    main()