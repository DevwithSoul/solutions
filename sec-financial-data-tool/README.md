# Automated SEC Financial Data Scraper

## Problem Description
Financial analysts and developers often struggle to extract consistent historical data from SEC filings (10-K, 10-Q). Parsing raw HTML is fragile due to inconsistent formatting across companies and years. Furthermore, the SEC EDGAR system has strict rate limits and requires specific User-Agent headers, making ad-hoc scraping unreliable.

## Solution Overview
This tool bypasses the need for complex HTML parsing by leveraging the SEC's **Company Facts API**. This API provides pre-processed XBRL data in JSON format, allowing us to extract precise US-GAAP metrics (like Assets, Revenue, Net Income) mapped to specific reporting periods.

### Key Features
- **Compliance:** Handles SEC User-Agent requirements automatically.
- **Reliability:** Uses the official JSON API source rather than screen scraping.
- **Structured Output:** Converts nested JSON trees into a clean CSV format ready for Excel or Python analysis.
- **Ticker Support:** Automatically maps stock tickers (e.g., AAPL) to SEC CIK numbers.

## Prerequisites
- Python 3.8+
- Internet connection (to access `data.sec.gov`)

## Installation
1. Unzip the tool package.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the script from the command line. You **MUST** provide an email address to satisfy SEC API requirements.

```bash
python sec_financial_scraper.py --ticker AAPL --email yourname@example.com
```

### Arguments
- `--ticker`: The stock symbol to scrape (e.g., MSFT, TSLA).
- `--email`: Your contact email (Required by SEC for the User-Agent header).
- `--output`: (Optional) Filename for the output CSV. Defaults to `financial_data.csv`.

### Example Output
`financial_data.csv` will contain columns like:
- `Concept`: (e.g., NetIncomeLoss)
- `Form`: (e.g., 10-K, 10-Q)
- `End Date`: The reporting period end date
- `Value`: The numerical value
- `Unit`: (e.g., USD)

## Recommendations
- **Rate Limiting:** The SEC limits requests to ~10 per second. This script is single-threaded and safe for individual usage. If you extend this to loop through thousands of tickers, add `time.sleep(0.1)` between requests.
- **Data Availability:** Not all companies report using XBRL (though most major public US companies do). If a ticker returns no data, checking the raw filing on SEC.gov is recommended.