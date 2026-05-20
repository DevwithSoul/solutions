#!/usr/bin/env python3
"""
Polymarket Wallet Monitor — Track and monitor Polymarket wallets in real-time.

Monitors Polymarket profile pages for new trades, shows wallet statistics,
and can send alerts when new activity is detected.

Usage:
    python3 polymarket_wallet_monitor.py <wallet_address_or_username>
    python3 polymarket_wallet_monitor.py <wallet> --monitor    # Watch for new trades
    python3 polymarket_wallet_monitor.py --file wallets.txt     # Batch check multiple wallets

Examples:
    python3 polymarket_wallet_monitor.py ca6859f3c004bff161e3328d27ddba6c
    python3 polymarket_wallet_monitor.py 0x7f69983eb28245bba0d5083502a78744a8f66162
    python3 polymarket_wallet_monitor.py ca6859f3c... --monitor --interval 30
"""

import asyncio
import json
import sys
import os
import time
import argparse
from datetime import datetime
from collections import defaultdict
from playwright.async_api import async_playwright


# ============================================================
# Configuration
# ============================================================
MONITOR_DEFAULT_INTERVAL = 20  # seconds between checks in monitor mode
MAX_CONCURRENT = 3
TIMEOUT = 30000
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


# ============================================================
# Data Extraction
# ============================================================
def extract_wallet_username(url_or_address):
    """Extract username from a Polymarket URL or address."""
    url_or_address = url_or_address.strip()
    if url_or_address.startswith("http"):
        # Full URL
        if "@" in url_or_address:
            user = url_or_address.split("@")[1].split("?")[0].split("/")[0]
        elif "profile/" in url_or_address:
            user = url_or_address.split("profile/")[1].split("?")[0].split("/")[0]
            if user.startswith("%40"):
                user = user[3:]
            elif user.startswith("@"):
                user = user[1:]
        else:
            return None
        return user
    elif url_or_address.startswith("0x"):
        # Ethereum address — use as-is
        return url_or_address
    else:
        # Plain username
        return url_or_address


def build_profile_url(username):
    """Build the Polymarket profile activity URL.
    
    ETH addresses don't have direct profile pages on Polymarket.
    Use Polygonscan instead to find Polymarket-related transactions.
    """
    if username.startswith("0x"):
        # Polymarket doesn't have profile pages for raw addresses
        # Return the URL but we'll check for 404 and suggest alternative
        return f"https://polymarket.com/address/{username}?tab=activity"
    return f"https://polymarket.com/@{username}?tab=activity"


async def scrape_wallet(browser, username, verbose=True):
    """
    Scrape a single Polymarket wallet's activity page.
    Returns: dict with wallet stats and list of trades
    """
    url = build_profile_url(username)
    page = await browser.new_page()
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT)
        await asyncio.sleep(4)  # Wait for JS to render
        
        # Check for 404 page
        try:
            title = await page.title()
            page_text = await page.inner_text("body")
            if "404" in page_text and "could not be found" in page_text:
                if verbose:
                    print(f"  ✗ {username}: Profile page not found "
                          f"(Polymarket doesn't have a page for this address)")
                    if username.startswith("0x"):
                        print(f"    💡 Use a Polymarket @username instead, or check if this "
                              f"address has interacted with Polymarket")
                return username, {}, []
        except Exception:
            pass
        
        # Extract wallet stats from the profile header
        stats = {}
        try:
            text = await page.inner_text("body")
            lines = text.split("\n")
            
            # Parse wallet stats from the text dump
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check upcoming lines for values
                if line_stripped == "Positions Value" and i + 1 < len(lines):
                    stats["positions_value"] = lines[i + 1].strip()
                elif line_stripped == "Biggest Win" and i + 1 < len(lines):
                    stats["biggest_win"] = lines[i + 1].strip()
                elif line_stripped == "Predictions" and i + 1 < len(lines):
                    stats["predictions"] = lines[i + 1].strip()
                elif "Profit/Loss" in line_stripped:
                    # The value might be on same line after tab text
                    pass
                elif line_stripped.startswith("$") and i > 0:
                    prev = lines[i - 1].strip() if i > 0 else ""
                    if prev == "":
                        # Maybe a standalone value
                        if "positions_value" not in stats:
                            stats["positions_value"] = line_stripped
        except Exception:
            pass
        
        # Try to extract stats more precisely using selectors
        try:
            # Look for the profile stat values in the header
            profile_header = page.locator("div.flex.flex-col.gap-2").first
            if profile_header:
                pass  # The text parsing above works well enough
        except Exception:
            pass
        
        # Extract trades from the activity table
        trades = []
        try:
            # Find all activity rows
            rows = await page.locator("div.px-4.py-3.rounded-lg").all()
            
            for row in rows:
                try:
                    trade_data = {}
                    
                    # TYPE (Buy / Sell / Redeem)
                    type_el = row.locator("p.text-sm.font-medium").first
                    trade_data["type"] = (await type_el.inner_text()).strip()
                    
                    # MARKET name
                    market_el = row.locator("a[href*='/event/'] h2").first
                    trade_data["market"] = (await market_el.inner_text()).strip()
                    
                    # SHARES
                    shares_el = row.locator("span:has-text('shares')").first
                    trade_data["shares"] = (await shares_el.inner_text()).strip()
                    
                    # VALUE ($ amount)
                    value_el = row.locator("p.text-sm.font-medium.text-right").first
                    trade_data["value"] = (await value_el.inner_text()).strip()
                    
                    # TIME — the text before polygonscan link
                    time_el = row.locator("a[href*='polygonscan']").first
                    time_text = (await time_el.inner_text()).strip()
                    # Remove SVG icon text that might be mixed in
                    time_text = time_text.replace("mo ago", "mo ago").replace("yr ago", "yr ago")
                    time_text = time_text.replace("d ago", "d ago").replace("h ago", "h ago")
                    time_text = time_text.replace("m ago", "m ago").replace("s ago", "s ago")
                    # Just grab first meaningful word group
                    time_parts = time_text.split()
                    if time_parts:
                        trade_data["time"] = " ".join(time_parts[:3])
                    else:
                        trade_data["time"] = time_text
                    
                    # TX hash from polygonscan link
                    tx_href = await time_el.get_attribute("href")
                    if tx_href and "/tx/" in tx_href:
                        trade_data["tx"] = tx_href.split("/tx/")[1].split("?")[0]
                    
                    trades.append(trade_data)
                    
                except Exception as e:
                    if verbose:
                        print(f"    ⚠ Skipped a row: {e}")
                    continue
                    
        except Exception as e:
            if verbose:
                print(f"    ⚠ Could not extract trades: {e}")
        
        if verbose and trades:
            print(f"  ✓ {username}: {len(trades)} trades found")
        elif verbose:
            print(f"  ✓ {username}: Scraped (no trade rows found)")
        
        return username, stats, trades
    
    except Exception as e:
        if verbose:
            print(f"  ✗ {username}: Failed — {e}")
        return username, {}, []
    
    finally:
        await page.close()


# ============================================================
# Display
# ============================================================
def display_wallet(username, stats, trades):
    """Display wallet information in a clean format."""
    print()
    print(f"  {'=' * 60}")
    print(f"  📊  @{username}")
    print(f"  {'=' * 60}")
    
    # Stats
    if stats:
        print(f"     Positions Value : {stats.get('positions_value', 'N/A')}")
        print(f"     Biggest Win     : {stats.get('biggest_win', 'N/A')}")
        print(f"     Predictions     : {stats.get('predictions', 'N/A')}")
    
    # Trades
    if trades:
        print(f"  {'─' * 60}")
        print(f"     Recent Activity ({len(trades)} trades)")
        print(f"  {'─' * 60}")
        for t in trades[:10]:  # Show last 10 trades
            market_short = t.get("market", "?")[:40]
            print(f"     [{t.get('type', '?').upper():>6}] {market_short:<40}")
            print(f"             Shares: {t.get('shares', '?'):<12} Value: {t.get('value', '?'):<10} Time: {t.get('time', '?')}")
    else:
        print(f"     ℹ  No recent trades found")
        print(f"     Try a different wallet or check if the wallet has activity")


def display_multi_wallet(results):
    """Display results from multiple wallets."""
    print(f"\n{'=' * 70}")
    print(f"  📊 POLYMARKET WALLET SCAN RESULTS")
    print(f"{'=' * 70}")
    
    for username, stats, trades in results:
        display_wallet(username, stats, trades)
    
    # Consensus analysis if multiple wallets
    if len(results) > 1:
        print(f"\n{'=' * 70}")
        print(f"  🔍 CONSENSUS ANALYSIS ({len(results)} wallets)")
        print(f"{'=' * 70}")
        
        market_consensus = defaultdict(lambda: {"buy": 0, "sell": 0})
        for username, _, trades in results:
            for t in trades:
                market = t.get("market", "Unknown")
                ttype = t.get("type", "").upper()
                if "BUY" in ttype:
                    market_consensus[market]["buy"] += 1
                elif "SELL" in ttype:
                    market_consensus[market]["sell"] += 1
        
        if market_consensus:
            print(f"  {'Market':<45} {'Buy':>6} {'Sell':>6}")
            print(f"  {'─' * 60}")
            for market, data in sorted(market_consensus.items(), 
                                      key=lambda x: x[1]["buy"] + x[1]["sell"], reverse=True)[:10]:
                m = market[:42] + ".." if len(market) > 45 else market
                print(f"  {m:<45} {data['buy']:>6} {data['sell']:>6}")
    
    print()


# ============================================================
# Monitor Mode (poll for new activity)
# ============================================================
async def monitor_wallet(browser, username, interval, seen_txs=None):
    """Check wallet for new activity and return any new trades."""
    if seen_txs is None:
        seen_txs = set()
    
    _, stats, trades = await scrape_wallet(browser, username, verbose=False)
    new_trades = []
    
    for t in trades:
        tx = t.get("tx", "")
        if tx and tx not in seen_txs:
            seen_txs.add(tx)
            new_trades.append(t)
    
    return stats, new_trades, seen_txs


async def run_monitor(username, interval=MONITOR_DEFAULT_INTERVAL):
    """Continuously monitor a wallet for new activity."""
    seen_txs = set()
    first_run = True
    
    print(f"\n  🔍 Monitoring @{username} every {interval}s...")
    print(f"  Press Ctrl+C to stop\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            while True:
                start_time = time.time()
                
                _, new_trades, seen_txs = await monitor_wallet(browser, username, interval, seen_txs)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if first_run:
                    if new_trades:
                        print(f"  [{timestamp}] Initial state — {len(new_trades)} existing trades cached")
                    else:
                        print(f"  [{timestamp}] Initial state — no trades found")
                    first_run = False
                else:
                    if new_trades:
                        print(f"\n  🆕 [{timestamp}] NEW TRADE{'S' if len(new_trades) > 1 else ''} DETECTED!")
                        print(f"  {'─' * 60}")
                        for t in new_trades:
                            print(f"     [{t.get('type', '?')}] {t.get('market', '?')[:50]}")
                            print(f"     Shares: {t.get('shares', '?')}  |  Value: {t.get('value', '?')}  |  Time: {t.get('time', '?')}")
                            tx = t.get("tx", "")
                            if tx:
                                print(f"     Tx: https://polygonscan.com/tx/{tx}")
                            print()
                    else:
                        # Progress dot
                        print(f"  [{timestamp}] ✓ No new activity", end="\r")
                
                # Sleep for the remaining interval time
                elapsed = time.time() - start_time
                sleep_time = max(1, interval - elapsed)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\n\n  🛑 Monitoring stopped by user\n")
        finally:
            await browser.close()


# ============================================================
# Multi-wallet batch scan
# ============================================================
async def batch_scan(wallets, verbose=True):
    """Scan multiple wallets and display results."""
    all_results = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        async def scrape_with_limit(username):
            async with semaphore:
                return await scrape_wallet(browser, username, verbose)
        
        tasks = [scrape_with_limit(w) for w in wallets]
        all_results = await asyncio.gather(*tasks)
        
        await browser.close()
    
    display_multi_wallet(all_results)
    return all_results


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Wallet Monitor — Track Polymarket wallets and activity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 polymarket_wallet_monitor.py ca6859f3c004bff161e3328d27ddba6c
  python3 polymarket_wallet_monitor.py 0x7f69983eb28245bba0d5083502a78744a8f66162
  python3 polymarket_wallet_monitor.py ca6859f3c... --monitor
  python3 polymarket_wallet_monitor.py --file wallets.txt
  python3 polymarket_wallet_monitor.py --file wallets.txt --monitor --interval 30
        """
    )
    parser.add_argument("wallet", nargs="?", help="Polymarket username or Ethereum address")
    parser.add_argument("--file", "-f", help="File with wallet addresses/usernames (one per line)")
    parser.add_argument("--monitor", "-m", action="store_true", help="Monitor mode — watch for new trades")
    parser.add_argument("--interval", "-i", type=int, default=MONITOR_DEFAULT_INTERVAL,
                        help=f"Check interval in seconds (default: {MONITOR_DEFAULT_INTERVAL})")
    parser.add_argument("--quiet", "-q", action="store_true", help="Less verbose output")
    
    args = parser.parse_args()
    
    # Collect wallets
    wallets = []
    if args.file:
        try:
            with open(args.file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        wallets.append(line)
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
    elif args.wallet:
        wallets.append(args.wallet)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Normalize wallet identifiers
    usernames = []
    for w in wallets:
        user = extract_wallet_username(w)
        if user:
            usernames.append(user)
        else:
            print(f"⚠ Could not parse wallet identifier: {w}")
    
    if not usernames:
        print("❌ No valid wallet identifiers provided")
        sys.exit(1)
    
    verbose = not args.quiet
    
    # Run
    if args.monitor:
        if len(usernames) > 1:
            print("⚠ Monitor mode only supports a single wallet. Using the first one.")
        asyncio.run(run_monitor(usernames[0], args.interval))
    else:
        asyncio.run(batch_scan(usernames, verbose))


if __name__ == "__main__":
    main()
