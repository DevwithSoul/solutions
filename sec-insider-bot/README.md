# Real-Time Insider Trading Alert System

This tool automates the monitoring of SEC Form 4 filings to detect significant open-market stock purchases by company insiders (CEOs, CFOs, Directors). It parses complex government XML data in real-time and filters for "Purchase" transaction codes, alerting you only when high-value trades occur.

## Problem Description
Traders often look for "Insider Buys" as a strong bullish signal. However, manually refreshing the SEC EDGAR database is inefficient. By the time a filing is noticed on news sites, the price may have already moved. This bot provides a programmatic edge by scraping the raw data immediately upon publication.

## Solution Overview
1. **Polling**: Monitors the SEC EDGAR RSS feed for new `Form 4` (Statement of Changes in Beneficial Ownership) filings.
2. **Parsing**: Fetches the raw XML document associated with the filing.
3. **Filtering**: specifically looks for Transaction Code `P` (Open Market Purchase). It ignores Grants (`A`) and Sales (`S`).
4. **Alerting**: Calculates the total value of the purchase. If it exceeds your defined threshold, it prints to the console and optionally sends a notification to a Discord/Slack webhook.

## Prerequisites
- Python 3.8+
- Internet connection

## Installation

1. Unzip the tool:
   ```bash
   unzip sec-insider-bot.zip
   cd sec-insider-bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The SEC requires a valid User-Agent string containing contact information (like an email address) to identify the scraper. **You must provide an email address.**

### Basic Run (Console Alerts Only)
```bash
python sec_insider_bot.py --email "yourname@example.com"
```

### With Discord Webhook & Custom Threshold
To receive alerts in a Discord channel, create a Webhook in your Discord Server settings and paste the URL here.

```bash
python sec_insider_bot.py --email "yourname@example.com" --webhook "https://discord.com/api/webhooks/xyz..." --threshold 50000
```

### Arguments
- `--email` (Required): Your email address for SEC compliance.
- `--webhook`: URL for Discord/Slack webhook notifications.
- `--threshold`: Minimum total purchase value ($) to trigger an alert. Default: $10,000.
- `--interval`: Seconds to wait between checking for new filings. Default: 60.

## Configuration
No config file is needed; all settings are passed via command-line arguments.

## Recommendations
- **Rate Limiting**: The bot includes sleep timers to respect SEC rate limits (max 10 requests/sec). Do not remove these sleeps, or your IP will be banned by the SEC.
- **Threshold**: Set a reasonable threshold (e.g., $10k or $50k) to avoid noise from small token purchases.
- **Deployment**: For 24/7 monitoring, run this script on a VPS (AWS EC2, DigitalOcean) using `screen` or `systemd`.
