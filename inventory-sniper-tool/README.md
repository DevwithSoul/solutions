# The Real-Time Inventory Sniper

## Problem Description
In high-demand markets (GPUs, sneakers, concert tickets), inventory sells out in seconds. Standard email notifications provided by retailers are often delayed by minutes, making them useless. Users need a way to monitor website changes instantly, rendering dynamic content (JavaScript) just like a real browser, and receiving immediate push notifications on their mobile devices.

## Solution Overview
This tool is a Python-based automation bot that:
1.  **Renders Dynamic Content**: Uses `Playwright` (a browser automation library) to load pages fully, ensuring that "Add to Cart" buttons loaded via JavaScript are detected.
2.  **Visual Verification**: Takes a screenshot when stock is found.
3.  **Instant Alerts**: Sends a push notification via Discord Webhooks immediately upon detection.

## Prerequisites
1.  **Python 3.8+** installed.
2.  **Discord Webhook URL**: 
    - Create a Discord Server -> Channel Settings -> Integrations -> Webhooks -> New Webhook -> Copy Webhook URL.

## Installation

1.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install Browser Drivers**:
    Playwright needs to download the browser binaries (Chromium) to function.
    ```bash
    playwright install chromium
    ```

## Usage

Run the script via command line. You need to identify the CSS selector of the element that indicates stock (e.g., the "Add to Cart" button).

### Basic Command
```bash
python inventory_sniper.py \
  --url "https://www.example.com/product-page" \
  --selector "button.add-to-cart" \
  --webhook "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
```

### Advanced Command (With Text Matching)
If the button always exists but changes text from "Sold Out" to "Add to Cart", use the `--text` argument.

```bash
python inventory_sniper.py \
  --url "https://www.example.com/product-page" \
  --selector "button" \
  --text "Add to Cart" \
  --webhook "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" \
  --interval 30
```

### Arguments
- `--url`: The product page URL.
- `--selector`: The CSS selector to watch (e.g., `#addToCart`, `.buy-button`).
- `--text` (Optional): Specific text the element must contain to trigger an alert.
- `--webhook`: Your Discord Webhook URL.
- `--interval`: Seconds between checks (default: 60).
- `--no-headless`: Run with the browser visible (useful for debugging selectors).

## Configuration & Tips
- **Finding Selectors**: Right-click the "Add to Cart" button in Chrome/Firefox and select "Inspect". Right-click the HTML element -> Copy -> Copy Selector.
- **Rate Limiting**: Do not set the interval too low (e.g., under 5 seconds) or the target website may block your IP address.

## Recommendations
For 24/7 monitoring, deploy this script on a VPS (Virtual Private Server) or a Raspberry Pi. Ensure the server has enough RAM to run a headless browser instance.