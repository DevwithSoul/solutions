# Automated Multi-Ticker RSI Alert System

## Problem Description

Monitoring multiple financial instruments manually for technical indicators like RSI (Relative Strength Index) across different timeframes is time-consuming and inefficient. Traders need an automated system that can:

- Scan multiple tickers simultaneously
- Calculate RSI on 5-minute interval data
- Detect overbought/oversold conditions
- Send instant notifications via Discord
- Respect API rate limits

This system eliminates the need for constant manual monitoring and provides real-time alerts when trading opportunities arise.

## Solution Overview

This Python-based automation tool:

1. **Fetches 5-minute OHLCV data** from Yahoo Finance for multiple tickers
2. **Calculates RSI** using the standard 14-period formula
3. **Detects conditions**: overbought (RSI > 70), oversold (RSI < 30), and RSI crossovers
4. **Sends formatted Discord notifications** with embeds containing RSI values and alert types
5. **Manages rate limits** with configurable delays between API calls
6. **Runs continuously** with configurable scan intervals

## Prerequisites

- Python 3.7+
- Discord server with webhook integration
- No paid API keys required (uses free Yahoo Finance data)

## Installation

1. Clone or download the project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Get a Discord webhook URL:
   - Go to your Discord server
   - Navigate to Server Settings > Integrations > Webhooks
   - Create a new webhook
   - Copy the webhook URL

## Usage

### Basic Usage

```bash
python rsi_alert_system.py --tickers AAPL,GOOGL,MSFT --webhook YOUR_DISCORD_WEBHOOK_URL
```

### Advanced Usage

```bash
python rsi_alert_system.py \
  --tickers AAPL,GOOGL,MSFT,TSLA,AMZN \
  --webhook https://discord.com/api/webhooks/xxx/yyy \
  --period 14 \
  --overbought 70 \
  --oversold 30 \
  --interval 300
```

### Command Line Arguments

- `--tickers`: Comma-separated list of ticker symbols (required)
- `--webhook`: Discord webhook URL (required)
- `--period`: RSI calculation period (default: 14)
- `--overbought`: Overbought threshold (default: 70)
- `--oversold`: Oversold threshold (default: 30)
- `--interval`: Scan interval in seconds (default: 300)

## Configuration

### Discord Webhook Setup

1. Open Discord and go to your server
2. Click the dropdown next to the server name
3. Select "Server Settings"
4. Click "Integrations" in the left sidebar
5. Click "Webhooks"
6. Click "New Webhook"
7. Name it "RSI Alerts" and choose a channel
8. Click "Copy Webhook URL"

### Supported Tickers

The system uses Yahoo Finance ticker symbols:
- Stocks: AAPL, GOOGL, MSFT, TSLA
- Crypto: BTC-USD, ETH-USD, SOL-USD
- Forex: EURUSD=X, GBPUSD=X
- ETFs: SPY, QQQ, IWM

### RSI Parameters

- **Period**: Typically 14 (default)
- **Overbought**: 70 (default) - RSI above this suggests overvaluation
- **Oversold**: 30 (default) - RSI below this suggests undervaluation

## Recommendations

1. **Start with fewer tickers** (3-5) to test the system
2. **Set scan interval to 300 seconds** (5 minutes) initially
3. **Monitor Discord channel** for alert frequency
4. **Adjust RSI thresholds** based on your trading strategy
5. **Run on a VPS or always-on computer** for continuous monitoring
6. **Use rate limiting wisely** - don't scan too frequently

## Troubleshooting

- **No data received**: Check ticker symbols are correct
- **Discord alerts not sending**: Verify webhook URL is correct and webhook hasn't been deleted
- **Rate limit errors**: Increase scan interval or add more delay between ticker requests
- **Empty data**: Some tickers may not have 5-minute data available

## Disclaimer

This tool is for educational and informational purposes only. Always do your own research before making trading decisions.
