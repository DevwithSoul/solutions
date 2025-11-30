# Real-Time SEC Insider Trade Alert Bot

## Problem Description
Traders and analysts often rely on SEC Form 4 filings to track insider sentiment. However, the raw SEC RSS feed is noisy. It mixes routine stock grants (awards given to executives as compensation) with actual open-market purchases (executives spending their own money to buy stock). Filtering these manually is time-consuming and prone to error.

## Solution Overview
This Python automation tool monitors the SEC EDGAR Atom feed in real-time. It:
1.  Detects new Form 4 filings.
2.  Fetches the raw XML document associated with the filing.
3.  Parses the XML to distinguish between Transaction Code 'P' (Purchase) and 'A' (Grant/Award).
4.  Calculates the total value of the purchase.
5.  Sends a rich-text alert to a Discord channel via Webhook only if a valid open-market purchase is detected.

## Prerequisites
-   Python 3.8+
-   A Discord Server (to create a Webhook).
-   Internet connection.

## Installation

1.  **Extract the tool**:
    Unzip `sec-insider-trade-bot.zip` to a folder.

2.  **Install Dependencies**:
    Open your terminal/command prompt in the folder and run:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The SEC requires a strictly formatted User-Agent string to identify who is scraping their data. You must provide a name and email.

Run the script from the command line:

```bash
python sec_insider_bot.py --webhook "YOUR_DISCORD_WEBHOOK_URL" --name "YourNameOrCompany" --email "admin@example.com"
```

### Arguments
-   `--webhook`: (Required) The Discord Webhook URL where alerts will be sent.
-   `--name`: (Required) Entity name for the User-Agent header.
-   `--email`: (Required) Contact email for the User-Agent header.
-   `--interval`: (Optional) Seconds to wait between checks (default: 60).

## Configuration
There is no configuration file; all settings are passed via command-line arguments for security and ease of deployment in containerized environments (like Docker).

## How it works
1.  **Feed Monitoring**: Checks the SEC RSS feed every 60 seconds.
2.  **Deduplication**: Tracks processed IDs to prevent duplicate alerts.
3.  **Deep Inspection**: Instead of relying on the generic RSS summary, it scrapes the index page to find the primary XML document.
4.  **Logic**: It sums up transactions where `transactionCode` is 'P' and `transactionAcquiredDisposedCode` is 'A'.

## Recommendations
-   **Rate Limiting**: The script includes a sleep timer to respect SEC rate limits (currently < 10 requests/second). Do not remove these delays.
-   **Deployment**: This script is ideal for running on a cheap VPS (e.g., DigitalOcean Droplet) or a Raspberry Pi using `systemd` or `Docker` to keep it running 24/7.