# Headless SPA Monitor

## Problem Description
Modern websites (Single Page Applications) rely heavily on JavaScript to render content. Standard HTTP libraries (like Python's `requests` or `BeautifulSoup` alone) often fail to scrape these sites because they only retrieve the initial HTML skeleton, not the dynamically loaded data. Developers need a way to "see" what a real user sees and monitor specific data points for changes.

## Solution Overview
This tool uses **Playwright**, a powerful browser automation library, to launch a headless Chromium browser. It:
1. Loads the full web page.
2. Executes the JavaScript.
3. Waits for specific DOM elements to appear.
4. Extracts the text content.
5. Compares it against previous checks and triggers alerts if the data changes.

## Prerequisites
- Python 3.8 or higher
- Pip (Python Package Manager)

## Installation

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Browser Binaries**
   Playwright requires its own browser binaries to function. Run this command after installing the requirements:
   ```bash
   playwright install chromium
   ```

## Usage

Run the script from the command line. You must provide the URL and the CSS selector of the element you want to watch.

### Basic Example
Monitor a crypto price element every 60 seconds (default):
```bash
python spa_monitor.py --url "https://example.com/crypto/btc" --selector ".current-price"
```

### Advanced Example
Monitor a stock status every 30 seconds and send a webhook alert (e.g., to Discord or Slack) when it changes:
```bash
python spa_monitor.py --url "https://shop.com/product/gpu" --selector "#stock-status" --interval 30 --webhook "https://discord.com/api/webhooks/xyz"
```

## Configuration Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--url` | Yes | The full URL of the page to monitor. |
| `--selector` | Yes | The CSS selector (e.g., `.class`, `#id`, `div > span`) of the target data. |
| `--interval` | No | Time in seconds between checks. Default: 60. |
| `--webhook` | No | A URL to POST a JSON payload to when data changes. |

## Recommendations
- **Selectors:** Use specific IDs or unique classes for the `--selector` argument to ensure accuracy.
- **Intervals:** Do not set the interval too low (e.g., < 5 seconds) to avoid getting IP banned by the target website.
- **Headless:** The script runs in headless mode by default, making it suitable for server environments (EC2, VPS, Docker).