# Polymarket Wallet Monitor

Track and monitor Polymarket wallets in real time. Scrapes Polymarket profile activity pages to show trades, positions, and wallet stats.

## Problem

Reddit user [u/paintwithletters](https://reddit.com/r/webscraping/comments/1tiqiw5/i_need_help/) and others on r/algotrading need tools to:
- Monitor Polymarket "smart" wallets for copy trading
- Track wallet activity without CLOB API credentials
- Get alerts when a wallet makes new trades

## Features

- **Single wallet scan** — Show all recent trades for a Polymarket user
- **Multi-wallet batch scan** — Scan multiple wallets with consensus analysis
- **Monitor mode** — Watch a wallet continuously and alert on new trades
- **ETH address support** — Detects invalid addresses and suggests alternatives

## Requirements

- Python 3.8+
- Playwright (`pip install playwright`)
- Playwright browsers: `playwright install chromium`

## Usage

```
# Scan a wallet by username
python3 polymarket_wallet_monitor.py ca6859f3c004bff161e3328d27ddba6c

# Batch scan from file
python3 polymarket_wallet_monitor.py --file wallets.txt

# Monitor mode — watch for new trades every 30 seconds
python3 polymarket_wallet_monitor.py ca6859f3c004bff161e3328d27ddba6c --monitor --interval 30

# Scan multiple wallets and show consensus
python3 polymarket_wallet_monitor.py --file winners.txt
```

## Wallet File Format

One wallet per line — username or URL:
```
ca6859f3c004bff161e3328d27ddba6c
https://polymarket.com/@CRYINGLITTLEBABY?tab=activity
```

## API Used

- **Polymarket.com profile pages** (scraped via Playwright)
- No CLOB API key or authentication required
- No blockchain RPC needed
