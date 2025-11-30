# Privacy-First Portfolio Rebalancer

## Problem Description
Investors managing assets across multiple brokerages often rely on manual spreadsheets to rebalance their portfolios. Linking accounts to third-party aggregators poses security risks, while manual calculation is prone to error and tedious. 

## Solution Overview
This tool is a local, Python-based automation script that:
1. **Ingests** a simple CSV of your current holdings and target allocations.
2. **Fetches** real-time market data using the Yahoo Finance API (via `yfinance`).
3. **Calculates** the exact trades needed to return your portfolio to its target allocation.
4. **Respects Privacy**: No financial data leaves your machine. Only ticker symbols are sent to Yahoo Finance to retrieve price data.

## Prerequisites
- Python 3.7+
- Internet connection (for fetching market prices)

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Prepare your CSV file** (e.g., `my_portfolio.csv`). 
   It must contain three columns: `Symbol`, `Quantity`, and `TargetPercent`.

   **Example `my_portfolio.csv`:**
   ```csv
   Symbol,Quantity,TargetPercent
   AAPL,10,20
   MSFT,5,20
   VTI,50,40
   BND,20,20
   ```

2. **Run the tool**:
   
   *Basic run:*
   ```bash
   python portfolio_rebalancer.py my_portfolio.csv
   ```

   *With a cash injection (e.g., investing an extra $1000):*
   ```bash
   python portfolio_rebalancer.py my_portfolio.csv --cash 1000
   ```

   *Save output to file:*
   ```bash
   python portfolio_rebalancer.py my_portfolio.csv --output plan.csv
   ```

## Configuration
No API keys are required. The tool uses the public Yahoo Finance endpoints via the `yfinance` library.

## Recommendations
- Always verify trade suggestions before executing them in your brokerage.
- Run the tool during market hours for the most accurate pricing, or after close for end-of-day estimates.
- If you have cash in your brokerage account that is part of the portfolio, add it as a row in the CSV with a dummy symbol (e.g., `CASH_USD`) and manually set the price to $1 in the code or ensure it's treated as a fixed asset.