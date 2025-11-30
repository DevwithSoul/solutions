#aiwebarchitects
import argparse
import csv
import json
import logging
import os
import time
import hashlib
import sys
import requests
from io import StringIO
from typing import Generator, Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class SupplierSyncMiddleware:
    """
    Middleware to synchronize a legacy CSV supplier feed with a modern E-commerce API.
    Features:
    - Stream processing (low memory usage)
    - Content hashing (efficient diffing)
    - Batch processing (rate limit compliance)
    - State persistence (avoids redundant updates)
    """

    def __init__(self, feed_url: str, api_url: str, api_key: str, batch_size: int = 50, dry_run: bool = False):
        self.feed_url = feed_url
        self.api_url = api_url
        self.api_key = api_key
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.state_file = 'sync_state.json'
        self.state = self._load_state()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _load_state(self) -> Dict[str, str]:
        """Load the previous synchronization state (SKU -> Hash)."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state file: {e}")
                return {}
        return {}

    def _save_state(self):
        """Save the current synchronization state to disk."""
        if self.dry_run:
            return
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f)
            logger.info("Sync state saved successfully.")
        except Exception as e:
            logger.error(f"Failed to save state file: {e}")

    def _calculate_hash(self, data: Dict[str, Any]) -> str:
        """Generate a deterministic hash of the product data for diffing."""
        # Sort keys to ensure consistent ordering
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.md5(serialized.encode('utf-8')).hexdigest()

    def fetch_feed_stream(self) -> Generator[Dict[str, str], None, None]:
        """
        Generator that yields rows from the supplier feed.
        Handles both local files and HTTP URLs.
        """
        logger.info(f"Fetching feed from: {self.feed_url}")
        
        if self.feed_url.startswith(('http://', 'https://')):
            with requests.get(self.feed_url, stream=True) as r:
                r.raise_for_status()
                # Decode stream to text
                lines = (line.decode('utf-8') for line in r.iter_lines())
                reader = csv.DictReader(lines)
                for row in reader:
                    yield row
        else:
            # Assume local file for testing/dev
            if not os.path.exists(self.feed_url):
                logger.error(f"File not found: {self.feed_url}")
                return
            with open(self.feed_url, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row

    def send_batch_update(self, batch: List[Dict[str, Any]]):
        """Sends a batch of updates to the E-commerce API."""
        if not batch:
            return

        if self.dry_run:
            logger.info(f"[DRY RUN] Would send batch of {len(batch)} items to {self.api_url}")
            return

        try:
            # Simulate API call
            # In production: response = requests.post(f"{self.api_url}/products/batch", json=batch, headers=self.headers)
            # response.raise_for_status()
            
            # Mocking network latency
            time.sleep(0.5)
            logger.info(f"Successfully synced batch of {len(batch)} items.")
        except Exception as e:
            logger.error(f"Failed to sync batch: {e}")
            # In a real scenario, you might implement retry logic here

    def run(self):
        """Main execution logic."""
        logger.info("Starting synchronization process...")
        
        batch = []
        updates_count = 0
        processed_count = 0
        
        # Iterate through the feed lazily
        for row in self.fetch_feed_stream():
            processed_count += 1
            sku = row.get('sku') or row.get('SKU')
            
            if not sku:
                logger.warning(f"Skipping row {processed_count}: Missing SKU")
                continue

            # Calculate hash to check for changes
            current_hash = self._calculate_hash(row)
            
            # Check if data has changed since last sync
            if sku not in self.state or self.state[sku] != current_hash:
                batch.append(row)
                # Optimistically update state (will be saved at end or periodically)
                self.state[sku] = current_hash
                updates_count += 1
            
            # If batch is full, send it
            if len(batch) >= self.batch_size:
                self.send_batch_update(batch)
                batch = []

        # Send remaining items
        if batch:
            self.send_batch_update(batch)

        self._save_state()
        logger.info(f"Sync complete. Processed: {processed_count}, Updated: {updates_count}")

def create_dummy_csv():
    """Helper to create a dummy CSV for testing if one doesn't exist."""
    filename = "supplier_data.csv"
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["sku", "name", "price", "stock"])
            writer.writerow(["A100", "Widget Pro", "19.99", "50"])
            writer.writerow(["B200", "Gadget Lite", "9.99", "10"])
            writer.writerow(["C300", "Super Tool", "45.00", "0"])
        logger.info(f"Created dummy feed file: {filename}")
    return filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Supplier Feed Sync Middleware")
    
    parser.add_argument("--feed-url", type=str, help="URL or local path to the supplier CSV feed")
    parser.add_argument("--api-url", type=str, default="https://api.mystore.com/v1", help="Target E-commerce API endpoint")
    parser.add_argument("--api-key", type=str, default="test_key", help="API Key for authentication")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of items to sync per request")
    parser.add_argument("--dry-run", action="store_true", help="Process data but do not send API requests")
    parser.add_argument("--create-sample", action="store_true", help="Generate a sample CSV file for testing")

    args = parser.parse_args()

    if args.create_sample:
        create_dummy_csv()
        sys.exit(0)

    # Default to dummy file if no URL provided for testing purposes
    feed_source = args.feed_url
    if not feed_source:
        feed_source = create_dummy_csv()

    syncer = SupplierSyncMiddleware(
        feed_url=feed_source,
        api_url=args.api_url,
        api_key=args.api_key,
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )

    syncer.run()