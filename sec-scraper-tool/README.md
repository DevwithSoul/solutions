# Automated SEC EDGAR Financial Scraper

## Problem Description
Value investors often struggle to analyze batches of stocks because manually extracting financial data (like Revenue and Net Income) from SEC 10-K filings is tedious. Existing free APIs are often rate-limited, unreliable, or lack specific XBRL tag data. This tool solves that by interfacing directly with the SEC's public data API to normalize and export financial metrics into a CSV spreadsheet.

## Solution Overview
This Python script:
1.  Fetches the official Ticker-to-CIK mapping from `sec.gov`.
2.  Iterates through a user-provided list of stock tickers.
3.  Queries the SEC EDGAR Company Concepts API for specific US-GAAP XBRL tags (`Revenues`, `NetIncomeLoss`).
4.  Filters data to retain only Annual (10-K) filings to ensure consistency.
5.  Normalizes the data into a structured table and exports it to CSV.

## Prerequisites
*   Python 3.7+
*   Internet connection (to access `data.sec.gov`)

## Installation

1.  **Unzip the tool**:
    ```bash
    unzip sec-scraper-tool.zip
    cd sec-scraper-tool
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The SEC requires a User-Agent header containing an email address to identify the requester. You must provide this via the `--email` argument.

### Basic Command

```bash
python sec_financial_scraper.py --tickers AAPL,MSFT,GOOGL,TSLA --email yourname@example.com
```

### Custom Output File

```bash
python sec_financial_scraper.py --tickers NVDA,AMD --email yourname@example.com --output my_analysis.csv
```

## Data Note
*   **Revenue**: Fetches the `us-gaap:Revenues` tag.
*   **Net Income**: Fetches the `us-gaap:NetIncomeLoss` tag.
*   **Currency**: Filters for `USD`.
*   **Period**: Filters for `10-K` (Annual) filings only.

## Troubleshooting
*   **403 Forbidden**: Ensure you provided a valid email address in the `--email` argument. The SEC blocks requests without a proper User-Agent.
*   **Empty Data**: Some companies use different XBRL tags for Revenue (e.g., `RevenueFromContractWithCustomer...`). This scraper uses the standard `Revenues` tag which covers most traditional companies.

## Recommendations
For a full-scale production application, consider adding:
*   Logic to handle alternative XBRL tags for Revenue.
*   A database (SQLite/PostgreSQL) to cache data and reduce load on SEC servers.
*   Quarterly (10-Q) data extraction logic.