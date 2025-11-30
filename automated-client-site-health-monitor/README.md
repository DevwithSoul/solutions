# Automated Client Site Health Monitor

A lightweight, production-ready Python tool designed for freelance developers and agencies. It automatically scans a client's website for common health issues (broken links, missing images, mixed content) and sends a consolidated report via Slack or Email.

## Problem Description

Manually clicking through client websites to check for broken assets or SSL warnings is time-consuming and prone to human error. This tool automates that process, allowing you to schedule regular health checks for multiple clients and receive alerts only when something is wrong.

## Solution Overview

This script performs a single-page audit (ideal for Homepages or Landing Pages) checking for:
1.  **Broken Links**: Scans all `<a>` tags and verifies the destination returns a 200 OK status.
2.  **Broken Images**: Scans all `<img>` tags to ensure images load correctly.
3.  **Mixed Content**: Detects if an HTTPS site is loading HTTP resources (scripts, images, css).
4.  **Reporting**: Sends a summary of errors to a Slack channel (via Webhook) or an Email address.

## Prerequisites

-   **Python 3.7+** installed on your machine.
-   **pip** (Python package manager).

## Installation

1.  Download the `site_health_monitor.py` file.
2.  Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the script from the command line. The only required argument is the URL to scan.

### Basic Scan (Console Output Only)
```bash
python site_health_monitor.py https://example.com
```

### Scan with Slack Notifications
To get a Slack Webhook URL, go to [Slack API](https://api.slack.com/messaging/webhooks) -> Create New App -> Activate Incoming Webhooks.

```bash
python site_health_monitor.py https://example.com --slack "https://hooks.slack.com/services/T000/B000/XXX"
```

### Scan with Email Notifications (Gmail Example)
*Note: For Gmail, you may need to use an [App Password](https://support.google.com/accounts/answer/185833?hl=en).*

```bash
python site_health_monitor.py https://example.com \
  --email-server smtp.gmail.com \
  --email-port 587 \
  --email-user yourdev@gmail.com \
  --email-pass "your-app-password" \
  --email-to client@example.com
```

## Configuration & Automation

To run this automatically (e.g., every morning), use **cron** (Linux/Mac) or **Task Scheduler** (Windows).

**Example Cron Job (Run daily at 8 AM):**
```bash
0 8 * * * /usr/bin/python3 /path/to/site_health_monitor.py https://client-site.com --slack "https://hooks.slack.com/..."
```

## Recommendations

1.  **Rate Limiting**: The script scans sequentially to be polite. Do not run this in parallel loops against the same server to avoid being blocked.
2.  **False Positives**: Some websites block automated requests (403 Forbidden). The script includes a standard User-Agent header to mitigate this, but strict firewalls may still block it.
3.  **Timeout**: If a site is slow, increase the timeout using `--timeout 30`.