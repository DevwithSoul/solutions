# The New-Money Portfolio Rebalancer

## Problem Description
Investors often struggle to maintain their target asset allocation. When adding new funds (monthly contributions, bonuses), calculating exactly how much of each asset to buy to bring the portfolio back into balance—without selling anything and triggering taxable events—requires complex spreadsheet math. 

## Solution Overview
This Python utility automates the "New Money" rebalancing strategy. It takes your current holdings and a cash contribution amount, then calculates purely **additive** trades. It directs new capital specifically to the assets that are most underweight relative to your targets.

## Prerequisites
*   Python 3.6+

## Installation
1.  Unzip the tool archive.
2.  Install the required dependency for pretty printing tables:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Prepare your Portfolio Data**
    Create a `portfolio.json` file in the same directory. Use the following format:

    ```json
    [
        {"symbol": "VTI", "shares": 50, "price": 220.50, "target_pct": 0.60},
        {"symbol": "VXUS", "shares": 100, "price": 55.20, "target_pct": 0.30},
        {"symbol": "BND", "shares": 40, "price": 72.10, "target_pct": 0.10}
    ]
    ```

2.  **Run the Tool**
    Run the script via command line, specifying the portfolio file and the amount of cash you wish to invest.

    ```bash
    python portfolio_rebalancer.py --portfolio portfolio.json --cash 1000
    ```

3.  **View Output**
    The tool will generate a table showing exactly how much dollar value to allocate to each ticker and the estimated number of shares to purchase.

## Configuration
*   **target_pct**: Ensure these sum to 1.0 (100%) in your JSON file.
*   **price**: You must manually update prices in the JSON file or integrate a price fetcher (kept manual here for simplicity and reliability).

## Recommendations
*   This tool assumes fractional shares are possible. If your brokerage only supports whole shares, round down the "Est. Shares" column and invest the remainder in the most underweight asset.
*   Always verify prices before executing trades.