# The Dynamic SPA Watcher

## Problem Description
Traditional web scrapers (like `requests` or `BeautifulSoup`) fetch the initial HTML of a page. However, modern Single Page Applications (SPAs) often load content asynchronously using JavaScript (React, Vue, Angular) *after* the initial page load. This makes standard scraping tools ineffective, as they see empty containers instead of data. Users need a way to execute the page's JavaScript, wait for specific elements to render, and monitor them for changes.

## Solution Overview
This tool uses **Playwright**, a powerful browser automation library, to launch a headless Chromium browser. It mimics a real user by:
1. Loading the page and executing all JavaScript.
2. Intelligently waiting for the target DOM element to appear.
3. Extracting the text content.
4. Comparing it against the previous state.
5. Alerting via Console or Webhook if a change is detected.

## Prerequisites
- **Python 3.8+**
- **Pip** (Python Package Manager)

## Installation

1. Install the required Python package:
   ```bash
   pip install -r requirements.txt
   ```

2. Install the Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

## Usage

Run the script from the command line.

### Basic Monitoring
Monitor a product price on an e-commerce SPA every 30 seconds:
```bash
python spa_watcher.py --url "https://example-spa-store.com/product/123" --selector ".current-price" --interval 30
```

### With Webhook Alerting
Send a POST request to a webhook (e.g., Slack, Discord, Zapier) when the content changes:
```bash
python spa_watcher.py --url "https://crypto-site.com/btc" --selector "#btc-value" --webhook "https://hooks.slack.com/services/T000/B000/XXXX"
```

### Debugging Mode
Run with the browser visible to verify the selector is correct:
```bash
python spa_watcher.py --url "..." --selector "..." --visible
```

## Configuration Options
| Argument | Description |
| :--- | :--- |
| `--url` | **Required**. The full URL of the page to monitor. |
| `--selector` | **Required**. The CSS selector (e.g., `#id`, `.class`) to watch. |
| `--interval` | Seconds to wait between checks. Default: 60. |
| `--webhook` | Optional URL. Receives a JSON POST with `text`, `source`, and `timestamp` on change. |
| `--visible` | If set, runs the browser in headful mode (visible UI). |

## Finding Selectors
To find the correct selector:
1. Open the website in Chrome/Firefox.
2. Right-click the element you want to watch.
3. Select "Inspect".
4. Right-click the HTML element in the DevTools panel -> Copy -> Copy selector.

## Recommendations
- **Intervals**: Do not set the interval too low (e.g., < 5 seconds) to avoid getting IP banned by the target server.
- **Selectors**: Use specific IDs (`#price`) over generic classes (`.text-bold`) for reliability.