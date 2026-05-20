#aiwebarchitects
import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

WIKI_API = "https://en.wikipedia.org/w/api.php"
AMO_URL = "https://www.amo.on.ca/about-us/municipal-101/ontario-municipalities"
ONTARIO_CA_URL = "https://www.ontario.ca/page/list-ontario-municipalities"
USER_AGENT = "OntarioElectionScraper/1.0 (student project; contact: parent@example.com)"
HEADERS = {"User-Agent": USER_AGENT}
REQUEST_DELAY = 1.0

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

class OntarioMunicipalityScraper:
    def __init__(self, output_dir="output", delay=REQUEST_DELAY, resume=False):
        self.output_dir = output_dir
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.municipalities = []
        self.results = []
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.cache_file = os.path.join(CACHE_DIR, "municipalities.json")
        self.progress_file = os.path.join(CACHE_DIR, "progress.json")
        if resume:
            self._load_progress()

    def _request(self, url, params=None):
        time.sleep(self.delay)
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            return None

    def fetch_municipality_list(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file) as f:
                self.municipalities = json.load(f)
            logger.info(f"Loaded {len(self.municipalities)} municipalities from cache")
            return self.municipalities

        logger.info("Fetching municipality list from Wikipedia...")
        params = {
            "action": "parse",
            "page": "List_of_municipalities_in_Ontario",
            "prop": "text",
            "format": "json"
        }
        resp = self._request(WIKI_API, params=params)
        if not resp:
            logger.error("Failed to fetch Wikipedia page")
            return []

        data = resp.json()
        html = data["parse"]["text"]["*"]
        tables = re.findall(r'<table[^>]*wikitable[^>]*>.*?</table>', html, re.DOTALL)

        if len(tables) < 2:
            logger.error("Could not find municipality table on Wikipedia")
            return []

        table = tables[1]
        rows = re.findall(r'<tr>.*?</tr>', table, re.DOTALL)

        for row in rows:
            # Municipality name is in <th scope="row"> element
            th_match = re.search(r'<th[^>]*>(.*?)</th>', row, re.DOTALL)
            if not th_match:
                continue

            name_html = th_match.group(1)
            name_link = re.search(r'<a[^>]*>(.*?)</a>', name_html)
            if name_link:
                name = re.sub(r'<[^>]+>', '', name_link.group(1)).strip()
            else:
                name = re.sub(r'<[^>]+>', '', name_html).strip()
            name = re.sub(r'\[\w+\]', '', name).strip()
            if not name or name.lower() in ('name', 'municipality'):
                continue

            # Data cells follow the <th>
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(cells) < 4:
                continue

            status = re.sub(r'<[^>]+>', '', cells[0]).strip()
            m_type = re.sub(r'<[^>]+>', '', cells[1]).strip()
            division = re.sub(r'<[^>]+>', '', cells[2]).strip()

            pop = re.sub(r'<[^>]+>', '', cells[3]).strip() if len(cells) > 3 else ''

            self.municipalities.append({
                "name": name,
                "status": status,
                "type": m_type,
                "division": division,
                "population": pop,
                "website": "",
                "candidate_page": "",
                "election_year": datetime.now().year
            })

        with open(self.cache_file, "w") as f:
            json.dump(self.municipalities, f, indent=2)

        logger.info(f"Found {len(self.municipalities)} municipalities")
        return self.municipalities

    def find_municipality_website(self, muni):
        if muni["website"]:
            return muni["website"]

        # Try common URL patterns for Ontario municipalities
        name_slug = muni["name"].lower()
        name_slug = re.sub(r'[^a-z0-9]+', '-', name_slug).strip('-')
        name_slug = re.sub(r'^-+|-+$', '', name_slug)

        patterns = [
            f"https://www.{name_slug}.ca",
            f"https://{name_slug}.ca",
            f"https://town.{name_slug}.on.ca",
            f"https://www.{name_slug}.on.ca",
            f"https://cityof{name_slug}.ca",
            f"https://www.townof{name_slug}.ca",
            f"https://www.townshipof{name_slug}.ca",
            f"https://municipalityof{name_slug}.ca",
            f"https://{name_slug}.municipalwebsites.ca"
        ]

        for pattern in patterns:
            resp = self._request(pattern)
            if resp and resp.status_code == 200:
                logger.info(f"  Found website: {pattern}")
                muni["website"] = pattern
                return pattern

        logger.debug(f"  No website found for {muni['name']}")
        return ""

    def find_candidate_page(self, muni):
        if muni["candidate_page"]:
            return muni["candidate_page"]

        website = muni["website"]
        if not website:
            return ""

        election_paths = [
            "/elections",
            "/municipal-election",
            "/town-hall/elections",
            "/government/elections",
            "/election",
            "/your-government/elections",
            "/municipal-government/elections",
            "/departments/clerk/elections",
            "/elections/candidates",
            "/candidates",
            "/news/elections"
        ]

        for path in election_paths:
            url = urljoin(website, path)
            resp = self._request(url)
            if resp and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                page_text = soup.get_text().lower()
                if "candidate" in page_text or "election" in page_text or "nomination" in page_text:
                    logger.info(f"  Found candidate page: {url}")
                    muni["candidate_page"] = url
                    return url
                logger.debug(f"  Page found but no candidate info: {url}")

        return ""

    def scrape_candidates(self, url):
        if not url:
            return []

        resp = self._request(url)
        if not resp:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text()
        candidates = []

        # Look for candidate names in common patterns
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Match patterns like "John Doe - Mayor" or "John Doe (Mayor)"
            for pos in ["Mayor", "Councillor", "Councillor Ward", "Regional Councillor",
                        "Trustee", "Deputy Mayor", "Reeve", "Deputy Reeve"]:
                if pos.lower() in line.lower():
                    name_match = re.match(r'^([A-Za-zÀ-ÿ\-\'\s]+)', line)
                    if name_match:
                        name = name_match.group(1).strip()
                        if len(name) > 3:
                            candidates.append({"name": name, "position": pos})
                            break

        # Also try looking for patterns in HTML lists
        for tag in ["ul", "ol"]:
            lists = soup.find_all(tag)
            for lst in lists:
                items = lst.find_all("li")
                for item in items:
                    item_text = item.get_text(strip=True)
                    if not item_text:
                        continue
                    for pos in ["Mayor", "Councillor", "Trustee", "Reeve"]:
                        if pos.lower() in item_text.lower():
                            name_match = re.match(r'^([A-Za-zÀ-ÿ\-\'\s\.]+)', item_text)
                            if name_match:
                                name = name_match.group(1).strip()
                                if len(name) > 3:
                                    candidates.append({"name": name, "position": pos})
                            break

        return candidates

    def process_municipality(self, muni):
        logger.info(f"Processing: {muni['name']} ({muni['status']})")
        result = dict(muni)
        result["website_found"] = False
        result["candidate_page_found"] = False
        result["candidates"] = []

        website = self.find_municipality_website(muni)
        if website:
            result["website_found"] = True
            candidate_url = self.find_candidate_page(muni)
            if candidate_url:
                result["candidate_page_found"] = True
                candidates = self.scrape_candidates(candidate_url)
                result["candidates"] = candidates
                logger.info(f"  Found {len(candidates)} candidate(s)")

        return result

    def _load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file) as f:
                data = json.load(f)
            self.results = data.get("results", [])
            logger.info(f"Resumed with {len(self.results)} already processed")

    def _save_progress(self):
        with open(self.progress_file, "w") as f:
            json.dump({"results": self.results, "updated": datetime.now().isoformat()}, f, indent=2)

    def run(self, limit=None):
        self.fetch_municipality_list()

        processed_names = {r["name"] for r in self.results}
        to_process = [m for m in self.municipalities if m["name"] not in processed_names]

        if limit:
            to_process = to_process[:limit]

        logger.info(f"Processing {len(to_process)} municipalities ({len(processed_names)} already done)")

        for i, muni in enumerate(to_process):
            logger.info(f"[{i+1}/{len(to_process)}] {muni['name']}")
            result = self.process_municipality(muni)
            self.results.append(result)
            self._save_progress()

            if (i + 1) % 25 == 0:
                self._export_csv()

        self._export_csv()
        self._export_json()
        self._generate_report()
        return self.results

    def _export_csv(self):
        path = os.path.join(self.output_dir, "ontario_municipal_elections.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Municipality", "Status", "Type", "Division", "Population",
                "Website", "Candidate Page", "Candidates Found"
            ])
            for r in self.results:
                candidate_names = "; ".join(
                    f"{c['name']} ({c['position']})" for c in r.get("candidates", [])
                ) if r.get("candidates") else ""
                writer.writerow([
                    r["name"], r["status"], r["type"], r["division"], r["population"],
                    r.get("website", ""), r.get("candidate_page", ""), candidate_names
                ])
        logger.info(f"CSV exported: {path} ({len(self.results)} rows)")

    def _export_json(self):
        path = os.path.join(self.output_dir, "ontario_municipal_elections.json")
        summary = {
            "generated": datetime.now().isoformat(),
            "total_municipalities": len(self.results),
            "websites_found": sum(1 for r in self.results if r.get("website_found")),
            "candidate_pages_found": sum(1 for r in self.results if r.get("candidate_page_found")),
            "municipalities_with_candidates": sum(1 for r in self.results if r.get("candidates")),
            "total_candidates_found": sum(len(r.get("candidates", [])) for r in self.results),
            "results": self.results
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info(f"JSON exported: {path}")

    def _generate_report(self):
        path = os.path.join(self.output_dir, "REPORT.md")
        total = len(self.results)
        websites = sum(1 for r in self.results if r.get("website_found"))
        cand_pages = sum(1 for r in self.results if r.get("candidate_page_found"))
        with_cands = sum(1 for r in self.results if r.get("candidates"))
        total_cands = sum(len(r.get("candidates", [])) for r in self.results)

        lines = [
            f"# Ontario Municipal Elections {datetime.now().year} - Candidate Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
            f"| Metric | Count |",
            f"|--------|-------|",
            f"| Total Municipalities | {total} |",
            f"| Websites Found | {websites} ({websites/total*100:.1f}%) |",
            f"| Candidate Pages Found | {cand_pages} ({cand_pages/total*100:.1f}%) |",
            f"| Municipalities with Candidate Data | {with_cands} ({with_cands/total*100:.1f}%) |",
            f"| Total Candidates Found | {total_cands} |",
            "",
            "## Notes",
            "",
            "- Candidate lists are collected from official municipal websites.",
            "- Not all municipalities publish candidate lists online.",
            "- Contact the municipal clerk's office for the most up-to-date information.",
            f"- Data collected from {total} Ontario municipalities.",
            "",
            "## Municipalities with Candidates Found",
            "",
        ]

        for r in self.results:
            if r.get("candidates"):
                lines.append(f"- **{r['name']}** ({r['status']}) — {len(r['candidates'])} candidate(s)")
                for c in r["candidates"]:
                    lines.append(f"  - {c['name']} — {c['position']}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info(f"Report exported: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Ontario Municipal Election Candidate Scraper",
        epilog="Example: python ontario_election_scraper.py --limit 10 --output ./report"
    )
    parser.add_argument("--output", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--delay", "-d", type=float, default=REQUEST_DELAY, help=f"Delay between requests in seconds (default: {REQUEST_DELAY})")
    parser.add_argument("--limit", "-l", type=int, help="Limit number of municipalities to process (for testing)")
    parser.add_argument("--resume", "-r", action="store_true", help="Resume from last run (uses cache)")
    parser.add_argument("--clear-cache", "-c", action="store_true", help="Clear cached municipality list")
    parser.add_argument("--list-only", action="store_true", help="Only fetch and save the municipality list, don't scrape")
    args = parser.parse_args()

    if args.clear_cache:
        cache_dir = ".cache"
        if os.path.exists(cache_dir):
            import shutil
            shutil.rmtree(cache_dir)
            logger.info("Cache cleared")
        return

    scraper = OntarioMunicipalityScraper(
        output_dir=args.output,
        delay=args.delay,
        resume=args.resume
    )

    if args.list_only:
        munis = scraper.fetch_municipality_list()
        path = os.path.join(args.output, "municipality_list.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "status", "type", "division", "population"])
            writer.writeheader()
            clean = [{k: m[k] for k in ["name", "status", "type", "division", "population"]} for m in munis]
            writer.writerows(clean)
        logger.info(f"Municipality list saved to {path} ({len(munis)} entries)")
        return

    scraper.run(limit=args.limit)


if __name__ == "__main__":
    main()
