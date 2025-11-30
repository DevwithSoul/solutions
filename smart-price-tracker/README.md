# Smart Price Tracker & Inventory Alert System

## Problem Description
Users often struggle to reliably scrape modern e-commerce websites to track prices and inventory. Traditional HTTP request-based scrapers fail because:
1.  **Dynamic Rendering:** Prices are often loaded via JavaScript after the initial page load.
2.  **Bot Detection:** Simple scripts are easily blocked by headers or behavior analysis.
3.  **Manual Checking:** Manually refreshing pages is inefficient and leads to missed opportunities.

## Solution Overview
This tool uses **Playwright** (a powerful browser automation library) to simulate a real user environment. It launches a headless Chromium browser, renders the full page including JavaScript, extracts the specific price/stock data using CSS selectors, and sends a notification to a Discord or Slack webhook if the price drops below your target.

## Prerequisites
1.  **Python 3.8+** installed on your system.
2.  **Webhook URL:**
    *   **Discord:** Server Settings -> Integrations -> Webhooks -> New Webhook.
    *   **Slack:** Incoming Webhooks App.

## Installation

1.  **Unzip the tool**:
    ```bash
    unzip smart-price-tracker.zip
    cd smart-price-tracker
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers**:
    *   This is a critical step. Playwright needs its own browser binaries.
    ```bash
    playwright install chromium
    ```

## Usage

### Finding Selectors
To use this tool, you need the **CSS Selector** for the price element on the website.
1.  Right-click the price on the website -> **Inspect**.
2.  Right-click the HTML element in the DevTools -> **Copy** -> **Copy selector**.

### Running Once (Cron Job Mode)
Useful if you want to schedule it via system cron (e.g., check every hour).

```bash
python smart_price_tracker.py \
  --url "https://example-ecommerce.com/product/123" \
  --price-selector ".product-price-text" \
  --target-price 299.99 \
  --webhook-url "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID"
```

### Running Continuously (Monitor Mode)
Keeps the script running and checks every 600 seconds (10 minutes).

```bash
python smart_price_tracker.py \
  --url "https://example-ecommerce.com/product/123" \
  --price-selector ".product-price-text" \
  --target-price 299.99 \
  --webhook-url "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID" \
  --interval 600
```

### Checking Stock (Optional)
You can also pass a selector to check if text indicates the item is out of stock.

```bash
python smart_price_tracker.py \
  ... (other args) \
  --stock-selector "#availability-status"
```

## Configuration

All configuration is handled via Command Line Arguments:

| Argument | Description | Required |
| :--- | :--- | :--- |
| `--url` | The full URL of the product page. | Yes |
| `--price-selector` | CSS selector for the price text. | Yes |
| `--target-price` | Float value (e.g., 50.00). Alerts if current <= target. | Yes |
| `--webhook-url` | URL to POST the JSON alert to. | Yes |
| `--stock-selector` | CSS selector to check for "Out of Stock" text. | No |
| `--interval` | Seconds to wait between checks. | No |

## Recommendations
*   **Intervals:** Do not set the interval too low (e.g., < 60 seconds) to avoid IP bans from the target website.
*   **Selectors:** E-commerce sites change layouts. If the script stops working, re-check the CSS selectors.
*   **Hosting:** For 24/7 monitoring, run this on a VPS (AWS EC2, DigitalOcean) or a Raspberry Pi.