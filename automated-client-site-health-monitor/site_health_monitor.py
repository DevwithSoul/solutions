#aiwebarchitects
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class SiteHealthMonitor:
    def __init__(self, target_url, slack_webhook=None, email_config=None, timeout=10):
        """
        Initialize the monitor.
        :param target_url: The URL to scan.
        :param slack_webhook: Optional Slack Webhook URL for reporting.
        :param email_config: Optional dictionary containing SMTP settings.
        :param timeout: Request timeout in seconds.
        """
        self.target_url = target_url
        self.slack_webhook = slack_webhook
        self.email_config = email_config
        self.timeout = timeout
        self.errors = []
        self.checked_links = set()
        
        # Headers to mimic a real browser to avoid 403 Forbidden on some sites
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def is_mixed_content(self, resource_url):
        """Check if a resource is HTTP when the main site is HTTPS."""
        if self.target_url.startswith('https://') and resource_url.startswith('http://'):
            return True
        return False

    def check_resource(self, url, resource_type="Link"):
        """
        Checks if a resource URL is reachable.
        Returns (status_code, error_message or None)
        """
        if url in self.checked_links:
            return 200, None  # Assume valid if already checked to save time
        
        self.checked_links.add(url)
        
        try:
            # Use HEAD request first to save bandwidth
            response = requests.head(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            
            # Some servers don't support HEAD, retry with GET
            if response.status_code == 405:
                response = requests.get(url, headers=self.headers, timeout=self.timeout, stream=True)
                response.close()
            
            if response.status_code >= 400:
                return response.status_code, f"Broken {resource_type} ({response.status_code})"
            
            return response.status_code, None
            
        except requests.exceptions.RequestException as e:
            return 0, f"Connection Error on {resource_type}: {str(e)}"

    def scan(self):
        """Orchestrates the scanning process."""
        logger.info(f"Starting scan for: {self.target_url}")
        
        try:
            response = requests.get(self.target_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"CRITICAL: Could not access target URL. {e}")
            self.errors.append(f"CRITICAL: Could not access site root. {e}")
            self.send_reports()
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Check Links (Anchors)
        links = soup.find_all('a', href=True)
        logger.info(f"Found {len(links)} links to check...")
        
        for link in links:
            href = link['href']
            full_url = urljoin(self.target_url, href)
            
            # Skip mailto, tel, javascript, or anchors
            if any(full_url.startswith(p) for p in ['mailto:', 'tel:', 'javascript:', '#']):
                continue
            
            # Check Mixed Content
            if self.is_mixed_content(full_url):
                self.errors.append(f"Mixed Content Warning (Link): {full_url}")

            # Check Validity (Only check internal links or allow external? 
            # For this tool, we check everything but catch exceptions gracefully)
            status, error = self.check_resource(full_url, "Link")
            if error:
                self.errors.append(f"{error} -> {full_url}")

        # 2. Check Images
        images = soup.find_all('img', src=True)
        logger.info(f"Found {len(images)} images to check...")
        
        for img in images:
            src = img['src']
            full_url = urljoin(self.target_url, src)
            
            if self.is_mixed_content(full_url):
                self.errors.append(f"Mixed Content Warning (Image): {full_url}")

            status, error = self.check_resource(full_url, "Image")
            if error:
                self.errors.append(f"{error} -> {full_url}")

        # 3. Check Scripts/CSS (Basic Mixed Content Check)
        for tag, attr in [('script', 'src'), ('link', 'href')]:
            elements = soup.find_all(tag, **{attr: True})
            for el in elements:
                res_url = urljoin(self.target_url, el[attr])
                if self.is_mixed_content(res_url):
                    self.errors.append(f"Mixed Content Warning ({tag}): {res_url}")

        logger.info("Scan complete.")
        self.send_reports()

    def send_reports(self):
        """Dispatches errors to configured channels."""
        if not self.errors:
            logger.info("No errors found! Site is healthy.")
            msg = f"✅ Health Check Passed for {self.target_url}"
            # Optionally send a 'success' ping if needed, but usually we only alert on error.
            # Uncomment below to force success notification
            # self.errors.append(msg) 
            return

        error_report = "\n".join(self.errors)
        summary = f"⚠️ Health Check Failed for {self.target_url}\nFound {len(self.errors)} issues:\n\n{error_report}"

        # Console Output
        print("\n" + "="*50)
        print(summary)
        print("="*50 + "\n")

        # Slack Notification
        if self.slack_webhook:
            self._send_slack(summary)

        # Email Notification
        if self.email_config:
            self._send_email(summary)

    def _send_slack(self, message):
        try:
            payload = {"text": message}
            requests.post(self.slack_webhook, json=payload)
            logger.info("Slack notification sent.")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def _send_email(self, message):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender']
            msg['To'] = self.email_config['recipient']
            msg['Subject'] = f"Site Health Alert: {self.target_url}"
            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender'], self.email_config['password'])
            server.send_message(msg)
            server.quit()
            logger.info("Email notification sent.")
        except Exception as e:
            logger.error(f"Failed to send Email notification: {e}")

def main():
    parser = argparse.ArgumentParser(description="Automated Client Site Health Monitor")
    
    # Required args
    parser.add_argument("url", help="The URL of the client site to scan (e.g., https://example.com)")
    
    # Optional args
    parser.add_argument("--slack", help="Slack Webhook URL for notifications", default=None)
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    
    # Email args (all required if one is provided, handled in logic logic)
    parser.add_argument("--email-server", help="SMTP Server (e.g., smtp.gmail.com)")
    parser.add_argument("--email-port", type=int, default=587, help="SMTP Port (default: 587)")
    parser.add_argument("--email-user", help="SMTP Username/Email")
    parser.add_argument("--email-pass", help="SMTP Password/App Password")
    parser.add_argument("--email-to", help="Recipient Email Address")

    args = parser.parse_args()

    # Construct Email Config if arguments provided
    email_config = None
    if args.email_server and args.email_user and args.email_pass and args.email_to:
        email_config = {
            'smtp_server': args.email_server,
            'smtp_port': args.email_port,
            'sender': args.email_user,
            'password': args.email_pass,
            'recipient': args.email_to
        }
    elif any([args.email_server, args.email_user, args.email_pass, args.email_to]):
        logger.warning("Incomplete email arguments provided. Email reporting disabled.")

    # Run Monitor
    monitor = SiteHealthMonitor(
        target_url=args.url, 
        slack_webhook=args.slack, 
        email_config=email_config,
        timeout=args.timeout
    )
    monitor.scan()

if __name__ == "__main__":
    main()