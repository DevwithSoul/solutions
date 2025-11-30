# Automated Bulk Stock Financials Extractor

## Problem Description
Investors and analysts often need to compare historical financial metrics (like Revenue and Free Cash Flow) across hundreds of stocks. Manually visiting finance websites, copying data, and pasting it into Excel is tedious, error-prone, and hard to maintain. 

## Solution Overview
This tool automates the process using Python. It utilizes the `yfinance` library to query Yahoo Finance's public API, extracts key financial metrics from the Income Statement and Cash Flow Statement, and compiles the data into a structured, multi-sheet Excel file suitable for immediate analysis.

### Key Features
- **Bulk Processing:** Accepts lists of tickers via CLI or text file.
- **Automatic Cleaning:** Aligns dates between different financial statements.
- **Smart Export:** Generates an Excel file with:
  - `Historical Data`: All available annual data points.
  - `Latest Summary`: A snapshot of the most recent fiscal year for every stock.
- **Robustness:** Includes error handling for missing data or invalid tickers.

## Prerequisites
- Python 3.8 or higher.
- An internet connection (to fetch data from Yahoo Finance).

## Installation

1. **Unzip the tool** to a folder.
2. **Install dependencies** using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from your terminal/command prompt.

### Option 1: Direct Ticker Input
Pass a comma-separated list of symbols.
```bash
python bulk_financials_extractor.py --tickers AAPL,MSFT,GOOGL,TSLA
```

### Option 2: File Input
Create a text file (e.g., `stocks.txt`) with one ticker per line, then run:
```bash
python bulk_financials_extractor.py --file stocks.txt
```

### Option 3: Custom Output Filename
```bash
python bulk_financials_extractor.py --tickers AAPL --output my_analysis.xlsx
```

## Configuration / Arguments
| Argument | Description | Default |
| :--- | :--- | :--- |
| `--tickers` | Comma-separated list of stock symbols. | None |
| `--file` | Path to a text file containing tickers. | None |
| `--output` | Name of the generated Excel file. | `financial_report.xlsx` |
| `--delay` | Seconds to wait between requests (prevents rate limiting). | `0.5` |

## Recommendations
- **Rate Limiting:** Yahoo Finance is generally lenient, but if you are processing >500 stocks, increase the `--delay` to 1.0 or 2.0 seconds to avoid temporary IP bans.
- **Data Availability:** Not all stocks (especially OTC or very small caps) have complete data on Yahoo Finance. The script will warn you if data is missing but continue processing the rest.