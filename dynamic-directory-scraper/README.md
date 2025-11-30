# The Dynamic Directory Scraper

## Problem Description
Modern websites often use techniques like Infinite Scrolling (lazy loading) or "Load More" buttons to display large datasets. Standard HTTP libraries (like Python's `requests`) cannot retrieve this data because it isn't present in the initial HTML response—it is loaded dynamically via JavaScript as the user interacts with the page.

## Solution Overview
This solution utilizes **Playwright**, a powerful browser automation library, to simulate a real user.

**Key Features:**
1.  **Headless Browser Automation:** Renders the full DOM and executes JavaScript.
2.  **Dual Strategy Support:** 
    *   `scroll`: Automatically scrolls to the bottom to trigger infinite loading.
    *   `click`: Finds and clicks a "Load More" / "Next" button.
3.  **Smart Waiting:** Waits for network idle states to ensure data is loaded before scraping.
4.  **Structured Export:** Saves data automatically to JSON or CSV.

## Prerequisites
*   Python 3.7+
*   pip (Python package manager)

## Installation

1.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install Playwright Browsers:**
    Playwright requires its own browser binaries to function.
    ```bash
    playwright install
    ```

## Usage

### 1. Basic Usage (Infinite Scroll)
The script defaults to a test sandbox (`quotes.toscrape.com/scroll`) to demonstrate functionality immediately.

```bash
python dynamic_scraper.py
```

### 2. Custom Infinite Scroll Target
To scrape a different site with infinite scroll:

```bash
python dynamic_scraper.py \
  --url "https://example.com/blog" \
  --selector ".post-item" \
  --limit 100 \
  --output blog_posts.json
```

### 3. "Load More" Button Strategy
If the site requires clicking a button to see more results:

```bash
python dynamic_scraper.py \
  --url "https://example.com/products" \
  --selector ".product-card" \
  --strategy click \
  --button ".load-more-btn" \
  --limit 50
```

### 4. Headless Mode
For production/server environments (runs faster without UI):

```bash
python dynamic_scraper.py --headless
```

## Configuration Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--url` | Target website URL | `http://quotes.toscrape.com/scroll` |
| `--selector` | CSS selector for the data items | `.quote` |
| `--output` | Output filename (.json or .csv) | `results.json` |
| `--limit` | Max items to scrape | `50` |
| `--strategy` | `scroll` or `click` | `scroll` |
| `--button` | CSS selector for the button (if strategy is click) | `None` |
| `--headless` | Run without visible browser window | `False` |

## Recommendations
*   **Selectors:** Use browser Developer Tools (F12) to find unique CSS selectors (classes or IDs) for the items you want to scrape.
*   **Rate Limiting:** The script includes small sleeps (`asyncio.sleep`) to simulate human behavior. Do not remove these if scraping real sites to avoid IP bans.
*   **Dynamic Content:** If a site is very slow, increase the timeout values in the `scroll_to_bottom` or `wait_for_load_state` methods.