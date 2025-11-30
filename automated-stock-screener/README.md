# Automated Fundamental Stock Screener

## Problem Description
Investors often spend hours manually copying financial statements (Income Statement, Balance Sheet) from websites into Excel to calculate valuation metrics. This manual process is prone to errors and makes it difficult to screen a large list of stocks for quality metrics like Return on Invested Capital (ROIC).

## Solution Overview
This Python-based automation tool connects directly to the **Financial Modeling Prep (FMP) API**. It:
1. Fetches the latest Annual Income Statement and Balance Sheet for provided tickers.
2. Automatically cleans the data.
3. Calculates derived metrics that aren't always provided by default, specifically **ROIC (Return on Invested Capital)** and **Net Margin**.
4. Exports the results to a clean CSV file, sorted by ROIC (High Quality first).

## Prerequisites
1. **Python 3.8+** installed.
2. **API Key**: You need a free API key from [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs/). The free tier is sufficient for basic testing.

## Installation

1. Unzip the tool folder.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script from the command line, providing your API key and a list of tickers you want to analyze.

### Syntax
```bash
python fundamental_screener.py --api-key YOUR_KEY --tickers LIST_OF_TICKERS
```

### Example
```bash
python fundamental_screener.py --api-key abc12345 --tickers AAPL,MSFT,TSLA,NVDA,JNJ
```

## Output
The script will generate a file named `screener_results.csv` in the same directory.

**Example Output Data:**
| Ticker | Revenue ($B) | Invested Capital ($B) | ROIC (%) | Net Margin (%) |
|--------|--------------|-----------------------|----------|----------------|
| NVDA   | 60.9         | 45.2                  | 45.3     | 48.8           |
| AAPL   | 383.2        | 120.5                 | 58.2     | 25.3           |

## Logic Explanation
- **NOPAT**: Calculated as `Operating Income * (1 - Tax Rate)`.
- **Invested Capital**: Calculated as `Total Equity + Total Debt - Cash`.
- **ROIC**: `NOPAT / Invested Capital`.

## Recommendations
- For production use, consider adding the `rate_limit` handling if you are analyzing thousands of stocks.
- The script currently fetches the most recent annual report (`limit=1`). You can modify the code to fetch historical data for trend analysis.