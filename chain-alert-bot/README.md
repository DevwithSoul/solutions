# Real-Time On-Chain Alert Bot

## Problem Description
In the fast-paced world of DeFi and NFTs, speed is everything. Traders and collectors often miss opportunities (like new crypto liquidity pools or stealth NFT mints) because they rely on slow manual monitoring or delayed third-party aggregators. Building a custom solution is difficult due to the complexity of handling WebSocket connections, decoding raw hex data from smart contracts, and managing asynchronous notification pipelines.

## Solution Overview
This tool is a specialized, production-ready automation bot written in Python. It connects directly to a blockchain node via WebSocket to listen for specific smart contract events in real-time. 

**Core Features:**
- **Real-Time Monitoring:** Uses `AsyncWeb3` to listen to the blockchain as blocks are produced.
- **Automatic Decoding:** Instantly converts raw blockchain event logs into human-readable data (e.g., Token Symbols).
- **Instant Alerts:** Pushes formatted notifications to Telegram immediately upon event detection.
- **Robustness:** Includes basic error handling and reconnection logic structure.

In this specific implementation, the bot monitors the **Uniswap V2 Factory** on the Ethereum network for the `PairCreated` event, alerting you whenever a new token pair is listed.

## Prerequisites
1. **Python 3.8+** installed.
2. **Telegram Bot:**
   - Create a bot via [@BotFather](https://t.me/BotFather) to get a `Bot Token`.
   - Get your `Chat ID` (you can use [@userinfobot](https://t.me/userinfobot)).
3. **Ethereum Node (WebSocket):**
   - You need a WSS URL (e.g., `wss://mainnet.infura.io/ws/v3/YOUR_KEY` or Alchemy).
   - Free tiers from Infura or Alchemy work for testing.

## Installation

1. **Unzip the tool:**
   ```bash
   unzip chain-alert-bot.zip
   cd chain-alert-bot
   ```

2. **Install Dependencies:**
   It is recommended to use a virtual environment.
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script via the command line by passing your credentials as arguments.

**Basic Command:**
```bash
python chain_alert_bot.py --rpc "wss://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY" --token "YOUR_TELEGRAM_BOT_TOKEN" --chat "YOUR_CHAT_ID"
```

**Example Output (Console):**
```text
2023-10-27 10:00:01 - INFO - Connecting to RPC: wss://...
2023-10-27 10:00:02 - INFO - Connected to Blockchain. Initializing Contract...
2023-10-27 10:00:02 - INFO - Listening for 'PairCreated' events... Press Ctrl+C to stop.
2023-10-27 10:05:15 - INFO - New Pair Detected: 0x...
2023-10-27 10:05:16 - INFO - Telegram notification sent successfully.
```

**Example Alert (Telegram):**
> 🚨 **New Liquidity Pool Detected** 🚨
> 
> **Pair:** WETH / PEPE
> **Address:** `0x1234...abcd`
> ...

## Configuration
- **Target Contract:** The script is pre-configured for Uniswap V2 Factory. To monitor a different contract (e.g., an NFT mint), modify `UNISWAP_V2_FACTORY_ADDRESS` and `FACTORY_ABI` in `chain_alert_bot.py`.
- **Network:** This works on any EVM-compatible chain (Ethereum, Binance Smart Chain, Polygon, Arbitrum) as long as you provide the correct WSS RPC URL and the contract address exists on that chain.

## Recommendations
- **Infrastructure:** For 24/7 uptime, run this script on a VPS (Virtual Private Server) using a process manager like `supervisor` or `Docker`.
- **Rate Limits:** Free RPC nodes have rate limits. If you receive connection errors, consider upgrading your node provider or increasing the `asyncio.sleep` interval in the code.