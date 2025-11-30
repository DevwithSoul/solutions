# The 'Open Market' Insider Signal Bot

## Problem Description
Retail investors often struggle to interpret SEC Form 4 filings. While insider trading data is public, the raw feed is noisy, mixing routine stock option exercises (which often don't signal bullish sentiment) with meaningful "Open Market" purchases (where insiders spend their own cash to buy stock). Investors need a way to filter this noise and get alerted only when insiders make significant bets on their own companies.

## Solution Overview
This automated bot polls the SEC EDGAR RSS feed for the latest Form 4 filings. It parses the underlying XML documents to identify transaction codes. Specifically, it looks for **Code 'P'** (Open Market Purchase) and filters out derivative exercises (Code 'M') or grants (Code 'A' with no price). If the total purchase value exceeds a user-defined threshold, it sends a rich alert to a Discord or Slack webhook.

## Prerequisites
- **Python 3.8+**
- A **Discord Webhook URL** (optional, but recommended for alerts).
- An email address (required by SEC API Guidelines for the User-Agent header).

## Installation

1. Extract the zip file.
2. Open a terminal in the extracted folder.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line. You must provide your email address to comply with SEC fair access policies.

### Basic Example (Console Output Only)
```bash
python insider_signal_bot.py --email yourname@example.com
```

### Production Example (With Discord Alerts)
```bash
python insider_signal_bot.py --email yourname@example.com --webhook "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" --threshold 50000
```

### Arguments
- `--email` (Required): Your email address for the User-Agent header.
- `--webhook`: URL for Discord/Slack webhook. If omitted, alerts are printed to the console.
- `--threshold`: Minimum total purchase value to trigger an alert (default: $10,000).
- `--interval`: Seconds to wait between polling the SEC feed (default: 60).

## Configuration
No config files are needed; everything is handled via CLI arguments. 

**Note on SEC Rate Limits**: The SEC limits requests to ~10 per second. This bot includes a sleep interval (`--interval`) and processes filings sequentially to stay well within safe limits.

## Recommendations
- **Threshold**: Start with a lower threshold (e.g., $10,000) to verify functionality, then raise it (e.g., $100,000) to reduce noise.
- **Deployment**: This script is lightweight and can be run 24/7 on a Raspberry Pi, a refined AWS Lambda function (with modifications for statelessness), or a cheap VPS.