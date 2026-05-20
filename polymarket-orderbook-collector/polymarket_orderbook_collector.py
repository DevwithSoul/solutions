#!/usr/bin/env python3
"""
Polymarket Orderbook & Market Data Collector

Collects real-time and historical market data from Polymarket's CLOB API.
Records orderbook snapshots, price changes, and trade data for analysis.

Uses the Polymarket subgraph (The Graph) and CLOB API for data collection.

Usage:
    python3 polymarket_orderbook_collector.py list                    # List active markets
    python3 polymarket_orderbook_collector.py snapshot <token_id>     # Single orderbook snapshot
    python3 polymarket_orderbook_collector.py collect <token_id>      # Collect data continuously
    python3 polymarket_orderbook_collector.py history <token_id>      # Fetch trade history from subgraph

Examples:
    python3 polymarket_orderbook_collector.py list
    python3 polymarket_orderbook_collector.py snapshot 36161990524808999529099890841186860907449767867066339846328156147773282747583
    python3 polymarket_orderbook_collector.py collect 36161990524808999529099890841186860907449767867066339846328156147773282747583 --interval 60
    python3 polymarket_orderbook_collector.py history 36161990524808999529099890841186860907449767867066339846328156147773282747583 --output trades.csv
"""

import json
import csv
import sys
import os
import time
import argparse
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


# ============================================================
# Configuration
# ============================================================
CLOB_API = "https://clob.polymarket.com"
SUBGRAPH_API = "https://api.thegraph.com/subgraphs/name/polymarket/matic-main"
POLYGONSCAN_API = "https://api.polygonscan.com/api"
USER_AGENT = "PolymarketDataCollector/1.0"
DEFAULT_INTERVAL = 60  # seconds between snapshots
MAX_RETRIES = 3


# ============================================================
# API Helpers
# ============================================================
def api_get(url, headers=None):
    """Generic API GET with retry logic."""
    if headers is None:
        headers = {"User-Agent": USER_AGENT}
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            last_error = e
            body = e.read().decode()[:200] if e.fp else ""
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
            else:
                return {"error": f"HTTP {e.code}: {body}"}
        except URLError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
            else:
                return {"error": str(e)}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}"}
    
    return {"error": str(last_error)}


def subgraph_query(query):
    """Execute a GraphQL query against the Polymarket subgraph."""
    data = json.dumps({"query": query}).encode()
    req = Request(SUBGRAPH_API, data=data, 
                  headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
            if "errors" in result:
                return {"error": result["errors"][0].get("message", "Subgraph error")}
            return result.get("data", {})
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# Market Listing
# ============================================================
def list_active_markets(limit=20):
    """Fetch and display active Polymarket markets."""
    url = f"{CLOB_API}/markets?limit={limit}&closed=false"
    result = api_get(url)
    
    if "error" in result:
        print(f"❌ API Error: {result['error']}")
        return []
    
    # Handle nested response
    items = result if isinstance(result, list) else result.get("data", [])
    
    if not items:
        print("ℹ  No markets found. The API may require different parameters.")
        # Try without closed filter
        url = f"{CLOB_API}/markets?limit={limit}"
        result = api_get(url)
        items = result if isinstance(result, list) else result.get("data", [])
    
    print(f"\n  Polymarket Active Markets")
    print(f"  {'=' * 70}")
    print(f"  {'#':<4} {'Market Question':<50} {'Tokens':>6} {'Orders':>8}")
    print(f"  {'─' * 70}")
    
    for i, m in enumerate(items[:limit]):
        question = m.get("question", "?")[:48]
        accepting = "✓" if m.get("accepting_orders") else "✗"
        tokens = len(m.get("tokens", []))
        ob = "✓" if m.get("enable_order_book") else "✗"
        print(f"  {i+1:<4} {question:<50} {tokens:>6} {ob:>8}")
        
        # Show tokens/outcomes
        for t in m.get("tokens", []):
            tid = t.get("token_id", "?")[:20]
            outcome = t.get("outcome", "?")[:35]
            price = t.get("price", "?")
            print(f"       Token: {tid}... | {outcome:<35} | Price: {price}")
    
    print(f"\n  Tip: Use the token_id with the 'snapshot' or 'collect' command\n")
    
    # Extract and return token IDs
    token_ids = []
    for m in items[:limit]:
        for t in m.get("tokens", []):
            tid = t.get("token_id")
            if tid:
                token_ids.append(tid)
    return token_ids


# ============================================================
# Orderbook Snapshot
# ============================================================
def get_orderbook(token_id):
    """Fetch orderbook for a given token_id from CLOB API."""
    url = f"{CLOB_API}/book?token_id={token_id}"
    result = api_get(url)
    
    if "error" in result:
        return result
    
    return result


def display_orderbook(token_id, book):
    """Display orderbook in a clean format."""
    if "error" in book:
        print(f"\n  ❌ No orderbook for token {token_id[:20]}...")
        print(f"     Error: {book['error']}")
        return
    
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    
    print(f"\n  Orderbook — Token {token_id[:20]}...")
    print(f"  {'=' * 50}")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Bids: {len(bids)} | Asks: {len(asks)}")
    
    if bids:
        print(f"\n  BIDS (BUY)")
        print(f"  {'─' * 40}")
        print(f"  {'Price':<12} {'Size':<12} {'Total':<12}")
        print(f"  {'─' * 40}")
        for b in bids[:10]:
            price = b.get("price", "?")
            size = b.get("size", "?")
            total = float(price) * float(size) if price != "?" and size != "?" else "?"
            total_str = f"{total:.2f}" if total != "?" else "?"
            print(f"  {str(price):<12} {str(size):<12} {total_str:<12}")
    
    if asks:
        print(f"\n  ASKS (SELL)")
        print(f"  {'─' * 40}")
        print(f"  {'Price':<12} {'Size':<12} {'Total':<12}")
        print(f"  {'─' * 40}")
        for a in asks[:10]:
            price = a.get("price", "?")
            size = a.get("size", "?")
            total = float(price) * float(size) if price != "?" and size != "?" else "?"
            total_str = f"{total:.2f}" if total != "?" else "?"
            print(f"  {str(price):<12} {str(size):<12} {total_str:<12}")
    
    # Spread
    if bids and asks:
        best_bid = float(bids[0].get("price", 0))
        best_ask = float(asks[0].get("price", 0))
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid) * 100 if best_bid > 0 else 0
        print(f"\n  Spread: {spread:.4f} ({spread_pct:.2f}%)")
    
    print()


# ============================================================
# Data Collection (continuous)
# ============================================================
def collect_orderbook_data(token_id, interval, output_dir):
    """Continuously collect orderbook snapshots."""
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, f"orderbook_{token_id[:20]}.csv")
    json_path = os.path.join(output_dir, f"snapshots_{token_id[:20]}.jsonl")
    
    # Check if CSV exists and has header
    csv_exists = os.path.exists(csv_path)
    
    print(f"\n  📊 Collecting orderbook data for token {token_id[:20]}...")
    print(f"  Interval: {interval}s | Output: {output_dir}/")
    print(f"  Press Ctrl+C to stop\n")
    
    try:
        while True:
            timestamp = datetime.now()
            ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            ts_epoch = timestamp.timestamp()
            
            # Fetch orderbook
            book = get_orderbook(token_id)
            
            if "error" not in book:
                bids = book.get("bids", [])
                asks = book.get("asks", [])
                
                # Calculate summary
                best_bid = float(bids[0]["price"]) if bids else 0
                best_ask = float(asks[0]["price"]) if asks else 0
                mid_price = (best_bid + best_ask) / 2 if (best_bid and best_ask) else 0
                bid_volume = sum(float(b.get("size", 0)) for b in bids)
                ask_volume = sum(float(a.get("size", 0)) for a in asks)
                
                # Append to CSV
                with open(csv_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    if not csv_exists:
                        writer.writerow(["timestamp", "token_id", "best_bid", "best_ask", 
                                       "mid_price", "spread", "bid_volume", "ask_volume", 
                                       "bid_count", "ask_count"])
                        csv_exists = True
                    writer.writerow([ts_str, token_id, best_bid, best_ask, mid_price, 
                                   best_ask - best_bid, bid_volume, ask_volume,
                                   len(bids), len(asks)])
                
                # Append full snapshot to JSONL
                with open(json_path, "a") as f:
                    snapshot = {
                        "timestamp": ts_str,
                        "timestamp_epoch": ts_epoch,
                        "token_id": token_id,
                        "bids": bids,
                        "asks": asks,
                        "summary": {
                            "best_bid": best_bid,
                            "best_ask": best_ask,
                            "mid_price": mid_price,
                            "spread": best_ask - best_bid,
                            "bid_volume": bid_volume,
                            "ask_volume": ask_volume
                        }
                    }
                    f.write(json.dumps(snapshot) + "\n")
                
                print(f"  [{ts_str}] ✓ {len(bids)} bids × {len(asks)} asks | "
                      f"mid={mid_price:.4f} | spread={best_ask-best_bid:.4f}")
            else:
                print(f"  [{ts_str}] ⚠ No orderbook data: {book.get('error', 'unknown')}")
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"\n\n  🛑 Collection stopped")
        print(f"  CSV: {csv_path}")
        print(f"  JSONL: {json_path}")
        print(f"  Total records: {sum(1 for _ in open(csv_path)) - 1 if os.path.exists(csv_path) else 0}\n")


# ============================================================
# Trade History (from Subgraph)
# ============================================================
def fetch_trade_history(token_id=None, limit=50):
    """Fetch historical trades from the Polymarket subgraph."""
    query = """
    {
      trades(first: %d%s) {
        id
        type
        price
        size
        timestamp
        transaction {
          id
        }
        market {
          question
        }
      }
    }
    """ % (limit, f', where: {{market: "{token_id}"}}' if token_id else "")
    
    result = subgraph_query(query)
    
    if "error" in result:
        print(f"❌ Subgraph error: {result['error']}")
        return []
    
    trades = result.get("trades", [])
    return trades


def display_trades(trades, output=None):
    """Display or save trade history."""
    if not trades:
        print("  ℹ  No trades found")
        return
    
    print(f"\n  Trade History ({len(trades)} trades)")
    print(f"  {'=' * 70}")
    print(f"  {'Type':<6} {'Price':<10} {'Size':<10} {'Timestamp':<20} {'Market':<30}")
    print(f"  {'─' * 70}")
    
    for t in trades[:20]:
        ttype = t.get("type", "?")[:5]
        price = t.get("price", "?")
        size = t.get("size", "?")
        ts = datetime.fromtimestamp(int(t.get("timestamp", 0))).strftime("%Y-%m-%d %H:%M") if t.get("timestamp") else "?"
        market = t.get("market", {}).get("question", "?")[:28]
        print(f"  {ttype:<6} {str(price):<10} {str(size):<10} {ts:<20} {market:<30}")
    
    # Save to CSV if requested
    if output:
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "type", "price", "size", "timestamp", "tx_hash", "market"])
            for t in trades:
                writer.writerow([
                    t.get("id", ""),
                    t.get("type", ""),
                    t.get("price", ""),
                    t.get("size", ""),
                    datetime.fromtimestamp(int(t.get("timestamp", 0))).strftime("%Y-%m-%d %H:%M:%S") if t.get("timestamp") else "",
                    t.get("transaction", {}).get("id", ""),
                    t.get("market", {}).get("question", "")
                ])
        print(f"\n  💾 Saved to {output}")
    
    print()


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Orderbook & Market Data Collector",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  list                   List active markets with token IDs
  snapshot <token_id>    Take a single orderbook snapshot
  collect <token_id>     Continuously collect orderbook data
  history <token_id>     Fetch historical trades from subgraph

Examples:
  python3 polymarket_orderbook_collector.py list
  python3 polymarket_orderbook_collector.py snapshot TOKEN_ID
  python3 polymarket_orderbook_collector.py collect TOKEN_ID --interval 60
  python3 polymarket_orderbook_collector.py history TOKEN_ID --output trades.csv
        """
    )
    parser.add_argument("command", nargs="?", help="Command: list, snapshot, collect, history")
    parser.add_argument("token_id", nargs="?", help="Token ID from the market")
    parser.add_argument("--interval", "-i", type=int, default=DEFAULT_INTERVAL,
                        help=f"Collection interval in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--output", "-o", help="Output file for trades CSV")
    parser.add_argument("--dir", "-d", default="orderbook_data",
                        help="Output directory for collected data")
    parser.add_argument("--limit", "-l", type=int, default=50,
                        help="Limit for listings/queries (default: 50)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "list":
        list_active_markets(args.limit)
    
    elif args.command == "snapshot":
        if not args.token_id:
            print("❌ Please provide a token_id. Use 'list' to find one.")
            sys.exit(1)
        book = get_orderbook(args.token_id)
        display_orderbook(args.token_id, book)
    
    elif args.command == "collect":
        if not args.token_id:
            print("❌ Please provide a token_id. Use 'list' to find one.")
            sys.exit(1)
        collect_orderbook_data(args.token_id, args.interval, args.dir)
    
    elif args.command == "history":
        trades = fetch_trade_history(args.token_id, args.limit)
        display_trades(trades, args.output)
    
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
