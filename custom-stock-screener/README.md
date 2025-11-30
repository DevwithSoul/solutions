# Automated Custom Stock Screener

## Problem Description
Retail investors often find free stock screening tools too rigid. They lack the ability to define custom logic for valuation (e.g., combining specific growth thresholds with debt ratios) and struggle with the manual effort required to aggregate data for multiple companies into a single view for comparison.

## Solution Overview
This Python-based tool automates the collection of fundamental financial data. It allows the user to:
1. Input a list of stock tickers via the command line.
2. Automatically fetch key financial metrics (P/E, Market Cap, Debt/Equity, etc.) using the `yfinance` API.
3. Apply programmable, custom logic to score and rank stocks.
4. Export the aggregated and calculated data to a CSV file for Excel/Sheets analysis.

## Prerequisites
- Python 3.8 or higher
- Internet connection (to fetch data from Yahoo Finance)

## Installation
1. Unzip the project folder.
2. Open a terminal/command prompt in the folder.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the script from the command line by passing the stock tickers you want to analyze.

**Basic Example:**
```bash
python stock_screener.py AAPL MSFT GOOGL TSLA AMD
```

**Specify Output File:**
```bash
python stock_screener.py NVDA INTC QCOM --output my_chip_stocks.csv
```

## Configuration
To change the logic for the "Custom Value Score":
1. Open `stock_screener.py`.
2. Locate the `calculate_custom_metrics` function.
3. Modify the `value_score` logic to fit your investment strategy (e.g., change P/E thresholds or weight revenue growth higher).

## Recommendations
- The tool relies on Yahoo Finance data, which is free but rate-limited. Avoid running lists of 100+ stocks in rapid succession to prevent temporary IP bans.
- For production use with high-frequency requests, consider integrating a paid API like Alpha Vantage or IEX Cloud.