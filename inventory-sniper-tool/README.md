# The Automated Inventory Sniper

## Problem Description
In high-demand markets (GPUs, limited edition sneakers, concert tickets), items sell out in seconds. Humans cannot manually refresh pages fast enough to compete with bots. This tool solves that problem by automating the monitoring process, handling dynamic page content (JavaScript), and sending instant alerts when an item becomes available.

## Solution Overview
This Python script uses **Selenium** to automate a web browser. Unlike simple HTTP requests, Selenium renders the full webpage, allowing it to bypass basic anti-bot measures that rely on checking for JavaScript execution. It monitors a specific HTML element on a page and triggers a Discord notification when the desired text (e.g., "Add to Cart") appears.

## Prerequisites
1. **Python 3.8+** installed on your system.
2. **Google Chrome** browser installed.
3. A **Discord Webhook URL** (optional, but recommended for mobile alerts).

## Installation

1. Unzip the tool folder.
2. Open a terminal/command prompt in the folder.
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script via command line. You need to provide the URL, the CSS selector of the element to watch, and the text that indicates the item is in stock.

### Finding the CSS Selector
1. Open the target website in Chrome.
2. Right-click the "Out of Stock" or "Add to Cart" button area.
3. Select **Inspect**.
4. Right-click the highlighted HTML code -> **Copy** -> **Copy selector**.

### Example Command

**Scenario:** Monitoring a generic store where the "Add to Cart" button has a class of `.add-btn`.

```bash
python inventory_sniper.py --url "https://example.com/product-page" --selector ".add-btn" --text "Add to Cart" --webhook "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID" --visible
```

### Arguments
- `--url`: The full URL of the product page.
- `--selector`: The CSS selector to monitor (e.g., `#availability`, `.stock-status`, `button[name='add']`).
- `--text`: THe text string that confirms the item is available.
- `--webhook`: (Optional) Your Discord Webhook URL for alerts.
- `--interval`: (Optional) Seconds to wait between checks (Default: 30).
- `--visible`: (Optional) Run the browser visibly (useful for debugging). Default is headless (hidden).

## Configuration & Tips
- **Anti-Bot Measures:** The script includes random sleep intervals and User-Agent rotation to mimic human behavior.
- **Rate Limiting:** Do not set the interval too low (e.g., under 5 seconds) or your IP address might be banned by the target website.
- **Headless Mode:** By default, the browser runs in the background. Use `--visible` if the site requires a CAPTCHA to be solved manually at the start.

## Recommendations
For 24/7 monitoring, deploy this script on a VPS (Virtual Private Server) or a Raspberry Pi. Ensure the server has a stable internet connection.