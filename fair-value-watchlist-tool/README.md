# Automated 'Fair Value' Stock Watchlist

## Problem Description
Value investors often waste hours every weekend manually looking up financial metrics (EPS, Book Value, Price) for a watchlist of stocks, copying them into spreadsheets, and applying formulas to determine if a stock is "on sale." This manual process is prone to errors and time-consuming.

## Solution Overview
This tool automates the entire valuation process. It is a Python script that:
1.  **Fetches Real-Time Data**: Connects to Yahoo Finance to get the latest price, EPS, Book Value, and Analyst Estimates.
2.  **Calculates Intrinsic Value**: 
    -   Implements the **Graham Number** ($ \sqrt{22.5 \times EPS 	imes Book Value} $) for classic value stocks.
    -   Falls back to **Analyst Consensus Price** for growth stocks or those with negative earnings.
3.  **Applies Margin of Safety**: Automatically calculates a "Buy Threshold" (default 20% discount).
4.  **Generates Reports**: Exports a clean CSV file sorted by "Potential Upside," ready to open in Excel.

## Prerequisites
-   **Python 3.8+** installed on your machine.
-   **pip** (Python package manager).

## Installation
1.  Download and unzip the `fair-value-watchlist-tool` folder.
2.  Open your terminal or command prompt in this folder.
3.  Install the required libraries:
    ```bash
    pip install yfinance pandas numpy openpyxl
    ```

## Usage
1.  **Configure Tickers**: Open `fair_value_watch.py` in a text editor. Modify the `TICKERS` list at the top to include the stock symbols you want to track.
    ```python
    TICKERS = ["AAPL", "MSFT", "INTC", "YOUR_TICKER"]
    ```
2.  **Run the Script**:
    ```bash
    python fair_value_watch.py
    ```
3.  **View Results**: A file named `fair_value_report_YYYY-MM-DD.csv` will be created in the folder. Open this in Excel or Google Sheets to see your buy signals.

## Recommendations
-   **Valuation Logic**: The script currently uses the Graham Number. If you prefer Discounted Cash Flow (DCF) or PEG ratios, modify the `calculate_intrinsic_value` function.
-   **Automation**: You can use Windows Task Scheduler or a Cron job (Linux/Mac) to run this script automatically every Friday at market close.
-   **API Limits**: The script uses `yfinance`, which is free but rate-limited. If you add hundreds of tickers, increase the `time.sleep(0.5)` duration to prevent IP blocking.