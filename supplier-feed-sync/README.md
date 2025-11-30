# Automated Supplier Feed Sync

## Problem Description
Legacy supplier systems often export data in monolithic CSV or XML files that are difficult to synchronize with modern RESTful APIs. Developers face challenges such as:
- **Memory Overheads:** Loading large feeds (100k+ items) entirely into RAM crashes scripts.
- **Rate Limits:** Sending updates too fast triggers API 429 errors.
- **Data Integrity:** Blindly updating all products risks overwriting custom data or causing unnecessary load.

## Solution Overview
This Python middleware solves these issues by acting as an intelligent bridge. 

**Key Features:**
1. **Stream Processing:** Reads the supplier feed line-by-line, keeping memory footprint negligible regardless of file size.
2. **Smart Diffing:** Maintains a local `sync_state.json` file containing hashes of product data. Only products that have actually changed (or are new) are queued for update.
3. **Batching:** Groups updates into configurable chunks (default: 50) to reduce HTTP overhead and respect API limits.

## Prerequisites
- Python 3.7+
- `requests` library

## Installation
1. Extract the tool.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Quick Test (Local)
Generate a sample CSV and run a dry-run sync:
```bash
# Create sample data
python supplier_sync.py --create-sample

# Run sync (defaults to using the local 'supplier_data.csv')
python supplier_sync.py --dry-run
```

### 2. Production Usage
Sync a remote CSV feed to your API:
```bash
python supplier_sync.py \
  --feed-url "https://supplier.com/feeds/daily_products.csv" \
  --api-url "https://api.yourstore.com/v1" \
  --api-key "YOUR_ACTUAL_API_KEY" \
  --batch-size 100
```

## Configuration

| Argument | Description | Default |
|----------|-------------|---------|
| `--feed-url` | URL or local path to CSV | `supplier_data.csv` |
| `--api-url` | Target API base URL | `https://api.mystore.com/v1` |
| `--api-key` | Auth token for API | `test_key` |
| `--batch-size` | Items per API request | `50` |
| `--dry-run` | Log actions without sending requests | `False` |

## Recommendations
- **Cron Job:** Schedule this script to run hourly or daily via crontab.
- **State File:** Ensure `sync_state.json` persists between runs. If running in a container (Docker), mount a volume for this file to avoid re-syncing the entire catalog every restart.