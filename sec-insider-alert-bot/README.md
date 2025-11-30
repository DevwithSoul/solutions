# Real-Time Insider Trading Alert Bot

This tool automates the monitoring of SEC Form 4 filings to identify genuine "Open Market Purchases" by company insiders. It filters out noise (like stock grants or option exercises) by specifically looking for Transaction Code 'P' in the raw XML data of the filings. When a purchase exceeds your defined threshold, it sends a rich notification to Discord.

## Problem Description
Traders often look for insider buying as a bullish signal. However, the SEC EDGAR feed is flooded with Form 4 filings that represent routine stock grants, tax withholdings, or option exercises, which are not necessarily bullish signals. Manually filtering these in real-time is impossible.

## Solution Overview
1. **Monitors** the SEC EDGAR Atom feed for the latest Form 4 filings.
2. **Scrapes** the filing detail page to locate the machine-readable XML document.
3. **Parses** the XML to find transactions marked with Code 'P' (Open Market Purchase).
4. **Calculates** the total value of the purchase (Shares * Price).
5. **Alerts** via Discord Webhook if the value exceeds the user-defined threshold.

## Prerequisites
- Python 3.8+
- A Discord Server (to create a Webhook URL).

## Installation

1. **Unzip the tool**:
   ```bash
   unzip sec-insider-alert-bot.zip
   cd sec-insider-alert-bot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line. You must provide a Discord Webhook URL.

### Basic Usage
```bash
python insider_trading_bot.py --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### Advanced Usage
Customize the threshold, check interval, and User-Agent.

```bash
python insider_trading_bot.py \
  --webhook "YOUR_DISCORD_WEBHOOK_URL" \
  --threshold 50000 \
  --interval 120 \
  --user-agent "MyTradingBot/1.0 (myname@example.com)"
```

**Note on User-Agent:** The SEC requires a User-Agent header that identifies your application and includes a contact email. If you do not provide one, the script uses a default placeholder, but for long-term usage, please use your own to avoid IP bans.

## Configuration Options

| Flag | Description | Default |
|------|-------------|---------|
| `--webhook` | **Required**. The Discord Webhook URL. | N/A |
| `--threshold` | Min transaction value ($) to trigger alert. | 10000.0 |
| `--interval` | Seconds to wait between RSS feed checks. | 60 |
| `--user-agent` | Identification string for SEC requests. | `InsiderBot...` |

## Recommendations
- **Thresholds:** Start with a lower threshold (e.g., $10,000) to verify it works, then raise it (e.g., $100,000+) to reduce noise.
- **Rate Limiting:** The SEC allows up to 10 requests per second. This bot sleeps between requests to stay well within safe limits.
- **Hosting:** Can be run on a Raspberry Pi, AWS EC2 free tier, or a local desktop background terminal.
