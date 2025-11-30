# The 'First Mover' Alert Bot

## Problem Description
In high-demand markets like apartment rentals, freelance job postings, or limited-edition product drops, speed is everything. Users often miss out because they cannot manually refresh pages fast enough. Furthermore, many modern websites use dynamic JavaScript (React, Vue, etc.) to load listings, making simple HTML scrapers ineffective.

## Solution Overview
This tool is a persistent automation bot designed to give you the "First Mover" advantage. 

**Key Features:**
1.  **Dynamic Rendering:** Uses Selenium WebDriver to render JavaScript-heavy websites just like a real browser.
2.  **State Management:** Maintains a local JSON database of "seen" items to ensure you only get alerted for *new* listings.
3.  **Real-Time Alerts:** Integrates with Discord Webhooks to push notifications immediately to your phone or desktop.
4.  **Configurable:** Works with any website by accepting CSS selectors via command-line arguments.

## Prerequisites
1.  **Python 3.8+** installed on your machine.
2.  **Google Chrome** browser installed.
3.  A **Discord Webhook URL** (optional, but recommended for alerts).

## Installation

1.  **Unzip the tool**:
    Extract `first-mover-alert-bot` to a folder.

2.  **Install Dependencies**:
    Open a terminal in the folder and run:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script via the command line. You need to identify the CSS selectors for the items you want to track.

### Basic Syntax
```bash
python first_mover_bot.py --url "<TARGET_URL>" --selector "<CONTAINER_CSS>" --id-selector "<LINK_CSS>" --webhook "<DISCORD_URL>"
```

### Example: Monitoring Hacker News (Newest)
This example tracks the "Newest" page of Hacker News and alerts you to every new post.

```bash
python first_mover_bot.py \
  --url "https://news.ycombinator.com/newest" \
  --selector "tr.athing" \
  --id-selector "span.titleline > a" \
  --interval 30
```
*(Note: Remove the backslashes and put on one line if using Windows Command Prompt)*

### Arguments
*   `--url`: The website address to monitor.
*   `--selector`: The CSS selector that identifies the container of a single listing (e.g., `div.job-card`).
*   `--id-selector`: (Optional) The CSS selector inside the container to find the specific link or title. If omitted, the bot uses the container itself.
*   `--webhook`: Your Discord Webhook URL. If omitted, alerts are printed to the console.
*   `--interval`: Seconds to wait between checks (default: 60).
*   `--no-headless`: Opens the browser window visibly (useful for debugging selectors).

## Configuration

### How to get CSS Selectors
1.  Open Chrome and go to the target site.
2.  Right-click the item you want to track and select **Inspect**.
3.  Look for a class name or ID (e.g., `<div class="listing-item">`).
4.  Use that class as the selector (e.g., `.listing-item`).

### How to get a Discord Webhook
1.  Create a text channel in your Discord server.
2.  Go to **Edit Channel** > **Integrations** > **Webhooks**.
3.  Create a new webhook and copy the URL.

## Recommendations
*   **Respect Rate Limits:** Do not set the `--interval` too low (e.g., under 5 seconds) or the target website may ban your IP address.
*   **State File:** The script creates a `seen_items.json` file. If you want to reset the bot to alert on everything currently on the page, delete this file.