# Real-Time Crypto Whale Tracker

A lightweight, low-latency Python bot that monitors specific Ethereum wallets for activity and sends instant notifications to Telegram. This tool helps traders track "Whale" movements (large transactions) in real-time without relying on slow block explorers or spammy generic alert services.

## Problem Description
Traders often miss profitable opportunities because:
1. Standard block explorer alerts are delayed.
2. Email alerts get lost in spam folders.
3. Existing tools are expensive or overly complex to configure for specific addresses.

This tool solves these issues by polling the blockchain directly via API and pushing instant alerts to your phone.

## Solution Overview
- **Language:** Python 3
- **Data Source:** Etherscan API (Free Tier compatible)
- **Notification:** Telegram Bot API
- **Features:**
  - Monitors multiple wallets simultaneously.
  - Filters transactions by ETH value threshold.
  - Distinguishes between Incoming and Outgoing transactions.
  - Provides direct links to transaction hashes.

## Prerequisites
1. **Python 3.8+** installed on your machine.
2. **Etherscan API Key**: 
   - Sign up at [Etherscan.io](https://etherscan.io/apis).
   - Create a free API key.
3. **Telegram Bot**: 
   - Message `@BotFather` on Telegram to create a new bot and get the **Token**.
   - Message `@userinfobot` (or check bot updates) to get your personal **Chat ID**.

## Installation

1. Unzip the project folder.
2. Open a terminal/command prompt in the folder.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script via command line, passing your keys and the wallets you want to watch.

### Basic Example
```bash
python whale_tracker.py ^
  --etherscan_key "YOUR_ETHERSCAN_KEY" ^
  --telegram_token "YOUR_TELEGRAM_BOT_TOKEN" ^
  --chat_id "YOUR_CHAT_ID" ^
  --wallets "0xWalletAddress1,0xWalletAddress2"
```
*(Note: Use `\` instead of `^` for line breaks on Linux/macOS)*

### Advanced Example (Set Threshold & Interval)
To only alert on transactions larger than 5 ETH and check every 60 seconds:
```bash
python whale_tracker.py ^
  --etherscan_key "..." ^
  --telegram_token "..." ^
  --chat_id "..." ^
  --wallets "0xABC...,0x123..." ^
  --threshold 5.0 ^
  --interval 60
```

## Configuration Options

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--etherscan_key` | API Key from Etherscan | Required |
| `--telegram_token` | Token from BotFather | Required |
| `--chat_id` | Your numeric Telegram Chat ID | Required |
| `--wallets` | Comma-separated addresses | Required |
| `--threshold` | Min ETH amount to alert | `0.1` |
| `--interval` | Seconds between checks | `30` |

## Recommendations
- **API Limits**: The free Etherscan API allows 5 calls per second. If monitoring many wallets (10+), increase the `--interval` to avoid rate limiting.
- **Hosting**: For 24/7 uptime, run this script on a VPS (like AWS EC2, DigitalOcean) or a Raspberry Pi using `screen` or `tmux` to keep it running in the background.