# Real-Time Rental Listing Monitor

## Problem Description
In competitive rental markets, good deals disappear within minutes. Standard platforms (Zillow, Craigslist, Rightmove, etc.) often delay email alerts by hours, causing users to miss opportunities. This tool solves that problem by scraping listing pages at a set interval and sending instant notifications to your phone or computer via Discord.

## Solution Overview
This Python script monitors a specific URL for changes. It:
1. Fetches the website content using rotated User-Agents to avoid bot detection.
2. Parses the HTML based on custom CSS selectors you provide.
3. Compares found listings against a local history file (`seen_listings.json`) to detect *new* items.
4. Sends a rich notification to a Discord channel via Webhook.

## Prerequisites
- **Python 3.7+** installed.
- A **Discord Account** and a server where you have permissions to create a Webhook.

## Installation

1. **Unzip the tool**:
   Extract the contents of `rental-listing-monitor.zip` to a folder.

2. **Install Dependencies**:
   Open your terminal/command prompt in the folder and run:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Get Discord Webhook URL
1. Open Discord, go to your server settings.
2. Go to **Integrations** > **Webhooks**.
3. Click **New Webhook**, name it "Rental Bot", and copy the **Webhook URL**.

### 2. Identify CSS Selectors
To make this script work on any site, you need to tell it where to look. 
1. Open the rental site in your browser (Chrome/Firefox).
2. Right-click on a listing card and select **Inspect**.
3. Find the class names for:
   - The main **Container** holding the listing info (e.g., `article.result-node`).
   - The **Title** (e.g., `.result-title`).
   - The **Price** (e.g., `.result-price`).
   - The **Link** (usually an `<a>` tag, e.g., `.result-title` or `a.link`).

## Usage

Run the script from the command line. 

**Example (Hypothetical Craigslist Search):**
```bash
python rental_monitor.py \
  --url "https://sfbay.craigslist.org/search/apa" \
  --webhook "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" \
  --container ".result-info" \
  --title ".titlestring" \
  --price ".price" \
  --link ".titlestring" \
  --interval 120
```

**Arguments:**
- `--url`: The search result page URL you want to monitor.
- `--webhook`: Your Discord Webhook URL.
- `--container`: CSS selector for the listing block.
- `--title`: CSS selector for the title text.
- `--price`: CSS selector for the price text.
- `--link`: CSS selector for the anchor tag containing the link.
- `--interval`: (Optional) Seconds to wait between checks (Default: 300).

## Recommendations
- **Interval**: Do not set the interval too low (e.g., under 60 seconds) to avoid getting your IP banned by the target website.
- **Testing**: Test your CSS selectors in the browser console first (e.g., `document.querySelectorAll('.result-info')`) to ensure they match.
- **Persistence**: The script creates a `seen_listings.json` file. If you want to reset the memory, simply delete this file.