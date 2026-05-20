# Polymarket Orderbook & Market Data Collector

Collect real-time and historical market data from Polymarket's CLOB API and subgraph.

## Problem

Reddit user [u/Ok-Hovercraft-3076](https://reddit.com/r/algotrading/comments/1tidjik/historical_polymarket_orderbook_data/) needs 2-3 years of historical orderbook depth data for Polymarket. Current vendors charge $39-249/month. This tool provides a free alternative.

## Features

- **List active markets** — Show all markets with token IDs and prices
- **Orderbook snapshots** — Take a single depth snapshot
- **Continuous collection** — Record orderbook data to CSV/JSONL at intervals
- **Trade history** — Fetch historical trades from the Polymarket subgraph (The Graph)

## Requirements

- Python 3.8+
- No external dependencies (uses urllib + json from stdlib)

## Usage

```
# List active markets with token IDs
python3 polymarket_orderbook_collector.py list

# Single orderbook snapshot
python3 polymarket_orderbook_collector.py snapshot TOKEN_ID

# Continuous collection (every 60 seconds)
python3 polymarket_orderbook_collector.py collect TOKEN_ID --interval 60

# Fetch trade history from subgraph
python3 polymarket_orderbook_collector.py history --limit 100

# Save trade history to CSV
python3 polymarket_orderbook_collector.py history --output trades.csv
```

## Output Format

### CSV (continuous collection)
```
timestamp,token_id,best_bid,best_ask,mid_price,spread,bid_volume,ask_volume,bid_count,ask_count
```

### JSONL (continuous collection)
Each line is a full orderbook snapshot with all bid/ask levels:
```json
{"timestamp": "...", "token_id": "...", "bids": [...], "asks": [...], "summary": {...}}
```

## API Used

- **CLOB API** — `GET /book?token_id=X` for orderbook depth
- **Subgraph (The Graph)** — Historical trades and market data
- No authentication required
