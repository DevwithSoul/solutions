# Cross-Exchange Arbitrage Alert

## Problem Description
Traders and developers often struggle to identify price discrepancies between cryptocurrency exchanges in real-time. The primary challenges are:
1.  **Latency:** REST APIs are too slow; WebSockets are required.
2.  **Data Normalization:** Every exchange sends data in a different JSON format.
3.  **Concurrency:** Handling multiple streams simultaneously without blocking.

## Solution Overview
This tool is a Python-based asynchronous monitor that connects to **Binance** and **Kraken** via WebSockets. It:
1.  Subscribes to real-time order book tickers (BTC/USDT).
2.  Normalizes the disparate data structures into a unified format.
3.  Calculates the spread between the highest Bid and lowest Ask across exchanges.
4.  Logs an alert immediately if the profit margin exceeds a user-defined threshold.

## Prerequisites
*   Python 3.8 or higher.
*   Internet connection (to reach Binance and Kraken public APIs).

## Installation

1.  **Unzip the tool**:
    ```bash
    unzip arbitrage-monitor-tool.zip
    cd arbitrage-monitor-tool
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script via the command line. By default, it looks for a 0.1% spread.

```bash
python arbitrage_monitor.py
```

### Custom Threshold
To change the alert sensitivity (e.g., alert only if spread > 0.5%):

```bash
python arbitrage_monitor.py --threshold 0.5
```

## Configuration
Currently, the script is hardcoded to monitor `BTC/USDT` (Bitcoin/Tether) as it is a high-liquidity pair available on almost all exchanges. 

*   **Binance Endpoint:** `wss://stream.binance.com:9443/ws/btcusdt@bookTicker`
*   **Kraken Endpoint:** `wss://ws.kraken.com` (Pair: `XBT/USDT`)

## Recommendations
For a full production deployment:
1.  **Execution:** Integrate with an execution API (like `ccxt`) to automatically place orders when an alert triggers.
2.  **Latency:** Host this script on a cloud server (AWS/GCP) located near the exchange servers (usually Tokyo or Ireland) for millisecond advantages.
3.  **Error Handling:** Add more robust network disconnection handling (exponential backoff) and alerting via Telegram/Discord webhooks.