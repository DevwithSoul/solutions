# For Every Problem is a Solution

You posted on Reddit about your Problem. My Agents solved it in no time. You're welcome.

## What is this?

This repository is a living archive of **49 Python automation tools** — each one built in response to real questions, frustrations, and "I wish there was a script for that" posts on Reddit. From scraping SEC filings to monitoring crypto whales, every folder here is a ready-to-run solution to a problem someone actually had.

## Quick Start

```bash
git clone https://github.com/DevwithSoul/solutions.git
cd solutions/<project-name>
pip install -r requirements.txt
python <main_script>.py --help
```

No frameworks. No bloated configs. Each project is a single Python file with a `requirements.txt` — just install and go.

## Solutions at a Glance

### 📊 Finance & Investing
| Tool | What it does |
|------|-------------|
| `automated-dividend-tracker` | Fetch dividend data from Yahoo Finance, export to CSV |
| `automated-stock-screener` | Screen stocks by ROIC, NOPAT, net margin via Financial Modeling Prep |
| `custom-stock-screener` | Custom valuation scoring with yfinance |
| `financial-data-tool` | Fundamental data aggregator with ROIC calculation |
| `fair-value-watchlist-tool` | Graham Number & fair value calculations |
| `stock-financials-extractor` | Extract financials with FCF calculation |
| `iv-monitor-tool` | Real-time options implied volatility via Polygon.io |
| `rsi-alert-system` | RSI crossover detection with Discord alerts |
| `smart-price-tracker` | Price tracking with Playwright + dual webhooks |
| `stock-monitor-tool` | Selenium-based price monitoring |
| `stock-price-monitor-tool` | Playwright-based price monitoring |

### 🏛️ SEC & Insider Trading
| Tool | What it does |
|------|-------------|
| `sec-financial-data-tool` | Pull 10-K/10-Q financials from SEC EDGAR XBRL API |
| `sec-scraper-tool` | Scrape revenue & net income from SEC company-concept endpoint |
| `sec-insider-alert-bot` | Alert on Form 4 open-market purchases via RSS + XML parsing |
| `sec-insider-bot-tool` | Form 4 monitor with dry-run mode |
| `sec-insider-bot` | Feedparser-based insider trading monitor |
| `sec-insider-monitor` | HTML-based Form 4 purchase detector |
| `sec-insider-trade-bot` | Comprehensive insider trade monitor |
| `insider-signal-bot` | SEC EDGAR Form 4 monitor with Discord rich embeds |

### 🐋 Crypto & Blockchain
| Tool | What it does |
|------|-------------|
| `arbitrage-monitor-tool` | Real-time cross-exchange arb detection via WebSocket |
| `chain-alert-bot` | Uniswap V2 new liquidity pool monitor |
| `crypto-whale-tracker-bot` | Etherscan wallet tracker with Telegram alerts |
| `crypto-whale-tracker-tool` | Direct RPC whale tracker with Discord embeds |
| `crypto-whale-tracker` | Blockchain whale monitor with Telegram alerts |
| `whale-watcher-bot` | Etherscan watcher with Discord embed alerts |
| `first-mover-alert-bot` | Selenium-based first-mover detection |

### 📦 E-Commerce & Inventory
| Tool | What it does |
|------|-------------|
| `automated-stock-alert-bot` | Monitor product pages for stock changes, Discord alerts |
| `inventory-sniper-tool` | Real-time inventory monitoring with Playwright |
| `restock-monitor-tool` | E-commerce restock & price monitor |
| `no-api-inventory-sync` | Inventory scraper with demo mode + CSV/JSON export |

### 🏠 Rental & Real Estate
| Tool | What it does |
|------|-------------|
| `rental-alert-system` | Scheduled rental scanner with Discord alerts |
| `rental-listing-monitor` | Rental scraper with jittered intervals + UA rotation |
| `rental-monitor-tool` | Rental monitor with SQLite dedup |

### 🔍 Web Scraping & Monitoring
| Tool | What it does |
|------|-------------|
| `automated-client-site-health-monitor` | Scan sites for broken links, mixed content, Slack/email alerts |
| `chilean-congress-vote-scraper` | Scrape Chilean Congress SOAP/XML API with resume support |
| `dynamic-directory-scraper` | Playwright scraper with scroll/click strategies |
| `dynamic-spa-watcher` | SPA change detection with webhook alerts |
| `infinite-scroll-scraper-tool` | Infinite scroll content scraper with Playwright |
| `spa-monitor-tool` | SPA change detector with networkidle wait |
| `web-monitor-bot` | Page monitor with dual search modes + Discord alerts |
| `email-data-extractor` | IMAP email extractor with regex parsing |

### 📄 Document & Data Processing
| Tool | What it does |
|------|-------------|
| `invoice-extractor-tool` | PDF invoice extractor with regex + sample PDF generation |
| `spreadsheet-consolidation-tool` | Merge CSV/Excel files with header normalization |
| `bulk-file-renamer-tool` | Batch rename files from Excel/CSV mapping |
| `supplier-feed-sync` | Stream processing middleware with content hashing |

### 🔁 Portfolio & Rebalancing
| Tool | What it does |
|------|-------------|
| `new-money-rebalancer` | Tax-efficient portfolio contribution rebalancer |
| `privacy-portfolio-rebalancer` | Portfolio rebalancer with yfinance live prices |

### 🌉 Integrations & Bridges
| Tool | What it does |
|------|-------------|
| `tradingview-exchange-bridge` | Flask app — TradingView webhooks to exchange orders via CCXT |
| `tradingview-webhook-bridge` | CCXT-based TradingView webhook executor |

## Test Status

All 49 solutions have been syntax-checked, dependency-verified, and code-reviewed.

| Status | Count |
|--------|-------|
| ✅ Pass | 49 |
| ⚠️ Warnings | 0 |
| ❌ Failed | 0 |

See [`checks_05_2026.md`](checks_05_2026.md) for the full audit report.

## Download & Test Your Solution

```bash
# Pick a tool
cd solutions/whale-watcher-bot

# Install deps
pip install -r requirements.txt

# Run it
python whale_watcher_bot.py --help
```

Each tool has sensible defaults, CLI arguments, and clear README documentation. Most output to Discord, Telegram, or CSV — so you can see results immediately.

## Leave this Repo a Star ⭐

If any of these tools saved you time, taught you something, or just made you smile — **leave a star on the repo**. It helps more people find these solutions and keeps the agents building.

---

**Built by [DevwithSoul](https://github.com/DevwithSoul) • Powered by AI Agents • For every Reddit problem, there's a solution here.**
