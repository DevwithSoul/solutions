# Automated Stock & Price Monitor

## Problem Description
Modern e-commerce websites use Single Page Application (SPA) frameworks (React, Vue, Angular) that render content dynamically using JavaScript. Traditional HTTP-request based scrapers (like BeautifulSoup) fail here because the HTML is empty until JS executes. Furthermore, these sites employ anti-bot measures that detect automated scripts based on browsing patterns and browser fingerprints.

## Solution Overview
This solution utilizes **Python** and **Playwright**. Unlike Selenium, Playwright is faster, more reliable for modern web apps, and offers better control over the browser context.

**Key Features:**
1.  **Full JS Rendering:** Uses a headless Chromium browser to execute JavaScript, ensuring dynamic prices and stock levels are visible.
2.  **Human Mimicry:** Implements random mouse movements, scrolling, and randomized wait intervals to evade basic heuristic bot detection.
3.  **Stealth Context:** Modifies browser flags (e.g., `navigator.webdriver`) and User-Agents to appear as a standard desktop user.
4.  **Alerting System:** Detects changes in price or stock status and triggers a placeholder alert (extensible to Email/SMS).

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Installation

1.  **Install Python Dependencies**
    ```bash
    pip install playwright
    ```

2.  **Install Playwright Browsers**
    This downloads the necessary browser binaries (Chromium, Firefox, WebKit).
    ```bash
    playwright install chromium
    ```

## Usage

1.  **Configuration**
    Open `stock_monitor.py` and modify the `config` dictionary at the bottom of the file:
    - `url`: The target product page.
    - `selectors`: CSS selectors for the price and stock elements (Inspect Element in your browser to find these).
    - `interval_range`: Min and max seconds to wait between checks.

2.  **Run the Monitor**
    ```bash
    python stock_monitor.py
    ```

3.  **Logs**
    - Execution logs are printed to the console.
    - A detailed `monitor.log` file is created in the same directory.
    - If an error occurs, a screenshot is saved as `error_TIMESTAMP.png`.

## Recommendations
- **Proxies:** For high-frequency monitoring, integrate a rotating residential proxy service within the Playwright launch arguments to avoid IP bans.
- **Docker:** To run this continuously on a server (AWS/DigitalOcean), wrap this script in a Docker container.
- **Selectors:** Websites change their layout. If the script stops working, check if the CSS selectors in the config need updating.