# Chilean Congress Voting Data Scraper

## Problem Description

A Reddit user in r/webscraping needed help extracting voting records from the Chilean Chamber of Deputies (Cámara de Diputados) Open Data portal. They wanted to build a database of how every congressman voted on every bill from **2005 to present** — but the official website requires looking up each bill and each vote ID manually, one by one. With thousands of bills and votes, this is impossible to do by hand.

The data is available through a SOAP web service at `opendata.camara.cl`, but the user had no experience with web scraping or SOAP APIs.

## Solution Overview

A Python script that automates the entire extraction process:

1. **Discovers votes** for a range of bill numbers via `getVotaciones_Boletin`
2. **Fetches full voting details** for each vote via `getVotacion_Detalle` — including how every individual deputy voted (yea/nay/abstain)
3. **Exports structured data** to CSV files ready for analysis in Excel, Python, R, or SQL
4. **Supports resume**: if the script is interrupted, it picks up where it left off
5. **Rate-limited & polite**: respects the server with configurable delays

### What you get

| File | Description |
|------|-------------|
| `votes.csv` | Every vote found for each bill (vote ID, date, description) |
| `vote_details.csv` | Metadata for each vote (totals, type, result, quorum) |
| `deputy_votes.csv` | **Individual deputy voting records** (who voted what) |
| `summary.json` | Summary of the scrape run |
| `.progress.json` | Progress tracker (used by `--resume`) |

### Sample `deputy_votes.csv` structure

| vote_id | dip_id | nombre | sexo | region | distrito | militancia | voto |
|---------|--------|--------|------|--------|----------|------------|------|
| 16197 | 1234 | Juan Pérez González | M | Metropolitana | 11 | Partido X | A Favor |
| 16197 | 5678 | María López Soto | F | Valparaíso | 7 | Partido Y | En Contra |

## Prerequisites

- **Python 3.7+** (no external packages required — uses only stdlib)
- Internet connection to access `opendata.camara.cl`

## Installation

```bash
# Clone or download this repository
cd chilean-congress-vote-scraper

# No pip install needed — the script uses Python's built-in libraries only:
#   xml.etree.ElementTree, urllib.request, csv, json, argparse, time, os, sys, pathlib
```

## Usage

### Basic usage — scrape a range of bill numbers

```bash
python chilean_congress_scraper.py --start-bill 8000 --end-bill 9000
```

### Scrape specific bills

```bash
python chilean_congress_scraper.py --bills 8575-05,8576,8577,9001
```

### Resume an interrupted scrape

```bash
python chilean_congress_scraper.py --start-bill 8000 --end-bill 9000 --resume
```

### Custom output directory

```bash
python chilean_congress_scraper.py --start-bill 1 --end-bill 500 --output ./congress_data
```

### Run with a longer delay (if rate-limited)

```bash
python chilean_congress_scraper.py --start-bill 8000 --end-bill 8100 --delay 2.5
```

## Configuration

The script exposes these command-line options:

| Argument | Default | Description |
|----------|---------|-------------|
| `--start-bill` | — | First bill number in range (use with `--end-bill`) |
| `--end-bill` | — | Last bill number in range (use with `--start-bill`) |
| `--bills` | — | Comma-separated list of bill numbers |
| `--output` | `voting_data` | Output directory for CSV files |
| `--resume` | `false` | Skip already-completed bills |
| `--delay` | `1.0` | Seconds between API requests |

## API Endpoints Used

Both endpoints use **HTTP GET** (no SOAP XML envelope needed):

- **`getVotaciones_Boletin`**: `GET /wscamaradiputados.asmx/getVotaciones_Boletin?prmBoletin={bill_number}`
  Returns all vote IDs associated with a bill number.

- **`getVotacion_Detalle`**: `GET /wscamaradiputados.asmx/getVotacion_Detalle?prmVotacionID={vote_id}`
  Returns full voting details including how each deputy voted.

Full API documentation: https://opendata.camara.cl/wscamaradiputados.asmx

## Recommendations

1. **Start small** — test with `--bills 8575-05,8576` to verify the output format
2. **Use `--resume`** — the Chilean Congress API is a public service; be respectful and use resume so you can stop/continue
3. **Bill number ranges** — Chilean bills range from roughly 1 to 18,000+. Start with recent bills (higher numbers) and work backwards
4. **Data analysis** — load `deputy_votes.csv` into pandas, R, or Excel for analysis:
   ```python
   import pandas as pd
   df = pd.read_csv("voting_data/deputy_votes.csv")
   # How many times did each deputy vote "A Favor"?
   df[df["voto"] == "A Favor"].groupby("nombre").size().sort_values(ascending=False)
   ```
5. **Be polite** — the default 1-second delay keeps the load reasonable on the public API

## License

MIT
