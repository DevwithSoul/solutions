# Ontario Municipal Election Candidate Scraper

## Problem Description

A parent asked for help on Reddit — their Grade 7 child needed to build a list of candidates running in all 414 municipalities across Ontario, Canada for a school project on municipal elections. The data is spread across dozens of municipal websites with no central database.

## Solution Overview

A Python scraper that:
1. Fetches the complete list of 414 Ontario municipalities from Wikipedia
2. For each municipality, attempts to find the official website using common URL patterns
3. Locates elections/candidate pages on those websites
4. Extracts candidate names and positions (Mayor, Councillor, Trustee, etc.)
5. Outputs everything to CSV, JSON, and a formatted report

## Prerequisites

- Python 3.8+
- `requests` and `beautifulsoup4` (see requirements.txt)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic usage — process all municipalities
```bash
python ontario_election_scraper.py
```

### Test with a small number first
```bash
python ontario_election_scraper.py --limit 5
```

### Resume a previous run (skips already-processed)
```bash
python ontario_election_scraper.py --resume
```

### Just get the municipality list (no scraping)
```bash
python ontario_election_scraper.py --list-only
```

### Custom output directory + faster/slower speed
```bash
python ontario_election_scraper.py --output ./my_report --delay 0.5
```

### Clear cache and start fresh
```bash
python ontario_election_scraper.py --clear-cache
```

## Output

All files go into the `output/` directory (configurable with `--output`):

| File | Description |
|------|-------------|
| `ontario_municipal_elections.csv` | Full dataset — one row per municipality |
| `ontario_municipal_elections.json` | Structured JSON with all candidate details |
| `REPORT.md` | Human-readable summary report |
| `.cache/municipalities.json` | Cached municipality list (for resume) |
| `.cache/progress.json` | Progress tracking (for resume) |

## Configuration

- **Delay:** 1 second between requests by default (respectful to websites). Adjust with `--delay`.
- **Output directory:** `./output` by default. Change with `--output`.
- **Resume:** Uses `.cache/progress.json` to skip already-processed municipalities.

## Recommendations

- Run with `--limit 10` first to verify the tool works for your region
- Municipal websites vary — the scraper does its best but may miss some candidate pages
- For the most accurate data, contact each municipal clerk's office directly
- Ontario municipal elections are held every 4 years (most recently 2022, next in 2026)
