#!/usr/bin/env python3
"""
GMP QA Job Scraper - 48-Hour Filter via after: Parameter
Simpler and more reliable than Tools dropdown
"""

import time
import csv
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

load_dotenv(Path(__file__).with_name(".env"), override=True)

# Configuration
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'gmp_jobs_output')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 5))
MAX_RESULTS_PER_QUERY = int(os.getenv('MAX_RESULTS_PER_QUERY', 30))
HOURS_LOOKBACK = int(os.getenv('HOURS_LOOKBACK', 48))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Calculate date filter
now = datetime.now()
lookback_date = now - timedelta(hours=HOURS_LOOKBACK)
date_filter = lookback_date.strftime('%Y-%m-%d')  # Format: 2026-01-29

print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Filtering jobs from last {HOURS_LOOKBACK} hours")
print(f"Looking back to: {lookback_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Google filter: after:{date_filter}")

# Senior patterns
SENIOR_PATTERNS = [
    r'\bsenior\b', r'\bsr\.?\b', r'\b(manager|supervisor|lead)\b',
    r'\b(director|head of|chief)\b', r'\bprincipal\b', r'\biii\b', r'\biv\b'
]

ENTRY_HINTS = ["associate", "entry level", "junior", " i ", "level 1"]

# Searches by category
SEARCHES_BY_CATEGORY = {
    'gmp_qa_associate': [
        {"query": 'GMP QA Associate site:myworkdayjobs.com', "ats": "Workday"},
        {"query": 'GMP Quality Assurance Associate site:myworkdayjobs.com', "ats": "Workday"},
        {"query": 'GMP QA Associate site:icims.com', "ats": "iCIMS"},
        {"query": 'GMP QA Associate site:boards.greenhouse.io', "ats": "Greenhouse"},
    ],
    'gmp_specialist': [
        {"query": 'GMP specialist site:myworkdayjobs.com', "ats": "Workday"},
        {"query": 'GMP Quality specialist site:icims.com', "ats": "iCIMS"},
        {"query": 'GMP compliance specialist site:myworkdayjobs.com', "ats": "Workday"},
    ],
    'document_control': [
        {"query": 'GMP document control specialist site:myworkdayjobs.com', "ats": "Workday"},
        {"query": 'document control specialist site:myworkdayjobs.com', "ats": "Workday"},
        {"query": 'document control site:icims.com GMP', "ats": "iCIMS"},
    ],
}


def setup_brave_driver():
    """Setup Brave browser"""
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    if not os.path.exists(brave_path):
        print("ERROR: Brave not found at:", brave_path)
        exit(1)

    options = Options()
    options.binary_location = brave_path
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--start-maximized')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Error: {e}")
        print("Install chromedriver: brew install chromedriver")
        exit(1)


def normalize_url(url):
    """Remove # anchors and tracking params"""
    if not url or '#' not in url:
        return url
    return url.split('#')[0].rstrip('/')


def extract_company(url):
    """Extract company name from URL"""
    if 'myworkdayjobs.com' in url:
        match = re.search(r'//([^.]+)\.wd\d+\.myworkdayjobs', url)
        if match:
            return match.group(1).title()

    if 'icims.com' in url:
        match = re.search(r'//([^.]+)\.icims', url)
        if match:
            company = match.group(1).replace('careers-', '').replace('uscareers-', '')
            return company.title()

    if 'greenhouse.io' in url:
        match = re.search(r'boards\.greenhouse\.io/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    return "Unknown"


def is_senior_role(title):
    """Check if senior role"""
    title_lower = title.lower()
    if any(hint in title_lower for hint in ENTRY_HINTS):
        return False
    return any(re.search(pattern, title_lower) for pattern in SENIOR_PATTERNS)


def google_search(driver, query, date_filter, max_results=30):
    """
    Search Google with after:DATE filter
    date_filter: YYYY-MM-DD format (e.g., "2026-01-29")
    """
    jobs = []
    seen_urls = set()

    try:
        driver.get("https://www.google.com")
        time.sleep(2)

        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()

        # Add after:DATE to filter last 48 hours
        query_with_filter = f"{query} after:{date_filter}"
        search_box.send_keys(query_with_filter)
        search_box.send_keys(Keys.RETURN)

        print(f"    Query: {query_with_filter}")
        time.sleep(4)

        page = 0

        while len(jobs) < max_results and page < 3:
            # Correct selector: div.tF2Cxc (Google's current HTML)
            results = driver.find_elements(By.CSS_SELECTOR, 'div.tF2Cxc')

            print(f"    Page {page + 1}: {len(results)} result containers")

            if not results:
                print("    No more results")
                break

            for result in results:
                if len(jobs) >= max_results:
                    break

                try:
                    # Extract title (h3 tag)
                    h3 = result.find_element(By.CSS_SELECTOR, 'h3')
                    title = h3.text.strip()

                    # Extract URL (parent a tag)
                    link = result.find_element(By.CSS_SELECTOR, 'a')
                    url = link.get_attribute('href')

                    # Validate
                    if not title or not url or len(title) < 5:
                        continue

                    if not url.startswith('http'):
                        continue

                    # Must be from target ATS platforms
                    if not any(ats in url for ats in ['myworkdayjobs.com', 'icims.com',
                                                      'greenhouse.io', 'lever.co']):
                        continue

                    # Deduplicate by base URL (removes #text anchors)
                    normalized = normalize_url(url)
                    if normalized in seen_urls:
                        continue
                    seen_urls.add(normalized)

                    # Filter senior roles
                    if is_senior_role(title):
                        print(f"    SKIP (senior): {title[:55]}")
                        continue

                    # Extract company
                    company = extract_company(url)

                    print(f"    ✓ {company} - {title[:60]}")

                    jobs.append({
                        'title': title,
                        'company': company,
                        'url': url
                    })

                except Exception as e:
                    continue

            # Try next page
            if len(jobs) < max_results and page < 2:
                try:
                    next_btn = driver.find_element(By.ID, "pnnext")
                    next_btn.click()
                    time.sleep(4)
                    page += 1
                    print(f"    → Going to page {page + 1}")
                except:
                    print("    No next page")
                    break
            else:
                break

        return jobs

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def save_category_csv(jobs, category_name):
    """Save jobs to category-specific CSV"""
    if not jobs:
        return None

    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = f"{OUTPUT_DIR}/{category_name}_{timestamp}.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'company', 'url', 'ats', 'date_found'])
        writer.writeheader()

        for job in jobs:
            writer.writerow(job)

    return filename


def main():
    """Main execution"""
    print("=" * 70)
    print("GMP QA JOB SCRAPER - LAST 48 HOURS")
    print(f"Started: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Date range: {lookback_date.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
    print(f"Output: {OUTPUT_DIR}/")
    print("=" * 70)

    driver = setup_brave_driver()
    print("Browser ready!\n")

    category_results = {}

    try:
        for category_name, searches in SEARCHES_BY_CATEGORY.items():
            print(f"\n{'=' * 70}")
            print(f"CATEGORY: {category_name.upper().replace('_', ' ')}")
            print(f"{'=' * 70}")

            category_jobs = []

            for idx, search_config in enumerate(searches, 1):
                print(f"\n[{idx}/{len(searches)}] {search_config['ats']}")

                jobs = google_search(
                    driver,
                    search_config['query'],
                    date_filter,  # Pass calculated date
                    MAX_RESULTS_PER_QUERY
                )

                if jobs:
                    for job in jobs:
                        job['ats'] = search_config['ats']
                        job['date_found'] = datetime.now().strftime('%Y-%m-%d %H:%M')

                    print(f"   Total: {len(jobs)} jobs")
                    category_jobs.extend(jobs)
                else:
                    print(f"   No jobs found")

                if idx < len(searches):
                    print(f"   Waiting {DELAY_BETWEEN_SEARCHES}s...")
                    time.sleep(DELAY_BETWEEN_SEARCHES)

            if category_jobs:
                filename = save_category_csv(category_jobs, category_name)
                category_results[category_name] = {
                    'count': len(category_jobs),
                    'file': filename
                }
                print(f"\n✓ Saved {len(category_jobs)} jobs → {filename}")

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        total = sum(r['count'] for r in category_results.values())

        if total > 0:
            print(f"\nTotal jobs found: {total}\n")

            for category, result in category_results.items():
                cat_name = category.replace('_', ' ').title()
                print(f"{cat_name}: {result['count']} jobs")
                print(f"  → {result['file']}")

            print("\nAll jobs are from the last 48 hours!")
        else:
            print("No jobs found in last 48 hours")
            print(f"\nTip: Try increasing HOURS_LOOKBACK to 72 or 168 in .env")

        print("\n" + "=" * 70)

    finally:
        print("\nClosing browser...")
        driver.quit()
        print("Done!")


if __name__ == "__main__":
    main()