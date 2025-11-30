# Real-Time Whale Watcher Bot

## Problem Description
Blockchain users often miss critical market movements because they cannot monitor specific addresses 24/7. Manually refreshing block explorers is inefficient, and raw blockchain data (integers in Wei) is difficult to read quickly. Users need an automated way to track "Whale" wallets and get instant notifications on their preferred communication platforms.

## Solution Overview
This Python automation script monitors an Ethereum address for new transactions using the Etherscan API. When a new transaction occurs:
1. It filters duplicates to ensure you only get notified once.
2. It converts raw blockchain values (Wei) into human-readable Ether.
3. It checks if the transaction value exceeds your defined threshold.
4. It sends a rich-text alert to a Discord channel via Webhooks.

## Prerequisites
1. **Python 3.8+** installed.
2. **Etherscan API Key**: 
   - Sign up at [Etherscan.io](https://etherscan.io/apis).
   - Create a free API key.
3. **Discord Webhook URL**:
   - Go to your Discord Server settings -> Integrations -> Webhooks.
   - Create a new webhook and copy the URL.

## Installation

1. Unzip the tool folder.
2. Open a terminal/command prompt in the folder.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line by passing the required arguments.

### Basic Command
```bash
python whale_watcher.py --address 0xYourTargetAddress --api-key YourEtherscanKey --webhook YourDiscordWebhookUrl
```

### Advanced Command (Custom Threshold & Interval)
To alert only on transactions larger than 5 ETH, checking every 30 seconds:
```bash
python whale_watcher.py --address 0xTargetAddress --api-key YourKey --webhook YourUrl --threshold 5.0 --interval 30
```

### Arguments
- `--address`: (Required) The Ethereum public address to watch.
- `--api-key`: (Required) Your Etherscan API key.
- `--webhook`: (Required) Your Discord Webhook URL.
- `--threshold`: (Optional) Minimum amount of ETH to trigger an alert (default: 0.1).
- `--interval`: (Optional) How often to check for new transactions in seconds (default: 60).

## Configuration & Recommendations
- **Rate Limits**: The free Etherscan API tier allows 5 calls per second. The default interval of 60 seconds is very safe. Do not lower the interval below 5 seconds.
- **Thresholds**: Set the threshold appropriately for the address you are watching. If watching an exchange wallet, set it high (e.g., 100 ETH) to avoid spam.

## Troubleshooting
- **403/401 Errors**: Check that your API key is correct.
- **No Alerts**: Ensure the address actually has *new* transactions occurring. The bot establishes a baseline on startup and only alerts on *future* transactions.