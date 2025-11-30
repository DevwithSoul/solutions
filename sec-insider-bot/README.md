# Real-Time Insider Trading Alert Bot

An automated tool designed to monitor the SEC EDGAR database for Form 4 filings (Statement of Changes in Beneficial Ownership). It filters for open market purchases (Transaction Code 'P') and sends real-time alerts to Discord when high-value insider buying occurs.

## Problem Description

Traders and analysts often look for "insider buying" as a strong signal of confidence in a company's future. However, the SEC receives thousands of filings daily. Manually refreshing the SEC website, parsing complex XML documents, and filtering out noise (like stock grants, options exercises, or small purchases) is time-consuming and error-prone. Traders need a system that pushes only the most significant signals directly to them immediately after filing.

## Solution Overview

This Python-based bot:
1.  **Polls** the SEC EDGAR RSS feed every 60 seconds for new Form 4 filings.
2.  **Extracts** the raw XML document link from the filing index page.
3.  **Parses** the XML to identify specific transaction codes ('P' - Open Market Purchase).
4.  **Aggregates** the total value of shares bought in the filing.
5.  **Filters** out transactions below a user-defined monetary threshold (e.g., $100,000).
6.  **Alerts** a Discord channel via Webhook with a rich embed containing the Ticker, Insider Name, Role, Total Value, and Price.

## Prerequisites

*   Python 3.8+
*   A Discord Server (to create a Webhook URL)
*   Internet connection

## Installation

1.  **Unzip the package**:
    ```bash
    unzip sec-insider-bot.zip
    cd sec-insider-bot
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the bot, you must provide your Discord Webhook URL and a User-Agent string. 

**Note on User-Agent:** The SEC strictly requires a User-Agent in the format: `"Name email@domain.com"` (e.g., `"John Doe john@example.com"`). Requests without this specific format may be blocked.

### Basic Command

```bash
python sec_insider_bot.py --webhook "YOUR_DISCORD_WEBHOOK_URL" --user-agent "YourName your@email.com"
```

### Custom Threshold

By default, the bot alerts on purchases over $100,000. To change this to $50,000:

```bash
python sec_insider_bot.py --webhook "..." --user-agent "..." --threshold 50000
```

### Running in Background (Linux/Mac)

```bash
nohup python sec_insider_bot.py --webhook "..." --user-agent "..." & 
```

## Recommendations

1.  **Rate Limiting**: The code includes delays to respect SEC rate limits (max 10 requests/sec). Do not remove the `time.sleep` calls.
2.  **Deployment**: For 24/7 uptime, deploy this script on a VPS (e.g., AWS EC2, DigitalOcean Droplet) or a container service (Docker).
3.  **Logging**: The bot logs to the console (Standard Output). Redirect this to a file if you need long-term debugging history.
4.  **Persistence**: The bot creates a `processed_filings.json` file to track history. If you delete this file, the bot may re-alert on the last 40 filings upon restart.