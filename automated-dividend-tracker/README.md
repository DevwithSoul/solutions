# Automated Dividend Income Tracker

## Problem Description
Retail investors often struggle to forecast monthly cash flow because standard spreadsheet functions (like `GOOGLEFINANCE`) cannot easily retrieve specific Ex-Dividend dates, Yields, and Payout Ratios. Manually looking up these dates for a diversified portfolio is time-consuming and prone to human error.

## Solution Overview
This tool is a Python-based automation script that:
1. Accepts a list of stock tickers (via CLI arguments or a text file).
2. Connects to the Yahoo Finance API (via `yfinance`) to fetch real-time data.
3. Extracts critical dividend information: Ex-Dividend Date, Annual Rate, Yield, and Payout Ratio.
4. Exports the data to a clean CSV file, ready for import into Excel or Google Sheets.

## Prerequisites
- **Python 3.7+** installed on your system.
- **pip** (Python package manager).

## Installation

1. Unzip the downloaded folder `automated-dividend-tracker`.
2. Open your terminal or command prompt in this folder.
3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Method 1: Direct Command Line Input
You can pass tickers directly to the script:

```bash
python dividend_tracker.py --tickers AAPL MSFT JNJ O SCHD
```

### Method 2: Using a Text File
Create a file named `portfolio.txt` with one ticker per line, then run:

```bash
python dividend_tracker.py --file portfolio.txt
```

### Custom Output Filename
By default, it saves to `dividend_report.csv`. You can change this:

```bash
python dividend_tracker.py --tickers KO PEP --output my_income_forecast.csv
```

## Output Data
The resulting CSV contains:
- **Ticker**: Stock Symbol
- **Company Name**: Full legal name
- **Ex-Dividend Date**: The next or most recent ex-date (Essential for capture)
- **Annual Dividend Rate**: The cash amount paid per year
- **Dividend Yield**: The return percentage
- **Current Price**: Market price at fetch time
- **Payout Ratio**: Percentage of earnings paid as dividends (Safety metric)
- **Sector**: Industry sector

## Recommendations
- **Frequency**: Run this script weekly or monthly to update your spreadsheet.
- **Excel Integration**: In Excel, go to `Data` -> `Get Data (From Text/CSV)` and select the generated file to create a refreshable connection.
- **API Limits**: While Yahoo Finance is free, extremely heavy usage (thousands of requests per minute) may get your IP temporarily blocked. A simple delay can be added if processing 100+ tickers.