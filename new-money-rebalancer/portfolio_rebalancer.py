#aiwebarchitects
import argparse
import json
import sys
from tabulate import tabulate

"""
Title: The New-Money Portfolio Rebalancer
Description: 
    Calculates how to distribute a cash contribution across a portfolio 
    to bring it closer to target allocations without selling any assets 
    (avoiding capital gains taxes).

Usage:
    python portfolio_rebalancer.py --portfolio portfolio.json --cash 5000

Input Format (portfolio.json):
    [
        {"symbol": "VTI", "shares": 50, "price": 220.50, "target_pct": 0.60},
        {"symbol": "VXUS", "shares": 100, "price": 55.20, "target_pct": 0.30},
        {"symbol": "BND", "shares": 40, "price": 72.10, "target_pct": 0.10}
    ]
"""

def load_portfolio(filepath):
    """Loads portfolio data from a JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File '{filepath}' contains invalid JSON.")
        sys.exit(1)

def validate_inputs(portfolio):
    """Validates that target percentages sum to 1.0 (100%)."""
    total_target = sum(item.get('target_pct', 0) for item in portfolio)
    # Allow for small floating point errors
    if not (0.99 <= total_target <= 1.01):
        print(f"Warning: Target percentages sum to {total_target*100:.2f}%, not 100%.")
        print("Calculations will proceed, but results may be skewed.")

def calculate_rebalancing(portfolio, new_cash):
    """
    Core Logic:
    1. Calculate current total value.
    2. Calculate theoretical total value (Current + New Cash).
    3. Determine ideal value for each asset based on targets.
    4. Determine the 'deficit' (how much is needed to reach target).
    5. Allocate cash proportionally to the deficits.
    """
    
    # 1. Current State Analysis
    current_total_value = 0.0
    for asset in portfolio:
        asset['current_value'] = asset['shares'] * asset['price']
        current_total_value += asset['current_value']

    final_projected_total = current_total_value + new_cash

    # 2. Calculate Deficits
    total_deficit = 0.0
    for asset in portfolio:
        # The value this asset *should* have after we add money
        target_value = final_projected_total * asset['target_pct']
        asset['target_value'] = target_value
        
        # Difference between ideal and current
        diff = target_value - asset['current_value']
        
        # We only care if we are UNDER the target (positive diff)
        # We do not sell (negative diff becomes 0 demand for new money)
        if diff > 0:
            asset['deficit'] = diff
            total_deficit += diff
        else:
            asset['deficit'] = 0.0

    # 3. Allocate New Cash
    # Logic: We distribute the new_cash weighted by the size of the deficit.
    # If total_deficit > new_cash, we can't fill all buckets, so we fill proportionally.
    # If total_deficit < new_cash, we fill deficits and distribute remainder by target %.
    
    allocations = []
    
    remaining_cash = new_cash

    for asset in portfolio:
        buy_amount = 0.0
        
        if total_deficit > 0:
            if new_cash <= total_deficit:
                # Not enough cash to fill all deficits, distribute proportionally
                weight = asset['deficit'] / total_deficit
                buy_amount = new_cash * weight
            else:
                # Enough cash to fill deficits, distribute remainder by target %
                buy_amount = asset['deficit'] + (new_cash - total_deficit) * asset['target_pct']
        else:
            # Edge case: All assets are exactly at or above target (unlikely with new cash)
            # Distribute based on target_pct to maintain ratios
            buy_amount = new_cash * asset['target_pct']
            
        asset['buy_amount'] = buy_amount
        
        # Calculate estimated shares to buy
        shares_to_buy = buy_amount / asset['price'] if asset['price'] > 0 else 0
        
        allocations.append([
            asset['symbol'],
            f"${asset['current_value']:,.2f}",
            f"{asset['target_pct']*100:.1f}%",
            f"${asset['target_value']:,.2f}",
            f"${buy_amount:,.2f}",
            f"{shares_to_buy:.4f}"
        ])

    return allocations, current_total_value, final_projected_total

def main():
    parser = argparse.ArgumentParser(description="New-Money Portfolio Rebalancer")
    parser.add_argument('--portfolio', required=True, help="Path to JSON file containing portfolio data")
    parser.add_argument('--cash', required=True, type=float, help="Amount of new cash to contribute")
    
    args = parser.parse_args()

    print(f"\n--- Portfolio Rebalancer ---")
    print(f"Processing File: {args.portfolio}")
    print(f"New Cash Contribution: ${args.cash:,.2f}\n")

    data = load_portfolio(args.portfolio)
    validate_inputs(data)
    
    results, start_val, end_val = calculate_rebalancing(data, args.cash)
    
    headers = ["Symbol", "Current Val", "Target %", "Ideal Val", "ALLOCATE (Buy)", "Est. Shares"]
    
    print(tabulate(results, headers=headers, tablefmt="grid"))
    
    print(f"\nStarting Portfolio Value: ${start_val:,.2f}")
    print(f"Final Project Value:      ${end_val:,.2f}")
    print("\nNote: 'Est. Shares' assumes fractional shares are allowed. Round down for whole shares.")

if __name__ == "__main__":
    main()