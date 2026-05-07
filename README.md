# DevwithSoul Solutions — Python Automation Tools

A curated collection of **production-ready Python automation scripts** covering cryptocurrency tracking, stock market analysis, web scraping, e-commerce monitoring, and workflow automation. Each tool is self-contained with its own dependencies and documentation.

---

## Table of Contents

- [Crypto & Blockchain](#-crypto--blockchain)
- [Stock Market & Investing](#-stock-market--investing)
- [SEC & Insider Trading](#-sec--insider-trading)
- [E-Commerce & Inventory](#-e-commerce--inventory)
- [Web Scraping & Monitoring](#-web-scraping--monitoring)
- [Rental Market](#-rental-market)
- [Automation & Productivity](#-automation--productivity)

---

## Crypto & Blockchain

Tools for tracking on-chain activity, whale wallets, arbitrage opportunities, and automating trade execution from TradingView signals.

| Tool | Description |
|------|-------------|
| [arbitrage-monitor-tool](./arbitrage-monitor-tool) | Monitors multiple exchanges simultaneously and fires alerts when a price discrepancy (arbitrage opportunity) is detected in real time. |
| [chain-alert-bot](./chain-alert-bot) | Real-time on-chain alert bot for DeFi and NFTs — catches new liquidity pools and stealth mints before the crowd. |
| [crypto-whale-tracker](./crypto-whale-tracker) | Decodes raw Ethereum blockchain data to identify large wallet movements ("whale" transactions) with minimal latency. |
| [crypto-whale-tracker-bot](./crypto-whale-tracker-bot) | Lightweight Telegram bot variant — monitors specific Ethereum wallets and pushes formatted alerts the moment a transaction lands. |
| [crypto-whale-tracker-tool](./crypto-whale-tracker-tool) | Standalone CLI tool version of the whale tracker with configurable wallet lists and threshold filters. |
| [whale-watcher-bot](./whale-watcher-bot) | Polls Etherscan for wallet activity and sends Discord webhook notifications for any qualifying transaction. |
| [tradingview-exchange-bridge](./tradingview-exchange-bridge) | Middleware server that receives TradingView Pine Script webhook alerts and forwards them as live orders to a crypto exchange (e.g. Binance). |
| [tradingview-webhook-bridge](./tradingview-webhook-bridge) | Lightweight HTTP server that validates and relays TradingView alerts to a brokerage account for automated trade execution. |

---

## Stock Market & Investing

Screeners, alert bots, and financial data aggregators that replace hours of manual spreadsheet work.

| Tool | Description |
|------|-------------|
| [automated-stock-alert-bot](./automated-stock-alert-bot) | Monitors e-commerce and financial sites for target price levels and pushes Discord notifications when conditions are met. |
| [automated-stock-screener](./automated-stock-screener) | Pulls Income Statement and Balance Sheet data in bulk, calculates valuation metrics, and outputs a filtered screener report to Excel. |
| [custom-stock-screener](./custom-stock-screener) | User-defined screening logic — combine custom growth thresholds, debt ratios, and valuation rules that rigid free tools won't allow. |
| [automated-dividend-tracker](./automated-dividend-tracker) | Fetches ex-dividend dates, yields, and payout ratios for a watchlist and forecasts monthly cash flow — without needing a paid data API. |
| [fair-value-watchlist-tool](./fair-value-watchlist-tool) | Automatically calculates Graham Number / fair-value estimates for a stock watchlist and flags undervalued names each weekend. |
| [financial-data-tool](./financial-data-tool) | Aggregates ROIC and EV/EBITDA across a list of tickers from public sources and exports to a structured spreadsheet. |
| [stock-financials-extractor](./stock-financials-extractor) | Bulk-extracts historical Revenue and Free Cash Flow for hundreds of stocks and consolidates them into a single comparison file. |
| [stock-price-monitor-tool](./stock-price-monitor-tool) | SPA-aware price and availability monitor built for modern React/Vue e-commerce and financial sites. |
| [new-money-rebalancer](./new-money-rebalancer) | Calculates exactly how to deploy new cash into an existing portfolio to restore target allocations — no selling required. |
| [privacy-portfolio-rebalancer](./privacy-portfolio-rebalancer) | Offline-first rebalancer for investors managing assets across multiple brokerages who don't want to connect accounts to third-party services. |

---

## SEC & Insider Trading

Bots that parse SEC EDGAR filings and surface only the high-signal insider activity worth acting on.

| Tool | Description |
|------|-------------|
| [sec-insider-alert-bot](./sec-insider-alert-bot) | Monitors SEC Form 4 filings in real time and alerts only on genuine open-market purchases (Transaction Code 'P'), filtering out grants and option exercises. |
| [sec-insider-bot](./sec-insider-bot) | Detects significant open-market stock purchases by CEOs, CFOs, and Directors by parsing raw government XML from EDGAR. |
| [sec-insider-bot-tool](./sec-insider-bot-tool) | CLI tool variant — same Form 4 parsing logic packaged for scheduled or one-off runs. |
| [sec-insider-monitor](./sec-insider-monitor) | Broader insider activity monitor with noise-filtering to separate meaningful conviction buys from routine compensation grants. |
| [sec-insider-trade-bot](./sec-insider-trade-bot) | Processes the SEC EDGAR RSS feed, strips routine grants, and delivers clean insider-buy alerts via your preferred notification channel. |
| [insider-signal-bot](./insider-signal-bot) | Focuses specifically on "open market" Form 4 purchases as a bullish signal — ignores everything that doesn't represent real money put at risk. |
| [sec-financial-data-tool](./sec-financial-data-tool) | Extracts consistent historical financial data (10-K / 10-Q) from EDGAR using the structured XBRL API rather than fragile HTML parsing. |
| [sec-scraper-tool](./sec-scraper-tool) | Bulk-scrapes Revenue and Net Income from SEC 10-K filings for a list of tickers and exports to Excel for value investing research. |

---

## E-Commerce & Inventory

Sniper bots, restock monitors, and sync tools for high-demand products and supplier pipelines.

| Tool | Description |
|------|-------------|
| [inventory-sniper-tool](./inventory-sniper-tool) | Sub-second inventory poller for GPUs, sneakers, and limited drops — far faster than retailer email notifications. |
| [restock-monitor-tool](./restock-monitor-tool) | Headless-browser monitor that handles JavaScript-rendered product pages and alerts on restock or price changes. |
| [smart-price-tracker](./smart-price-tracker) | Combines price tracking and inventory status monitoring for modern SPA e-commerce sites, with configurable alert thresholds. |
| [stock-monitor-tool](./stock-monitor-tool) | Headless scraper for dynamically rendered inventory pages — works where plain `requests` fails. |
| [no-api-inventory-sync](./no-api-inventory-sync) | Screen-scrapes legacy supplier portals (no REST API available) and syncs live inventory data into a modern system. |
| [supplier-feed-sync](./supplier-feed-sync) | Parses monolithic CSV/XML supplier exports and synchronizes them with a RESTful API, handling deduplication and schema mapping. |

---

## Web Scraping & Monitoring

General-purpose scrapers and watchers that handle JavaScript-heavy, infinite-scroll, and SPA sites.

| Tool | Description |
|------|-------------|
| [dynamic-directory-scraper](./dynamic-directory-scraper) | Handles infinite-scroll and "Load More" paginated directories that standard HTTP scrapers can't reach. |
| [dynamic-spa-watcher](./dynamic-spa-watcher) | Watches Single Page Applications (React, Vue, Angular) for content changes by driving a real browser headlessly. |
| [infinite-scroll-scraper-tool](./infinite-scroll-scraper-tool) | Scrolls JavaScript-rendered pages to completion and extracts the full dataset — no content left behind. |
| [spa-monitor-tool](./spa-monitor-tool) | Lightweight headless SPA monitor that diffs page state between runs and triggers alerts on changes. |
| [web-monitor-bot](./web-monitor-bot) | General-purpose page watcher that detects when any target URL changes and fires instant notifications — useful for drops, postings, and releases. |
| [automated-client-site-health-monitor](./automated-client-site-health-monitor) | Crawls a client website looking for broken links, missing images, and mixed-content warnings, then emails a clean report. |
| [first-mover-alert-bot](./first-mover-alert-bot) | Polls high-competition pages (rentals, job boards, product drops) at high frequency and pushes alerts the moment new content appears. |

---

## Rental Market

Fast-moving rental listing monitors for competitive housing markets.

| Tool | Description |
|------|-------------|
| [rental-alert-system](./rental-alert-system) | 24/7 rental listing monitor that catches new postings within minutes — before the major platforms deliver their delayed email digests. |
| [rental-listing-monitor](./rental-listing-monitor) | Scrapes Zillow, Craigslist, and other listing sites in real time and pushes instant alerts for new listings that match your filters. |
| [rental-monitor-tool](./rental-monitor-tool) | Scraper and notifier for legacy rental sites with no built-in push notifications, so you never miss a listing. |

---

## Automation & Productivity

File, spreadsheet, and email automation tools that eliminate repetitive manual data work.

| Tool | Description |
|------|-------------|
| [bulk-file-renamer-tool](./bulk-file-renamer-tool) | Renames thousands of files in bulk using a mapping defined in an Excel spreadsheet — SKUs, employee IDs, product metadata, any column. |
| [email-data-extractor](./email-data-extractor) | Connects to a mailbox, parses recurring structured emails (invoices, order confirmations, reports), and writes extracted data fields to Excel automatically. |
| [invoice-extractor-tool](./invoice-extractor-tool) | Uses PDF parsing to pull Invoice Numbers, Dates, and Totals from PDF invoices and populate a spreadsheet — no manual transcription. |
| [spreadsheet-consolidation-tool](./spreadsheet-consolidation-tool) | Merges dozens of CSV/Excel files into a single master report, normalizing inconsistent column headers and tracking the source file for every row. |

---

## Getting Started

Each tool is self-contained. To run any of them:

```bash
cd <tool-folder>
pip install -r requirements.txt
python <script>.py
```

See the `README.md` inside each folder for configuration details, required API keys, and usage examples.

---

## Contributing

Found a bug or want to improve a tool? Open an issue or submit a pull request. Each tool lives in its own directory to keep contributions focused and easy to review.

---

*Built and maintained by [DevwithSoul](https://github.com/devwithsoul)*
