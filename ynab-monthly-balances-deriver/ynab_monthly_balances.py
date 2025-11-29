#aiwebarchitects
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import os
import json

# --- Configuration ---
# YNAB API Base URL
YNAB_API_BASE_URL = "https://api.ynab.com/v1"

# Your YNAB Personal Access Token (PAT)
# Get this from: https://app.ynab.com/settings/developer
# It's highly recommended to store this in an environment variable for security.
# Example (Linux/macOS): export YNAB_ACCESS_TOKEN="YOUR_PAT_HERE"
# Example (Windows CMD): set YNAB_ACCESS_TOKEN="YOUR_PAT_HERE"
YNAB_ACCESS_TOKEN = os.getenv("YNAB_ACCESS_TOKEN")

# Your YNAB Budget ID
# You can find this in the URL when viewing your budget in YNAB (e.g., https://app.ynab.com/<budget_id>/...)
# Or by listing budgets via the API and inspecting the response.
# Example (Linux/macOS): export YNAB_BUDGET_ID="YOUR_BUDGET_ID_HERE"
# Example (Windows CMD): set YNAB_BUDGET_ID="YOUR_BUDGET_ID_HERE"
YNAB_BUDGET_ID = os.getenv("YNAB_BUDGET_ID")

def make_ynab_request(endpoint, params=None):
    """
    Helper function to make authenticated YNAB API GET requests.
    Raises exceptions for network or API errors.
    """
    if not YNAB_ACCESS_TOKEN:
        raise ValueError("YNAB_ACCESS_TOKEN environment variable is not set. Please configure it.")

    headers = {
        "Authorization": f"Bearer {YNAB_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"{YNAB_API_BASE_URL}/{endpoint}"

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()['data']
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        raise
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error occurred: {e}. Check your internet connection or YNAB API status.")
        raise
    except requests.exceptions.Timeout as e:
        print(f"Timeout error occurred: {e}. The request took too long.")
        raise
    except requests.exceptions.RequestException as e:
        print(f"An unexpected request error occurred: {e}")
        raise
    except KeyError:
        print(f"API response missing 'data' key or malformed: {response.text}")
        raise

def get_budget_accounts():
    """
    Fetches all accounts (open and closed) for the configured budget from the YNAB API.
    Returns a list of account dictionaries.
    """
    if not YNAB_BUDGET_ID:
        raise ValueError("YNAB_BUDGET_ID environment variable is not set. Please configure it.")
    
    print(f"Fetching accounts for budget ID: {YNAB_BUDGET_ID}...")
    data = make_ynab_request(f"budgets/{YNAB_BUDGET_ID}/accounts")
    accounts = data.get('accounts', [])
    print(f"Found {len(accounts)} accounts.")
    return accounts

def get_all_transactions():
    """
    Fetches all transactions for the configured budget from the YNAB API.
    Returns a list of transaction dictionaries.
    Note: For extremely large budgets, this might be slow or hit rate limits.
          A more advanced solution might fetch transactions in chunks using `since_date`.
    """
    if not YNAB_BUDGET_ID:
        raise ValueError("YNAB_BUDGET_ID environment variable is not set. Please configure it.")

    print(f"Fetching all transactions for budget ID: {YNAB_BUDGET_ID}...")
    
    # The YNAB API /transactions endpoint returns all transactions for the budget.
    # It does not typically require manual pagination in the same way some other APIs do,
    # but a 'last_knowledge_of_server' token can be used for incremental sync.
    # For a full historical fetch, this single call is usually sufficient.
    data = make_ynab_request(f"budgets/{YNAB_BUDGET_ID}/transactions")
    transactions = data.get('transactions', [])
    
    print(f"Found {len(transactions)} transactions.")
    return transactions

def generate_month_sequence(min_date_obj, max_date_obj):
    """
    Generates a list of 'YYYY-MM' strings for all months
    between the given min_date_obj and max_date_obj (inclusive).
    """
    if not min_date_obj or not max_date_obj:
        return []

    months = []
    # Start from the first day of the min_date month
    current_date = min_date_obj.replace(day=1)
    
    # Iterate until the current month exceeds the max_date month
    while current_date.year < max_date_obj.year or \
          (current_date.year == max_date_obj.year and current_date.month <= max_date_obj.month):
        months.append(current_date.strftime('%Y-%m'))
        
        # Move to the first day of the next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)
    return months


def derive_monthly_balances(transactions, accounts):
    """
    Derives historical monthly account balances from a list of transactions and accounts.
    
    This function calculates the cumulative balance for each *open* account at the end of each month
    within the range of the provided transactions. It assumes an initial balance of 0 for each account
    prior to its earliest recorded transaction in the dataset. Balances are carried forward
    for months where an account has no transactions.

    Args:
        transactions (list): A list of transaction dictionaries from the YNAB API.
        accounts (list): A list of account dictionaries from the YNAB API.

    Returns:
        dict: A dictionary where keys are account names and values are lists of dictionaries,
              each containing 'month' (YYYY-MM string) and 'balance' (float) for that month.
              Example: {
                  'Checking': [{'month': '2023-01', 'balance': 1500.00}, ...],
                  'Savings': [{'month': '2023-01', 'balance': 5000.00}, ...]
              }
    """
    if not transactions or not accounts:
        print("No transactions or accounts provided. Cannot derive balances.")
        return {}

    print("Deriving monthly balances...")
    
    # Create a map of account ID to account name, only for open accounts
    account_name_map = {acc['id']: acc['name'] for acc in accounts if not acc['closed']}

    # 1. Group transaction amounts by account ID and month (YYYY-MM)
    # This aggregates all inflows/outflows for a given account in a specific month.
    txns_by_account_month = defaultdict(lambda: defaultdict(list)) # {account_id: {month_year: [amount1, amount2, ...]}}
    
    all_transaction_dates = []
    for txn in transactions:
        # Only process transactions for accounts that are currently open
        if txn['account_id'] in account_name_map:
            date_obj = datetime.fromisoformat(txn['date'])
            month_year_str = date_obj.strftime('%Y-%m')
            # YNAB amounts are in milliunits, so divide by 1000 for actual currency units
            txns_by_account_month[txn['account_id']][month_year_str].append(txn['amount'] / 1000.0)
            all_transaction_dates.append(date_obj)

    if not all_transaction_dates:
        print("No relevant transactions found for open accounts. Cannot derive balances.")
        return {}

    # 2. Determine the full date range (min_date to max_date) covered by transactions
    # This ensures we generate balance entries for every month in between.
    min_date = min(all_transaction_dates)
    max_date = max(all_transaction_dates)
    month_sequence = generate_month_sequence(min_date, max_date)

    if not month_sequence:
        print("No valid month sequence generated from transaction dates.")
        return {}

    # 3. Calculate running balances for each account, month by month
    derived_monthly_balances = {} # {account_name: [{'month': 'YYYY-MM', 'balance': X.XX}, ...]}
    current_account_balances = defaultdict(float) # {account_id: cumulative_balance_at_end_of_last_processed_month}

    for month_str in month_sequence:
        for account_id, account_name in account_name_map.items():
            # Sum all transaction amounts for this specific account in the current month
            # If no transactions for the month, monthly_net_change will be 0.
            monthly_net_change = sum(txns_by_account_month[account_id].get(month_str, []))
            
            # Update the running balance for this account by adding the net change for the month
            current_account_balances[account_id] += monthly_net_change
            
            # Initialize the list for the account if it's the first time we're seeing it
            if account_name not in derived_monthly_balances:
                derived_monthly_balances[account_name] = []
            
            # Append the derived balance for this month to the account's list
            # Round to two decimal places for currency precision
            derived_monthly_balances[account_name].append({
                'month': month_str,
                'balance': round(current_account_balances[account_id], 2)
            })
    
    print("Monthly balances derived successfully.")
    return derived_monthly_balances

def main():
    """
    Main function to orchestrate the process:
    1. Fetches accounts from YNAB.
    2. Fetches all transactions from YNAB.
    3. Derives historical monthly balances for each account.
    4. Prints the results and saves them to a JSON file.
    """
    print("Starting YNAB Monthly Balance Derivation Tool...")
    try:
        accounts = get_budget_accounts()
        transactions = get_all_transactions()
        
        monthly_balances = derive_monthly_balances(transactions, accounts)
        
        if monthly_balances:
            print("\n--- Derived Monthly Account Balances Summary ---")
            # Print a summary to console for immediate feedback
            for account_name, balances_list in monthly_balances.items():
                print(f"\nAccount: {account_name}")
                # Print only the first few and last few entries for brevity if there are many months
                if len(balances_list) > 6:
                    for entry in balances_list[:3]:
                        print(f"  {entry['month']}: {entry['balance']:,.2f}")
                    print("  ...")
                    for entry in balances_list[-3:]: # Show the latest three months
                        print(f"  {entry['month']}: {entry['balance']:,.2f}")
                else:
                    for entry in balances_list:
                        print(f"  {entry['month']}: {entry['balance']:,.2f}")
            
            # Save the full derived balances to a JSON file
            output_filename = "ynab_monthly_balances.json"
            with open(output_filename, 'w') as f:
                json.dump(monthly_balances, f, indent=4) # Use indent for pretty-printing in the file
            print(f"\nFull derived monthly balances saved to {output_filename}")
        else:
            print("No monthly balances could be derived. Please check your YNAB data and configuration.")

    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("Please ensure YNAB_ACCESS_TOKEN and YNAB_BUDGET_ID environment variables are correctly set.")
    except requests.exceptions.RequestException as e:
        print(f"\nAPI Communication Error: {e}")
        print("Could not connect to YNAB API. Check your internet connection or API status.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()