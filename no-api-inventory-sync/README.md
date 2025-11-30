# The "No-API" Inventory Sync Bot

## Problem Description
Many legacy suppliers and distributors operate on older web infrastructure that lacks modern APIs (REST/GraphQL). E-commerce businesses relying on these suppliers currently face operational inefficiencies:
1.  **Manual Labor:** Staff must manually check supplier websites to update local stock.
2.  **Overselling Risk:** Delays in manual checking lead to selling out-of-stock items.
3.  **Data Lag:** Pricing changes aren't reflected immediately.

## Solution Overview
This automation tool is a robust web scraper designed to bridge the gap between legacy HTML websites and modern inventory systems. It acts as a synthetic API by:
1.  Fetching the HTML content of the supplier's page.
2.  Parsing specific CSS selectors to extract SKU, Name, Stock, and Price.
3.  Cleaning the data (converting currency strings to floats, stock text to integers).
4.  Exporting a structured CSV or JSON file ready for import into Shopify, WooCommerce, or ERP systems.

## Prerequisites
- Python 3.8+
- Basic understanding of CSS selectors (to target specific elements on the supplier's site).

## Installation

1.  **Unzip the tool**:
    ```bash
    unzip no-api-inventory-sync.zip
    cd no-api-inventory-sync
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Run Demo Mode
To see the bot in action immediately, run it with the `--demo` flag. This creates a temporary local HTML file representing a legacy site, scrapes it, and outputs the data.

```bash
python inventory_sync_bot.py --demo --format json
```
*Check the directory for a new `.json` or `.csv` file containing parsed widget data.*

### 2. Run on a Real Website
You need to identify the CSS selectors for the target website (use Chrome DevTools -> Inspect Element).

**Example Command:**
```bash
python inventory_sync_bot.py \
  --url "https://legacy-supplier.com/products/list" \
  --sel-container ".product-item" \
  --sel-sku ".model-number" \
  --sel-stock ".inventory-count" \
  --sel-price ".current-price" \
  --format csv
```

### CLI Arguments
| Argument | Description |
| :--- | :--- |
| `--url` | The URL of the supplier page to scrape. |
| `--demo` | Runs the script against a locally generated mock file. |
| `--format` | Output format: `csv` (default) or `json`. |
| `--sel-container` | CSS selector for the row/div wrapping a single product. |
| `--sel-sku` | CSS selector for the SKU text inside the container. |
| `--sel-stock` | CSS selector for the stock level text. |
| `--sel-price` | CSS selector for the price text. |

## Recommendations
- **Scheduling:** Use `cron` (Linux) or Task Scheduler (Windows) to run this script every hour.
- **Rate Limiting:** If scraping many pages, add `time.sleep()` delays to avoid IP bans.
- **Error Handling:** The script currently logs errors but continues processing other items. Monitor the logs for layout changes on the supplier site.