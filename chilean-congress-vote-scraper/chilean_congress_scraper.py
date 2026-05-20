#!/usr/bin/env python3
"""
Chilean Congress Voting Data Scraper
======================================
Scrapes voting records from the Chilean Chamber of Deputies (Cámara de Diputados)
Open Data API. Extracts how every congressman voted on every bill from 2005 onward.

API Source: https://opendata.camara.cl/wscamaradiputados.asmx
Method: HTTP GET (no SOAP XML needed)

Usage:
    # Scrape bills 8000 through 9000, save to CSV
    python chilean_congress_scraper.py --start-bill 8000 --end-bill 9000

    # Scrape specific bills
    python chilean_congress_scraper.py --bills 8575-05,8576,8577

    # Resume from a previous run (skips already-fetched bills)
    python chilean_congress_scraper.py --start-bill 8000 --end-bill 9000 --resume

    # Output to custom directory
    python chilean_congress_scraper.py --start-bill 1 --end-bill 500 --output ./voting_data
"""

import argparse
import csv
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BASE_URL = "https://opendata.camara.cl/wscamaradiputados.asmx"
DEFAULT_OUTPUT_DIR = "voting_data"
REQUEST_DELAY = 1.0  # seconds between requests (be polite)
MAX_RETRIES = 3
RETRY_DELAY = 5.0  # seconds between retries

NS = {
    "temp": "http://tempuri.org/",
}

# ---------------------------------------------------------------------------
# API Helpers
# ---------------------------------------------------------------------------

def fetch_xml(url: str) -> str:
    """Fetch a URL and return the raw XML text with retry logic."""
    headers = {
        "User-Agent": "ChileanCongressScraper/1.0 (research project; contact: user@example.com)",
        "Accept": "text/xml, application/xml, */*",
    }
    req = Request(url, headers=headers)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except (HTTPError, URLError, OSError) as e:
            print(f"  [WARN] Request failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                raise


def get_votaciones_for_bill(bill_number: str) -> list[dict]:
    """
    Fetch all vote IDs for a given bill number.
    API: getVotaciones_Boletin?prmBoletin={bill_number}
    Returns list of vote dicts.
    Note: API returns raw XML (no SOAP envelope) with namespace http://tempuri.org/
    """
    url = f"{BASE_URL}/getVotaciones_Boletin?prmBoletin={quote(bill_number)}"
    raw = fetch_xml(url)

    votes = []
    try:
        root = ET.fromstring(raw)
        # API returns <Votaciones xmlns="http://tempuri.org/"> with <Votacion> children
        # No SOAP envelope – root is the response directly
        for v in root.findall("temp:Votacion", NS):
            vid = v.findtext("temp:ID", "", NS).strip()
            fecha = v.findtext("temp:Fecha", "", NS).strip()
            tipo = v.findtext("temp:Tipo", "", NS).strip()
            resultado = v.findtext("temp:Resultado", "", NS).strip()
            quorum = v.findtext("temp:Quorum", "", NS).strip()
            articulo = v.findtext("temp:Articulo", "", NS).strip()
            boletin = v.findtext("temp:Boletin", "", NS).strip()
            tramite = v.findtext("temp:Tramite", "", NS).strip()
            total_si = v.findtext("temp:TotalAfirmativos", "0", NS).strip()
            total_no = v.findtext("temp:TotalNegativos", "0", NS).strip()
            total_abs = v.findtext("temp:TotalAbstenciones", "0", NS).strip()
            total_dis = v.findtext("temp:TotalDispensados", "0", NS).strip()

            if vid:
                votes.append({
                    "id": vid,
                    "fecha": fecha,
                    "tipo": tipo,
                    "resultado": resultado,
                    "quorum": quorum,
                    "articulo": articulo,
                    "boletin": boletin if boletin else bill_number,
                    "tramite": tramite,
                    "bill_number": bill_number,
                    "total_afirmativos": total_si,
                    "total_negativos": total_no,
                    "total_abstenciones": total_abs,
                    "total_dispensados": total_dis,
                })
    except ET.ParseError as e:
        print(f"  [ERROR] XML parse error for bill {bill_number}: {e}")

    return votes


def get_votacion_detail(vote_id: str) -> dict | None:
    """
    Fetch detailed voting record for a specific vote ID.
    API: getVotacion_Detalle?prmVotacionID={vote_id}
    Returns dict with vote metadata and list of individual deputy votes.
    Note: API returns raw <Votacion xmlns="http://tempuri.org/"> directly (no SOAP)
    """
    url = f"{BASE_URL}/getVotacion_Detalle?prmVotacionID={quote(vote_id)}"
    raw = fetch_xml(url)

    try:
        root = ET.fromstring(raw)
        # API returns <Votacion xmlns="http://tempuri.org/"> directly (no SOAP envelope)
        votacion = root

        # Parse vote-level metadata
        meta = {
            "vote_id": vote_id,
            "fecha": votacion.findtext("temp:Fecha", "", NS).strip(),
            "tipo": votacion.findtext("temp:Tipo", "", NS).strip(),
            "resultado": votacion.findtext("temp:Resultado", "", NS).strip(),
            "quorum": votacion.findtext("temp:Quorum", "", NS).strip(),
            "articulo": votacion.findtext("temp:Articulo", "", NS).strip(),
            "boletin": votacion.findtext("temp:Boletin", "", NS).strip(),
            "tramite": votacion.findtext("temp:Tramite", "", NS).strip(),
            "informe": votacion.findtext("temp:Informe", "", NS).strip(),
            "total_si": votacion.findtext("temp:TotalAfirmativos", "0", NS).strip(),
            "total_no": votacion.findtext("temp:TotalNegativos", "0", NS).strip(),
            "total_abstencion": votacion.findtext("temp:TotalAbstenciones", "0", NS).strip(),
            "total_dispensado": votacion.findtext("temp:TotalDispensados", "0", NS).strip(),
        }

        # Parse individual deputy votes
        deputy_votes = []
        votos_elem = votacion.find("temp:Votos", NS)
        if votos_elem is not None:
            for voto in votos_elem.findall("temp:Voto", NS):
                diputado = voto.find("temp:Diputado", NS)
                if diputado is not None:
                    nombre = " ".join(filter(None, [
                        diputado.findtext("temp:Nombre", "", NS).strip(),
                        diputado.findtext("temp:Apellido_Paterno", "", NS).strip(),
                        diputado.findtext("temp:Apellido_Materno", "", NS).strip(),
                    ]))
                    deputy_votes.append({
                        "vote_id": vote_id,
                        "dip_id": diputado.findtext("temp:DIPID", "", NS).strip(),
                        "nombre": nombre,
                        "voto": voto.findtext("temp:Opcion", "", NS).strip(),
                    })
                else:
                    # Some votes have Diputado1/Diputado2 structure (replacement voters)
                    for key in ("temp:Diputado1", "temp:Diputado2"):
                        dip = voto.find(key, NS)
                        if dip is not None:
                            nombre = " ".join(filter(None, [
                                dip.findtext("temp:Nombre", "", NS).strip(),
                                dip.findtext("temp:Apellido_Paterno", "", NS).strip(),
                                dip.findtext("temp:Apellido_Materno", "", NS).strip(),
                            ]))
                            deputy_votes.append({
                                "vote_id": vote_id,
                                "dip_id": dip.findtext("temp:DIPID", "", NS).strip(),
                                "nombre": nombre,
                                "voto": voto.findtext("temp:Opcion", "", NS).strip(),
                                "reemplaza_a": key.replace("temp:", ""),
                            })

        return {
            "meta": meta,
            "deputy_votes": deputy_votes,
        }

    except ET.ParseError as e:
        print(f"  [ERROR] XML parse error for vote {vote_id}: {e}")
    return None


# ---------------------------------------------------------------------------
# CSV Writers
# ---------------------------------------------------------------------------

def write_votes_csv(output_dir: str, votes: list[dict], mode: str = "a"):
    """Write/append vote metadata to CSV."""
    path = Path(output_dir) / "votes.csv"
    fieldnames = ["id", "fecha", "tipo", "resultado", "quorum", "articulo", "boletin", "bill_number", "tramite", "total_afirmativos", "total_negativos", "total_abstenciones", "total_dispensados"]
    write_header = not path.exists() or mode == "w"

    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for v in votes:
            # Only write fields that exist in fieldnames
            writer.writerow({k: v.get(k, "") for k in fieldnames})


def write_deputies_csv(output_dir: str, deputy_votes: list[dict], mode: str = "a"):
    """Write/append individual deputy vote records to CSV."""
    path = Path(output_dir) / "deputy_votes.csv"
    if not deputy_votes:
        return
    fieldnames = ["vote_id", "dip_id", "nombre", "voto", "reemplaza_a"]
    write_header = not path.exists() or mode == "w"

    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for dv in deputy_votes:
            writer.writerow({k: dv.get(k, "") for k in fieldnames})


def write_vote_details_csv(output_dir: str, details: list[dict], mode: str = "a"):
    """Write/append vote detail metadata to CSV."""
    path = Path(output_dir) / "vote_details.csv"
    if not details:
        return
    fieldnames = ["vote_id", "fecha", "tipo", "resultado", "quorum", "articulo", "boletin", "tramite", "informe", "total_si", "total_no", "total_abstencion", "total_dispensado"]
    write_header = not path.exists() or mode == "w"

    with open(path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for d in details:
            writer.writerow({k: d.get(k, "") for k in fieldnames})


# ---------------------------------------------------------------------------
# Progress Tracking (for resume)
# ---------------------------------------------------------------------------

def load_progress(output_dir: str) -> set:
    """Load already-completed bill numbers from progress file."""
    path = Path(output_dir) / ".progress.json"
    if path.exists():
        with open(path) as f:
            return set(json.load(f))
    return set()


def save_progress(output_dir: str, completed: set):
    """Save completed bill numbers to progress file."""
    path = Path(output_dir) / ".progress.json"
    with open(path, "w") as f:
        json.dump(sorted(completed), f, indent=2)


# ---------------------------------------------------------------------------
# Main Scraper Logic
# ---------------------------------------------------------------------------

def scrape_bills(
    bill_numbers: list[str],
    output_dir: str,
    resume: bool = False,
    delay: float = REQUEST_DELAY,
):
    """
    Scrape voting data for a list of bill numbers.
    
    Args:
        bill_numbers: List of bill numbers to scrape
        output_dir: Directory to save output files
        resume: If True, skip already-completed bills
        delay: Delay between API requests in seconds
    """
    os.makedirs(output_dir, exist_ok=True)
    completed = load_progress(output_dir) if resume else set()

    total_bills = len(bill_numbers)
    total_votes_found = 0
    total_deputy_votes = 0
    errors = []

    print(f"{'='*60}")
    print(f"Chilean Congress Voting Data Scraper")
    print(f"{'='*60}")
    print(f"Output directory: {output_dir}")
    print(f"Total bills to process: {total_bills}")
    print(f"Resume mode: {'ON (skipping ' + str(len(completed)) + ' completed)' if resume else 'OFF'}")
    print(f"{'='*60}\n")

    start_time = time.time()

    for idx, bill in enumerate(bill_numbers):
        if resume and bill in completed:
            print(f"[{idx+1}/{total_bills}] ⏭ Skipping bill {bill} (already completed)")
            continue

        print(f"[{idx+1}/{total_bills}] 🔍 Processing bill {bill}...", end=" ", flush=True)

        try:
            # Step 1: Get votes for this bill
            votes = get_votaciones_for_bill(bill)
            time.sleep(delay)

            if not votes:
                print("no votes found")
                if resume:
                    completed.add(bill)
                    save_progress(output_dir, completed)
                continue

            print(f"{len(votes)} vote(s) found")

            # Step 2: Write basic vote listing
            write_votes_csv(output_dir, votes)
            total_votes_found += len(votes)

            # Step 3: For each vote, get detailed record
            for v in votes:
                print(f"         └─ Fetching vote {v['id']}...", end=" ", flush=True)
                detail = get_votacion_detail(v["id"])
                time.sleep(delay)

                if detail is None:
                    print("FAILED")
                    errors.append(f"bill={bill}, vote={v['id']}: detail fetch failed")
                    continue

                meta = detail["meta"]
                deputy_votes = detail["deputy_votes"]

                # Write vote detail metadata
                write_vote_details_csv(output_dir, [meta])

                # Write individual deputy votes
                if deputy_votes:
                    write_deputies_csv(output_dir, deputy_votes)
                    total_deputy_votes += len(deputy_votes)

                print(f"OK ({len(deputy_votes)} deputies)")

            # Mark bill as completed
            if resume:
                completed.add(bill)
                save_progress(output_dir, completed)

        except (HTTPError, URLError, OSError, ET.ParseError) as e:
            print(f"ERROR: {e}")
            errors.append(f"bill={bill}: {e}")
            # Continue to next bill

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"SCRAPE COMPLETE")
    print(f"{'='*60}")
    print(f"Bills processed:  {total_bills}")
    print(f"Votes found:      {total_votes_found}")
    print(f"Deputy votes:     {total_deputy_votes}")
    print(f"Errors:           {len(errors)}")
    print(f"Time elapsed:     {elapsed:.1f}s")
    print(f"Output:           {os.path.abspath(output_dir)}/")
    print(f"{'='*60}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  - {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    # Write summary file
    summary = {
        "scraped_at": datetime.now().isoformat(),
        "bills_processed": total_bills,
        "votes_found": total_votes_found,
        "deputy_votes_collected": total_deputy_votes,
        "errors": len(errors),
        "error_list": errors[:50],
        "output_dir": output_dir,
    }
    with open(Path(output_dir) / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Bill Number Helpers
# ---------------------------------------------------------------------------

def generate_bill_range(start: int, end: int) -> list[str]:
    """Generate a list of bill numbers from start to end (inclusive)."""
    return [str(n) for n in range(start, end + 1)]


def parse_bill_list(bills_str: str) -> list[str]:
    """Parse comma-separated bill numbers (e.g., '8575-05,8576,8577')."""
    return [b.strip() for b in bills_str.split(",") if b.strip()]


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Chilean Congress Voting Data Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chilean_congress_scraper.py --start-bill 8000 --end-bill 9000
  python chilean_congress_scraper.py --bills 8575-05,8576,8577
  python chilean_congress_scraper.py --start-bill 1 --end-bill 500 --output ./mi_data --resume
        """,
    )
    parser.add_argument(
        "--start-bill",
        type=int,
        help="First bill number in range (inclusive)",
    )
    parser.add_argument(
        "--end-bill",
        type=int,
        help="Last bill number in range (inclusive)",
    )
    parser.add_argument(
        "--bills",
        type=str,
        help="Comma-separated list of specific bill numbers",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous run (skips already-completed bills)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY,
        help=f"Delay between API requests in seconds (default: {REQUEST_DELAY})",
    )

    args = parser.parse_args()

    # Determine bill list
    bill_numbers = []
    if args.bills:
        bill_numbers = parse_bill_list(args.bills)
    elif args.start_bill and args.end_bill:
        bill_numbers = generate_bill_range(args.start_bill, args.end_bill)
    else:
        parser.print_help()
        print("\n[ERROR] Either --bills or --start-bill + --end-bill is required.")
        sys.exit(1)

    if not bill_numbers:
        print("[ERROR] No bill numbers provided.")
        sys.exit(1)

    print(f"Bill count: {len(bill_numbers)}")
    if len(bill_numbers) > 10:
        print(f"Range: {bill_numbers[0]} → {bill_numbers[-1]}")
    else:
        print(f"Bills: {', '.join(bill_numbers)}")

    scrape_bills(bill_numbers, args.output, resume=args.resume, delay=args.delay)


if __name__ == "__main__":
    main()
