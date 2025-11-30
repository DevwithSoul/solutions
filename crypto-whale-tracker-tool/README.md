# Real-Time Crypto Whale Tracker Bot

This tool solves the problem of missing market-moving transactions by providing a low-latency, automated monitoring system. Instead of manually refreshing block explorers, this script tracks specific "Whale" wallets on the Ethereum blockchain (or any EVM-compatible chain) and pushes instant alerts to a Discord channel.

## Problem Description
Professional traders need to know when large holders (Whales) move funds to exchanges (potential sell-off) or to cold storage (accumulation). Manual tracking is impossible due to the speed of the blockchain. Existing tools are often expensive SaaS subscriptions. This tool provides a free, self-hosted alternative.

## Solution Overview
- **Language**: Python 3
- **Blockchain Interface**: Web3.py
- **Alerting**: Discord Webhooks
- **Mechanism**: Connects to an RPC node, polls for new blocks, iterates transactions, and filters based on a user-defined watchlist and value threshold.

## Prerequisites

1. **Python 3.8+** installed.
2. **RPC Node URL**: You need access to an Ethereum node. 
   - Free providers: [Alchemy](https://www.alchemy.com/), [Infura](https://www.infura.io/), or [QuickNode](https://www.quicknode.com/).
   - Example: `https://eth-mainnet.g.alchemy.com/v2/YOUR-API-KEY`
3. **Discord Webhook URL**:
   - Create a Discord Server -> Channel Settings -> Integrations -> Webhooks -> New Webhook -> Copy Webhook URL.

## Installation

1. Unzip the project folder.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line. You must provide your RPC URL, the wallets you want to watch, and your Discord Webhook URL.

### Basic Command
```bash
python crypto_whale_tracker.py --rpc "https://eth-mainnet..." --wallets "0xTargetWallet1,0xTargetWallet2" --webhook "https://discord.com/api/webhooks/..."
```

### With Value Threshold
Only alert if the transaction is greater than 5 ETH:
```bash
python crypto_whale_tracker.py --rpc "https://eth-mainnet..." --wallets "0xTargetWallet1" --webhook "https://discord..." --threshold 5.0
```

### Arguments
- `--rpc`: (Required) The HTTP URL of your blockchain node.
- `--wallets`: (Required) A comma-separated list of public addresses to watch.
- `--webhook`: (Required) Your Discord Webhook URL.
- `--threshold`: (Optional) Minimum amount of native currency (e.g., ETH) to trigger an alert. Default is 0.

## Configuration & Recommendations
- **Rate Limits**: If using a free RPC provider (like free Alchemy tier), the script includes a small `sleep` delay to prevent hitting rate limits. If you have a private node, you can reduce the sleep time in the code for faster alerts.
- **Chains**: This works on Ethereum Mainnet by default but works on **any EVM chain** (Binance Smart Chain, Polygon, Avalanche) if you provide the corresponding RPC URL.

## Disclaimer
This tool monitors native currency transfers (ETH). It does not decode internal contract transactions or ERC-20 token transfers (like USDT) without further modification to include contract ABIs.