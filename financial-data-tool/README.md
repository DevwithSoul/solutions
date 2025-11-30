# Automated Fundamental Data Aggregator

## Problem Description
Investors frequently need specific fundamental ratios like **ROIC (Return on Invested Capital)** and **EV/EBITDA** to evaluate the quality and valuation of companies. However, most free financial websites do not allow easy export of this data, and manual calculation from financial statements is prone to error and time-consuming. Generic scraping is often blocked by anti-bot measures.

## Solution Overview
This tool automates the retrieval and calculation of high-value financial metrics.

1.  **Data Source**: Uses `yfinance` to access Yahoo Finance API data programmatically.
2.  **Custom Calculation**: While EV/EBITDA is fetched directly, ROIC is calculated manually using the latest annual Financials and Balance Sheet data to ensure accuracy ($ROIC = NOPAT / Invested Capital$).
3.  **Normalization**: Outputs a clean, standardized CSV file ready for Excel or further analysis.

## Prerequisites
- Python 3.8 or higher
- Internet connection (for API access)

## Installation

1.  Unzip the tool folder.
2.  Install dependencies using the requirements file:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script via command line. You can provide tickers directly or via a text file.

### Option 1: Direct Tickers
```bash
python fundamental_aggregator.py --tickers AAPL MSFT GOOG TSLA
```

### Option 2: From File
Create a file named `watchlist.txt` with one ticker per line, then run:
```bash
python fundamental_aggregator.py --file watchlist.txt
```

### Output
The tool prints a summary table to the console and saves a detailed CSV file (default: `fundamental_analysis.csv`).

To change the output filename:
```bash
python fundamental_aggregator.py --tickers AAPL --output my_portfolio.csv
```

## Configuration
No API keys are required for this version as it relies on public data access via `yfinance`. Note that excessive requests in a short period may lead to temporary IP rate limiting by Yahoo Finance.

## Recommendations
- **ROIC Calculation**: The tool estimates ROIC using the formula: `EBIT * (1 - TaxRate) / (Equity + Debt - Cash)`. This is a standard approximation. For deeper analysis, always verify against official 10-K filings.
- **Data Availability**: Some metrics (like EV/EBITDA) may be missing for very small cap stocks or ETFs.
