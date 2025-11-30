# Real-Time Insider Trading Alert Bot

This tool monitors the SEC EDGAR database in real-time for **Form 4** filings. It parses the raw XML data to distinguish "Open Market Purchases" (Transaction Code 'P') from other noises (like grants or options exercises). When a purchase exceeds your defined value threshold, it sends a rich notification to a Discord server.

## Features
- **Real-Time Monitoring**: Polls SEC RSS feeds every 60 seconds (configurable).
- **Smart Filtering**: Specifically looks for Transaction Code `P` (Open Market Buy).
- **Value Calculation**: Sums up total shares * price per share to filter out small trades.
- **Discord Integration**: Sends beautiful embedded alerts with Ticker, Owner, and Value.
- **Production Ready**: Includes error handling, logging, and user-agent compliance.

## Prerequisites
1. **Python 3.8+** installed.
2. **Discord Webhook URL** (if you want alerts sent to a channel).
   - Go to Discord Channel Settings -> Integrations -> Webhooks -> New Webhook.

## Installation

1. **Unzip the tool**:
   ```bash
   unzip sec-insider-bot-tool.zip
   cd sec-insider-bot-tool
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The SEC requires a strictly formatted `User-Agent` header to identify who is scraping their data. You must provide this.

### Basic Command
```bash
python sec_insider_bot.py --user-agent "John Doe johndoe@example.com" --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### Advanced Usage
Set a higher threshold ($50,000) and check every 30 seconds:
```bash
python sec_insider_bot.py \
  --user-agent "MyCompany admin@mycompany.com" \
  --webhook "https://discord.com/api/webhooks/..." \
  --threshold 50000 \
  --interval 30
```

### Dry Run (No Webhook)
If you just want to test parsing without sending alerts, omit the `--webhook` argument. The bot will print alerts to the console.
```bash
python sec_insider_bot.py --user-agent "TestBot test@test.com" --threshold 0
```

## Configuration Options

| Flag | Description | Default |
|------|-------------|---------|
| `--webhook` | Discord Webhook URL. | None (Console only) |
| `--threshold` | Minimum USD value to trigger alert. | 10000.0 |
| `--interval` | Seconds to wait between SEC feed checks. | 60 |
| `--user-agent` | **REQUIRED**. Format: `Name email`. | N/A |

## Important Notes
- **SEC Rate Limits**: The SEC limits requests to 10 per second. This bot sleeps between polls to stay well within limits.
- **First Run**: When you start the bot, it performs an initial fetch to mark existing filings as "seen" so you don't get spammed with old news. It will only alert on *new* filings that appear after the script starts.
