# The Infinite Scroll Scraper

## Problem Description
Modern web development relies heavily on JavaScript to render content dynamically. Traditional scraping tools (like BeautifulSoup or basic requests) fetch the initial HTML state, which often lacks the actual data. Furthermore, "Infinite Scroll" patterns require user interaction (scrolling) to trigger AJAX calls that load subsequent pages of data. Users currently cannot access thousands of hidden records on these sites.

## Solution Overview
This solution utilizes **Playwright**, a powerful browser automation library, to create a "Headless Browser" scraper. 

**Key Features:**
1.  **Browser Simulation**: Launches a real Chromium browser (headless or visible) to execute JavaScript.
2.  **Smart Scrolling Logic**: Automatically detects page height, scrolls to the bottom, and waits for content to hydrate.
3.  **Dynamic Extraction**: Allows passing custom extraction logic to parse specific DOM elements once they are rendered.
4.  **Export**: Saves data to structured JSON format.

## Prerequisites
- Python 3.8 or higher
- pip (Python Package Manager)

## Installation

1.  **Install Python Dependencies**:
    ```bash
    pip install playwright
    ```

2.  **Install Playwright Browsers**:
    Playwright needs to download the browser binaries to function.
    ```bash
    playwright install chromium
    ```

## Usage

1.  **Configure the Script**:
    Open `infinite_scroll_scraper.py`. In the `__main__` block, adjust the following variables:
    - `TARGET_URL`: The website you want to scrape.
    - `TARGET_SELECTOR`: The CSS selector for the repeating item (e.g., `.product-card`, `.tweet`).
    - `extract_quote_data`: Update this function to select the specific text/attributes you need from each item.

2.  **Run the Scraper**:
    ```bash
    python infinite_scroll_scraper.py
    ```

3.  **Output**:
    The script will generate `scraped_quotes.json` (or your defined output name) containing the structured data.

## Recommendations
- **Rate Limiting**: The `scroll_delay` parameter is crucial. Setting it too low (e.g., < 500ms) may trigger anti-bot protections or result in incomplete page loads. 2000ms is a safe default.
- **Headless Mode**: Set `headless=True` for production servers (faster, no UI). Set `headless=False` for debugging to see what the bot is doing.
- **Selectors**: Use browser Developer Tools (F12) to find unique CSS classes for the items you wish to scrape.