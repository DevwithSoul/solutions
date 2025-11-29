# YNAB Monthly Balance Derivation Tool

## Problem Description
Many users require historical monthly account balances for financial analysis, budgeting reviews, or integration with other tools. However, the official YNAB API does not provide a direct endpoint to retrieve account balances at specific historical dates or aggregated monthly balances. This means developers must implement a custom solution to process raw transaction data and derive these balances programmatically.

## Solution Overview
This Python script provides a robust solution to derive historical monthly account balances from your YNAB budget. It works by:
1.  **Fetching all accounts** associated with your specified YNAB budget.
2.  **Fetching all transactions** for that budget from the YNAB API.
3.  **Processing transactions**: It groups transactions by account and by month.
4.  **Calculating cumulative balances**: For each open account, it iterates through all months from the earliest transaction date to the latest, summing the net change from transactions for that month and carrying forward the balance from the previous month. This provides a derived balance at the end of each month.

The final output is a structured dictionary, providing a list of monthly balances for each account, which is also saved to a JSON file.

## Prerequisites
*   **Python 3.7+**: The script is written in Python.
*   **`requests` library**: Used for making HTTP requests to the YNAB API. Install it using pip:
    ```bash
    pip install requests
    ```
*   **YNAB Personal Access Token (PAT)**: This is required to authenticate with the YNAB API. You can generate one from your YNAB settings page: `https://app.ynab.com/settings/developer`.
*   **YNAB Budget ID**: The unique identifier for the specific YNAB budget you want to analyze. You can find this in the URL when viewing your budget in YNAB (e.g., `https://app.ynab.com/<budget_id>/...`).

## Installation
1.  **Save the script**: Save the provided Python code as `ynab_monthly_balances.py`.
2.  **Set Environment Variables**: For security, store your YNAB Personal Access Token and Budget ID as environment variables. Replace `YOUR_PAT_HERE` and `YOUR_BUDGET_ID_HERE` with your actual values.
    *   **Linux/macOS (bash/zsh)**:
        ```bash
        export YNAB_ACCESS_TOKEN="YOUR_PAT_HERE"
        export YNAB_BUDGET_ID="YOUR_BUDGET_ID_HERE"
        # To make them persistent, add these lines to your ~/.bashrc or ~/.zshrc file
        ```
    *   **Windows (Command Prompt)**:
        ```cmd
        set YNAB_ACCESS_TOKEN="YOUR_PAT_HERE"
        set YNAB_BUDGET_ID="YOUR_BUDGET_ID_HERE"
        # For persistent variables, use System Properties -> Environment Variables
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        $env:YNAB_ACCESS_TOKEN="YOUR_PAT_HERE"
        $env:YNAB_BUDGET_ID="YOUR_BUDGET_ID_HERE"
        # To make them persistent, add these to your PowerShell profile
        ```

## Usage
Navigate to the directory where you saved `ynab_monthly_balances.py` in your terminal and run the script:

```bash
python ynab_monthly_balances.py
```

The script will:
1.  Print status messages as it fetches accounts and transactions.
2.  Print a summary of the derived monthly balances for each account to the console.
3.  Save the complete derived monthly balances to a JSON file named `ynab_monthly_balances.json` in the same directory.

### Output Format (`ynab_monthly_balances.json`)
```json
{
  "Account Name 1": [
    { "month": "YYYY-MM", "balance": 1234.56 },
    { "month": "YYYY-MM", "balance": 1300.00 }
  ],
  "Account Name 2": [
    { "month": "YYYY-MM", "balance": 5000.00 },
    { "month": "YYYY-MM", "balance": 4800.75 }
  ]
}
```

## Recommendations
*   **Security**: Always use environment variables for sensitive data like API tokens. Avoid hardcoding them directly in your script.
*   **Error Handling**: The script includes basic error handling for API requests and configuration issues. For production environments, consider more sophisticated logging and retry mechanisms.
*   **Large Budgets**: For budgets with tens of thousands or hundreds of thousands of transactions, fetching all transactions in a single API call might be slow or encounter rate limits. A more advanced solution could implement chunked fetching using the `since_date` parameter of the YNAB API's `transactions` endpoint.
*   **Initial Balances**: This script derives balances by cumulatively summing transactions from the earliest date recorded in your YNAB budget. It essentially assumes a starting balance of 0 before the very first transaction for an account. If you need balances relative to a specific historical known balance (e.g., from an account opening statement), you would need to adjust the initial `current_account_balances` accordingly.
*   **Extensibility**: The core logic for deriving balances can be extended to calculate budget-wide balances, balances per category, or other aggregates by modifying how transactions are grouped and summed.