# Real-Time Rental Scraper & Notifier

## Problem Description
In competitive housing markets, relying on legacy websites that lack email or push notifications often results in missing out on opportunities. By the time a user manually refreshes the page, the best rentals are already taken. This user needed a way to automate the checking process and receive instant alerts on their phone via Discord.

## Solution Overview
This tool is a Python-based web scraper designed to run continuously on a local machine or server (like a Raspberry Pi or VPS). It monitors a specific URL for changes in the listing grid. 

**Key Features:**
- **Deduplication:** Uses a local SQLite database to track seen listings, ensuring you never get the same alert twice.
- **Anti-Ban Logic:** Implements randomized sleep intervals (Jitter) and browser-like User-Agent headers to mimic human behavior and prevent IP blocking.
- **Instant Notifications:** Integrates with Discord Webhooks to send push notifications immediately when a new listing appears.
- **Robust Parsing:** Uses `BeautifulSoup4` for flexible HTML parsing.

## Prerequisites
- Python 3.8 or higher.
- A Discord account and a Server (to create a Webhook).
- Basic knowledge of HTML/CSS (to adjust selectors for your specific target website).

## Installation

1. **Unzip the package:**
   Extract `rental-monitor-tool.zip` to a folder.

2. **Install Dependencies:**
   Open your terminal/command prompt in the folder and run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the Script:**
   Open `rental_monitor.py` in a text editor.
   - Update `TARGET_URL` with the website you want to scrape.
   - Update `DISCORD_WEBHOOK_URL` with your actual webhook URL.
   - **Critical:** Update the `SELECTORS` dictionary. You must inspect the target website's HTML structure (Right-click -> Inspect) to find the correct CSS classes for the listing container, title, price, and link.

## Usage

Run the script using Python:

```bash
python rental_monitor.py
```

**First Run Behavior:**
The script will scan the page and save all *current* listings to the database without sending notifications (to prevent spamming you with old ads). It will log "Initial scan complete".

**Subsequent Checks:**
The script will sleep for a random interval (default 1-3 minutes). On the next wake-up, if it finds a listing not in the database, it will send a Discord alert.

## Recommendations
- **Hosting:** For 24/7 monitoring, run this on a VPS (e.g., DigitalOcean, AWS EC2) or a Raspberry Pi.
- **Respect Rate Limits:** Do not set the `CHECK_INTERVAL` too low (e.g., under 30 seconds), or you risk getting your IP banned by the target website.
- **Selectors:** Websites change their layout. If the script stops finding listings, re-check the CSS selectors in the configuration.