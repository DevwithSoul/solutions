# Automated Restock & Price Monitor

## Problem Description
Users often miss out on limited-stock items or price drops because they cannot physically refresh a webpage 24/7. Furthermore, modern e-commerce sites use dynamic JavaScript (React, Vue, etc.) which renders standard HTTP request bots useless. This tool solves that problem by using a real browser automation engine to monitor availability and prices.

## Solution Overview
This tool uses **Python** and **Playwright**. Playwright launches a real Chromium browser (headless by default) to load the webpage, rendering all JavaScript exactly as a user would see it. 

It extracts text from a specific CSS selector you provide and checks if:
1. The price is below your target.
2. Or, specific text (like "Add to Cart") is present.

If a condition is met, it logs to the console and optionally sends a notification to a **Discord channel**.

## Prerequisites
1. **Python 3.8+** installed.
2. **Discord Webhook URL** (Optional, for notifications).

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Browsers for Playwright**
   This is a critical step. The script relies on Playwright's browser binaries.
   ```bash
   playwright install chromium
   ```

## Usage

Run the script from the command line.

### 1. Price Drop Monitor
Alert if the price at the selector drops below $500.
```bash
python restock_monitor.py --url "https://example.com/product" --selector ".product-price" --max-price 500 --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### 2. Restock Monitor (Keyword)
Alert if the text "In Stock" appears in the status area.
```bash
python restock_monitor.py --url "https://example.com/gpu" --selector "#availability-status" --keyword "In Stock" --interval 30
```

### 3. Debugging (Visual Mode)
If you aren't sure if it's working, add `--visible` to see the browser open and navigate.
```bash
python restock_monitor.py --url "..." --selector "..." --keyword "Stock" --visible
```

## Configuration Arguments

| Argument | Description |
|----------|-------------|
| `--url` | The product page URL. (Required) |
| `--selector` | The CSS selector for the element to watch (e.g., `.price`, `#status`). (Required) |
| `--max-price` | Trigger if the number found in the selector is <= this value. |
| `--keyword` | Trigger if this specific text is found inside the selector. |
| `--webhook` | Discord Webhook URL for alerts. |
| `--interval` | How often to check in seconds (default: 60). |
| `--visible` | Run the browser visibly instead of headless. |

## Finding the Selector
1. Open the product page in Chrome/Firefox.
2. Right-click the Price or "Out of Stock" text.
3. Select **Inspect**.
4. In the developer tools, right-click the highlighted HTML element -> **Copy** -> **Copy selector**.

## Recommendations
- **Interval:** Do not set the interval too low (e.g., < 10 seconds) or you risk getting IP banned by the website.
- **Hosting:** This script runs perfectly on a Raspberry Pi or a cheap VPS (DigitalOcean/Linode).