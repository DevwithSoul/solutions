# IV Rank Monitoring & Alerting System

## Problem Description
The user is unable to manually track historical implied volatility trends to identify profitable premium-selling opportunities. They require an automated pipeline to scrape real-time options data, calculate IV ranks, and trigger alerts when volatility reaches specific thresholds.

## Solution Overview
This solution uses the polygon.io API to fetch the current implied volatility (IV) of the at-the-money (ATM) call option for a given stock. It then compares the current IV to user-defined low and high thresholds. If the IV breaches either threshold, an alert is printed to the console.

Note: This is a simplified version that does not calculate IV Rank (IVR) due to API limitations and complexity. Instead, it monitors the absolute IV.

## Prerequisites
- Python 3.6 or higher
- A polygon.io API key (free tier available at https://polygon.io/dashboard)

## Installation
1. Install the required package:
   ```
   pip install requests==2.31.0
   ```

## Usage
Run the script from the command line with the following arguments:

```
python iv_monitor.py --ticker <TICKER> --threshold-low <LOW_THRESHOLD> --threshold-high <HIGH_THRESHOLD> --api-key <API_KEY>
```

Example:
```
python iv_monitor.py --ticker AAPL --threshold-low 0.2 --threshold-high 0.8 --api-key YOUR_API_KEY
```

This will:
1. Fetch the current stock price for the ticker
2. Find the nearest options expiration date
3. Get the option chain for that expiration and identify the ATM call option
4. Fetch the IV for that option
5. Print the current IV and alert if it's below the low threshold or above the high threshold

## Configuration
The script is configured via command-line arguments. No configuration file is needed.

## Recommendations
- This script is designed to be run once per day, after market close, to capture the day's closing IV
- For more frequent monitoring, consider running the script during market hours, but note that IV may change rapidly
- The script uses the free tier of polygon.io, which has a rate limit of 5 requests per minute. Ensure you don't exceed this limit
- For production use, extend the alerting mechanism to send emails or webhook notifications
