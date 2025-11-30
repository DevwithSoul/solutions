# The Instant Web Monitor Bot

## Problem Description
In today's high-demand digital marketplace, items like concert tickets, limited-edition sneakers, or gaming consoles sell out in seconds. Users are exhausted from manually refreshing pages, often missing opportunities due to human delay or sleep. There is a need for an automated solution that watches the page for them and notifies them immediately.

## Solution Overview
This tool is a Python-based automation bot that periodically scrapes a target website. It mimics a real browser to bypass basic anti-bot checks and parses the HTML content. 

**Key Features:**
- **Real-time Monitoring:** Checks website status at user-defined intervals.
- **Flexible Logic:** Can alert when text appears (e.g., "In Stock") OR when text disappears (e.g., "Sold Out" is gone).
- **Instant Notifications:** Integrates directly with Discord Webhooks to push alerts to your phone or computer instantly.
- **Spam Prevention:** Intelligent state tracking prevents the bot from sending duplicate alerts for the same event.

## Prerequisites
1. **Python 3.7+** installed on your machine.
2. **Discord Account** (for notifications).

## Installation

1. **Unzip the tool**:
   Extract the contents of `web-monitor-bot` to a folder.

2. **Install Dependencies**:
   Open your terminal or command prompt in the folder and run:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from your terminal using the following arguments:

### Basic Example
Alert me when "Add to Cart" appears on a page:
```bash
python web_monitor_bot.py --url "https://example.com/product" --text "Add to Cart" --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### Negative Search Example
Alert me when "Out of Stock" DISAPPEARS from the page:
```bash
python web_monitor_bot.py --url "https://example.com/product" --text "Out of Stock" --webhook "YOUR_DISCORD_WEBHOOK_URL" --missing
```

### Arguments Explained
- `--url`: The website address to monitor (Required).
- `--text`: The specific keyword phrase to look for (Required).
- `--webhook`: Your Discord Webhook URL. If omitted, it just logs to the console.
- `--interval`: How many seconds to wait between checks (Default: 30).
- `--missing`: (Optional Flag) If used, the bot alerts when the text is *NOT* found.

## Configuration: Getting a Discord Webhook
1. Open Discord and go to a Server you own (or create a new one).
2. Right-click a Text Channel -> **Edit Channel**.
3. Go to **Integrations** -> **Webhooks**.
4. Click **New Webhook**, name it (e.g., "Stock Bot"), and copy the **Webhook URL**.
5. Paste this URL into the `--webhook` argument.

## Recommendations
- **Intervals:** Do not set the interval too low (e.g., under 5 seconds) or the target website might ban your IP address for spamming requests.
- **Dynamic Sites:** This bot uses standard HTTP requests. It works for 80% of sites (Shopify, standard e-commerce). Sites that are fully JavaScript-rendered (where the screen is blank until JS loads) might require a more advanced Selenium-based solution.