# Real-Time SEC Insider Trading Monitor

## Problem Description
Investors often struggle to track meaningful insider activity amidst the noise of stock grants, option exercises, and gifts. The SEC EDGAR database provides this data, but it is raw and unorganized. Traders need a tool to specifically filter for **Open Market Purchases** (Form 4, Transaction Code 'P') and receive immediate alerts on platforms they use daily, like Discord.

## Solution Overview
This Python-based automation tool monitors the SEC EDGAR Atom feed in real-time. It:
1. Polls for new `Form 4` filings (Statement of Changes in Beneficial Ownership).
2. Parses the raw HTML filing to distinguish between automatic grants and actual open-market purchases.
3. Filters specifically for Transaction Code `P` (Purchase).
4. Sends a rich-text alert to a configured Discord Webhook.

## Prerequisites
*   **Python 3.8+** installed.
*   A **Discord Webhook URL** (Channel Settings > Integrations > Webhooks).
*   A valid **User-Agent string**. The SEC requires a User Agent in the format: `"Company Name AdminContact@company.com"` to identify your bot. Using a fake or generic agent may result in IP bans.

## Installation

1.  **Unzip the tool**:
    ```bash
    unzip sec-insider-monitor.zip
    cd sec-insider-monitor
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from the command line using the arguments below.

```bash
python sec_monitor.py --webhook "YOUR_DISCORD_WEBHOOK_URL" --user-agent "MyInvestmentBot myemail@example.com"
```

### Optional Arguments
*   `--interval`: Set the polling frequency in seconds (Default: 60). Do not set lower than 1 second to respect SEC rate limits.

## Configuration

No config file is required; all settings are passed via CLI arguments for ease of deployment (e.g., in Docker or Systemd).

## Recommendations
*   **Hosting**: Run this on a small VPS (DigitalOcean, AWS EC2, or a Raspberry Pi) using `systemd` or `screen` to keep it running 24/7.
*   **Rate Limiting**: The SEC limits requests to 10 per second. This script defaults to checking every 60 seconds, which is well within safe limits.
*   **Logic**: The parser looks for the specific Transaction Code 'P' in the HTML tables. While effective, SEC HTML formats can vary slightly between older filings; this tool is optimized for standard modern filings.