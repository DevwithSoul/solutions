# Real-Time Crypto Whale Tracker

## Problem Description
Traders and analysts often struggle to identify significant market movements ("Whale" activity) in real-time due to the complexity of decoding raw blockchain data and the latency introduced by standard API rate limits. Missing these large transactions means missing critical copy-trading or risk-management opportunities.

## Solution Overview
This tool is a lightweight, low-latency Python bot that connects directly to an Ethereum node via `web3.py`. It monitors every new block, filters transactions based on a user-defined ETH value threshold, and instantly delivers formatted alerts to a Telegram channel or user. 

### Key Features:
- **Direct Node Connection:** Bypasses 3rd party tracker APIs for lower latency.
- **Smart Filtering:** Detects native ETH transfers and identifies basic Smart Contract interactions.
- **Instant Alerts:** Pushes notifications to Telegram immediately upon block processing.
- **Configurable:** Adjustable thresholds and polling intervals.

## Prerequisites

1. **Python 3.8+** installed.
2. **Ethereum RPC URL:** You need access to an Ethereum node. 
   - Free providers: [Infura](https://infura.io/), [Alchemy](https://www.alchemy.com/), or public endpoints like `https://cloudflare-eth.com` (Note: Public endpoints have strict rate limits).
3. **Telegram Bot (Optional but recommended):**
   - Create a bot via [@BotFather](https://t.me/botfather) to get a Token.
   - Get your Chat ID via [@userinfobot](https://t.me/userinfobot).

## Installation

1. Download and unzip the tool.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line. You must provide an RPC URL.

### Basic Example (Console Logging only)
```bash
python crypto_whale_tracker.py --rpc https://cloudflare-eth.com --threshold 50
```

### Full Example (With Telegram Alerts)
```bash
python crypto_whale_tracker.py \
  --rpc https://mainnet.infura.io/v3/YOUR_INFURA_KEY \
  --threshold 10 \
  --telegram-token "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" \
  --chat-id "123456789"
```

### Arguments
- `--rpc`: (Required) The HTTP URL of the Ethereum Node.
- `--threshold`: (Optional) Minimum ETH amount to trigger an alert (Default: 10).
- `--telegram-token`: (Optional) Your Bot API Token.
- `--chat-id`: (Optional) Your Telegram Chat ID.
- `--interval`: (Optional) Seconds to wait between checking for new blocks (Default: 10).

## Configuration & Recommendations
- **Rate Limits:** If using a free public RPC (like Cloudflare), set `--interval` to at least 10 seconds to avoid being blocked.
- **Production:** For true low-latency trading, use a paid private node (Alchemy/QuickNode) and reduce the interval or switch the code to use WebSockets (requires minor code refactoring).
