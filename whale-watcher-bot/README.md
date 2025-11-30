# Whale Watcher Bot

An automated Python script to monitor specific Ethereum wallets for activity. It polls the blockchain via Etherscan and sends formatted alerts to a Discord channel via Webhooks.

## Problem Description
Users often need to track specific "Whale" wallets or their own cold storage for security and analysis. Manually refreshing block explorers is inefficient. This tool provides an automated, always-on solution that handles API rate limits and data decoding automatically.

## Solution Overview
- **Language:** Python 3
- **Data Source:** Etherscan API (Free Tier compatible)
- **Alerting:** Discord Webhooks (Push notifications)
- **Features:**
  - Monitors ETH transactions (Incoming/Outgoing).
  - Converts Wei to ETH automatically.
  - Filters small transactions via a threshold argument.
  - Respects API rate limits to prevent bans.
  - Robust error handling for network glitches.

## Prerequisites

1. **Python 3.8+** installed on your machine.
2. **Etherscan API Key**:
   - Sign up at [Etherscan.io](https://etherscan.io/register).
   - Create a free API key in your profile settings.
3. **Discord Webhook**:
   - Go to Server Settings -> Integrations -> Webhooks.
   - Create a new webhook and copy the URL.

## Installation

1. Download the source code.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line using arguments:

```bash
python whale_watcher.py --address <WALLET_ADDRESS> --apikey <ETHERSCAN_API_KEY> --webhook <DISCORD_WEBHOOK_URL>
```

### Optional Arguments
- `--threshold`: Minimum amount of ETH to trigger an alert (e.g., `0.5`). Default is 0.
- `--interval`: How often to check in seconds. Default is 60 (Recommended for free API tiers).

### Example Command
```bash
python whale_watcher.py --address 0xde0b295669a9fd93d5f28d9ec85e40f4cb697bae --apikey ABC123XYZ --webhook https://discord.com/api/webhooks/... --threshold 1.0
```

## Configuration & Recommendations
- **Rate Limits**: The free Etherscan API allows 5 calls per second. The default interval of 60 seconds is very safe. Do not lower below 5 seconds.
- **Hosting**: To keep this running 24/7, consider deploying it on a Raspberry Pi, a cheap VPS (DigitalOcean/Linode), or a cloud function.
- **Logs**: The script outputs logs to the console. You can redirect this to a file using `python whale_watcher.py ... > bot.log`.
