# Real-Time Rental Alert System

## Problem Description
In hyper-competitive rental markets, affordable units are often rented within hours of being listed. Manual refreshing of websites is inefficient and impossible to maintain 24/7. This tool solves the problem by automating the monitoring process and delivering instant push notifications to your phone or computer.

## Solution Overview
This Python-based automation tool monitors specific property management websites or listing aggregators. It runs on a defined interval, checks for new listings, filters them by your maximum budget, and sends real-time alerts via Discord Webhooks.

### Key Features
*   **24/7 Monitoring:** Runs continuously on a scheduler.
*   **Smart Filtering:** Only alerts you for units under your max price.
*   **Duplicate Detection:** Remembers seen listings to prevent spam.
*   **Instant Alerts:** Uses Discord Webhooks (free, reliable, works on mobile/desktop).
*   **Configurable:** Customize target URL and CSS selectors via command line.

## Prerequisites
*   Python 3.8 or higher
*   A Discord Server (free) to receive notifications.

## Installation

1.  **Unzip the tool**:
    ```bash
    unzip rental-alert-system.zip
    cd rental-alert-system
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Get a Discord Webhook URL**:
    *   Open Discord -> Server Settings -> Integrations -> Webhooks.
    *   Click "New Webhook", name it "Rental Bot".
    *   Copy the **Webhook URL**.

## Usage

### 1. Test the Alert System
Before running the scraper, ensure you can receive messages:

```bash
python rental_alert_bot.py --test --webhook "YOUR_DISCORD_WEBHOOK_URL"
```

### 2. Run the Scraper
You need to identify the CSS selectors for the website you want to scrape (Right-click element -> Inspect in Chrome). 

**Example (Generic Site):**
```bash
python rental_alert_bot.py \
  --url "https://example-rentals.com/listings" \
  --max-price 1500 \
  --webhook "YOUR_DISCORD_WEBHOOK_URL" \
  --interval 5
```

**Example with Custom Selectors:**
If the website uses specific classes (e.g., `<div class="property-card">` and `<span class="rent-cost">`):

```bash
python rental_alert_bot.py \
  --url "https://some-agency.com" \
  --max-price 2000 \
  --webhook "YOUR_WEBHOOK_URL" \
  --sel-container ".property-card" \
  --sel-price ".rent-cost" \
  --sel-title ".property-title"
```

## Configuration Options

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--url` | The URL to scrape (Required) | N/A |
| `--max-price` | Maximum budget filter | 2000.0 |
| `--webhook` | Discord Webhook URL | Empty (Logs only) |
| `--interval` | Minutes between checks | 10 |
| `--test` | Run a simulation to test alerts | False |
| `--sel-container` | CSS selector for the listing card | `article` |
| `--sel-price` | CSS selector for the price text | `.price` |
| `--sel-title` | CSS selector for the title | `h2` |

## Recommendations
*   **Deployment:** Run this on a Raspberry Pi or a cheap VPS (e.g., DigitalOcean, AWS Free Tier) using `nohup` or `screen` to keep it running 24/7.
*   **Respect:** Do not set the interval lower than 1-2 minutes to avoid getting your IP banned by the target website.
*   **Selectors:** Websites change frequently. If the bot stops finding listings, check if the website changed its HTML structure and update your CSS selectors accordingly.