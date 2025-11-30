# Automated Stock Alert Bot

A Python-based tool designed to monitor e-commerce websites for product availability and send instant notifications via Discord when an item comes back in stock.

## Problem Description
Buying high-demand items (GPUs, consoles, limited sneakers) is difficult because they sell out in seconds. Manually refreshing pages is inefficient and exhausting. This tool automates the checking process, running 24/7 to alert you the moment stock is detected.

## Solution Overview
This script acts as a specialized web scraper. It visits a target URL at set intervals, isolates a specific part of the page (like the "Add to Cart" button or status text), and checks if the text indicates availability. If it does, it sends a POST request to a Discord Webhook, triggering a push notification on your phone or computer.

## Prerequisites
1.  **Python 3.7+** installed on your system.
2.  **Discord Account** (for notifications).

## Installation

1.  **Unzip the tool**:
    Extract the contents of `automated-stock-alert-bot`.

2.  **Install Dependencies**:
    Open your terminal/command prompt in the folder and run:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

### Gets a Discord Webhook
1.  Open Discord and go to a server you own (or create a new one).
2.  Right-click a text channel -> **Edit Channel** -> **Integrations** -> **Webhooks**.
3.  Click **New Webhook**, name it, and copy the **Webhook URL**.

### Finding CSS Selectors
To tell the bot where to look on the page:
1.  Go to the product page in your browser (Chrome/Firefox).
2.  Right-click the "Out of Stock" or "Add to Cart" text and select **Inspect**.
3.  Look for the `class` or `id` of that element.
    *   Example ID: `#add-to-cart-button`
    *   Example Class: `.inventory-status`

## Usage

Run the script from the command line using arguments to define what to track.

### Scenario A: Alert when "In Stock" appears

```bash
python stock_alert_bot.py --url "https://example.com/product" --selector ".stock-label" --text "In Stock" --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### Scenario B: Alert when "Sold Out" disappears (Negative Match)
Sometimes it's safer to check if the "Sold Out" text is gone.

```bash
python stock_alert_bot.py --url "https://example.com/product" --selector ".status" --text "Sold Out" --negative --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### Command Line Arguments
-   `--url`: The full URL of the product page.
-   `--selector`: The HTML/CSS identifier (e.g., `h1`, `.price`, `#status`).
-   `--text`: The specific text to verify.
-   `--webhook`: (Optional) Your Discord Webhook URL.
-   `--interval`: (Optional) How often to check in seconds (default: 30).
-   `--negative`: (Optional) Flag to alert if the text is NOT found.

## Recommendations
-   **Interval**: Don't set the interval too low (e.g., < 5 seconds) or the website might ban your IP address.
-   **Testing**: Test the selector on a product that IS in stock first to ensure your configuration works.
