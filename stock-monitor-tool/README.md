# Automated Inventory Monitor

## Problem Description
Monitoring modern websites for stock updates or appointment slots is difficult because many sites use JavaScript to render content dynamically. Simple HTTP requests (like `curl` or `requests`) often fail to retrieve the actual data because they do not execute the JavaScript code required to display the inventory status.

## Solution Overview
This tool uses **Selenium WebDriver** to launch a real Chrome browser instance (which can run headlessly). This allows the script to:
1. Fully render the web page, including all JavaScript.
2. Wait for specific dynamic elements to load.
3. Check the text or presence of elements to determine stock status.

**Note:** This solution is designed for legitimate monitoring of public data. It respects standard web technologies but does not include features designed to bypass CAPTCHAs, IP bans, or other security controls, as those practices can violate Terms of Service.

## Prerequisites
- Python 3.8 or higher
- Google Chrome browser installed on the machine

## Installation
1.  **Unzip the tool**:
    ```bash
    unzip stock-monitor-tool.zip
    cd stock-monitor-tool
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
Run the script from the command line by providing the target URL and the CSS selector (or XPath) of the element that contains the stock status.

### Basic Example
Check a product page every 30 seconds:
```bash
python inventory_monitor.py \
  --url "https://example.com/product-page" \
  --selector ".stock-status-label" \
  --type css \
  --interval 30
```

### Headless Mode (Server/Background)
Run without a visible browser window:
```bash
python inventory_monitor.py \
  --url "https://example.com/product-page" \
  --selector "//div[@id='add-to-cart']" \
  --type xpath \
  --interval 60 \
  --headless
```

## Configuration
- **Target Selector**: You must inspect the webpage (Right-click -> Inspect) to find the unique ID, Class, or XPath of the element that indicates stock availability.
- **Interval**: Adjust the `--interval` to balance between timely updates and not overwhelming the target server.

## Recommendations
- **Rate Limiting**: Do not set the interval too low (e.g., under 5 seconds) to avoid being blocked by the server for excessive traffic.
- **Selectors**: CSS selectors are generally faster and more robust than XPaths for simple element lookups.