#!/usr/bin/env python3
"""
GMP QA & Document Control Job Scraper - BRAVE BROWSER + GOOGLE SEARCH
Uses Selenium with Brave browser to scrape Google search results

Searches for:
- GMP QA Associate
- GMP Specialist
- GMP Document Control Specialist/Associate
- Quality Assurance Associate (GMP)
- Quality Control Associate (GMP)

Requirements:
- Brave browser installed
- selenium
- chromedriver (brew install chromedriver on Mac)

Install:
pip install selenium python-dotenv
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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

load_dotenv(Path(__file__).with_name(".env"), override=True)

# Configuration
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'gmp_qa_jobs_google.csv')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 5))  # Minimum 5 seconds
MAX_RESULTS_PER_QUERY = int(os.getenv('MAX_RESULTS_PER_QUERY', 20))
HOURS_LOOKBACK = int(os.getenv('HOURS_LOOKBACK', 48))  # Default: last 48 hours

# Calculate date for Google search filter (48 hours ago)
now = datetime.now()
lookback_date = now - timedelta(hours=HOURS_LOOKBACK)
date_filter = lookback_date.strftime('%Y-%m-%d')  # Format: YYYY-MM-DD

print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Looking back {HOURS_LOOKBACK} hours to: {lookback_date.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Google date filter: after:{date_filter}")

# Senior role patterns for GMP/QA roles
SENIOR_PATTERNS = [
    r'\bsenior\b',
    r'\bsr\.?\b',
    r'\b(manager|supervisor|lead)\b',
    r'\b(director|head of|chief)\b',
    r'\bprincipal\b'
]

# Entry-level/associate hints (keep these)
ENTRY_HINTS = ["associate", "entry level", "junior", "I", " i ", "level 1"]

# Search queries - GMP QA and Document Control roles
SEARCHES = [
    # GMP QA Associate - Major pharma ATS
    {"query": 'GMP QA Associate site:myworkdayjobs.com',
     "role": "GMP QA Associate", "ats": "Workday"},

    {"query": 'GMP Quality Assurance Associate site:myworkdayjobs.com',
     "role": "GMP QA Associate", "ats": "Workday"},

    {"query": 'GMP QA Associate site:icims.com',
     "role": "GMP QA Associate", "ats": "iCIMS"},

    # GMP Specialist
    {"query": 'GMP specialist site:myworkdayjobs.com',
     "role": "GMP Specialist", "ats": "Workday"},

    {"query": 'GMP Quality specialist site:icims.com',
     "role": "GMP Specialist", "ats": "iCIMS"},

    {"query": 'GMP compliance specialist site:myworkdayjobs.com',
     "role": "GMP Specialist", "ats": "Workday"},

    # Document Control Specialist
    {"query": 'GMP document control specialist site:myworkdayjobs.com',
     "role": "Document Control Specialist", "ats": "Workday"},

    {"query": 'document control specialist associate site:myworkdayjobs.com',
     "role": "Document Control Associate", "ats": "Workday"},

    {"query": 'GMP document control site:icims.com',
     "role": "Document Control Specialist", "ats": "iCIMS"},

    # General QA roles
    {"query": 'quality assurance associate GMP site:myworkdayjobs.com',
     "role": "QA Associate", "ats": "Workday"},

    {"query": 'quality control associate GMP site:myworkdayjobs.com',
     "role": "QC Associate", "ats": "Workday"},

    # Greenhouse and Lever (biotech companies often use these)
    {"query": 'GMP QA Associate site:boards.greenhouse.io',
     "role": "GMP QA Associate", "ats": "Greenhouse"},

    {"query": 'document control specialist site:boards.greenhouse.io',
     "role": "Document Control Specialist", "ats": "Greenhouse"},

    {"query": 'GMP specialist site:jobs.lever.co',
     "role": "GMP Specialist", "ats": "Lever"},

    {"query": 'QA associate GMP site:jobs.lever.co',
     "role": "QA Associate", "ats": "Lever"},
]


def setup_brave_driver():
    """Setup Selenium with Brave browser"""

    # Brave browser executable paths (common locations)
    brave_paths = [
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",  # macOS
        "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",  # Windows
        "/usr/bin/brave-browser",  # Linux
        "/snap/bin/brave",  # Linux Snap
    ]

    brave_path = None
    for path in brave_paths:
        if os.path.exists(path):
            brave_path = path
            break

    if not brave_path:
        print("ERROR: Brave browser not found!")
        print("Please install Brave from: https://brave.com/")
        print("Or update brave_paths in the script with your Brave location")
        exit(1)

    print(f"Using Brave at: {brave_path}")

    # Setup Chrome options for Brave
    options = Options()
    options.binary_location = brave_path

    # Add options to avoid detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')

    # Disable automation flags
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Optional: Run headless (no browser window)
    # options.add_argument('--headless')

    # User agent
    options.add_argument(
        'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Create driver using regular Chrome driver (works with Brave)
    # Just download latest chromedriver, it works with Brave
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Error with ChromeDriverManager: {e}")
        print("\nTrying alternative method...")
        # Fallback: try system chromedriver
        try:
            driver = webdriver.Chrome(options=options)
        except Exception as e2:
            print(f"Error: {e2}")
            print("\nPlease install chromedriver:")
            print("  Mac: brew install chromedriver")
            print("  Or download from: https://chromedriver.chromium.org/")
            exit(1)

    return driver


def is_senior_role(title):
    """Check if title indicates senior role"""
    title_lower = title.lower()

    # Check for entry-level exceptions first
    if any(hint in title_lower for hint in ENTRY_HINTS):
        return False

    return any(re.search(pattern, title_lower) for pattern in SENIOR_PATTERNS)


def google_search(driver, query, max_results=20, date_filter=None):
    """
    Perform Google search and extract job links
    date_filter: Google date filter like 'after:2026-01-21' for last 48 hours
    """
    jobs = []

    try:
        # Navigate to Google
        driver.get("https://www.google.com")
        time.sleep(2)

        # Find search box and enter query with time filter
        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()

        # Add time filter to query if provided
        if date_filter:
            query_with_time = f"{query} after:{date_filter}"
        else:
            query_with_time = query

        search_box.send_keys(query_with_time)
        search_box.send_keys(Keys.RETURN)

        # Wait for results to load
        print(f"    Searching: {query_with_time}")
        time.sleep(4)

        # Debug: Check if we got results
        page_source = driver.page_source
        if "did not match any documents" in page_source or "No results found" in page_source:
            print("    Google says: No results found")
            return []

        # Extract search results - try multiple selectors
        results_collected = 0
        page = 0

        while results_collected < max_results and page < 3:
            try:
                # Try different Google result selectors
                search_results = []

                # Method 1: Standard div.g selector
                search_results = driver.find_elements(By.CSS_SELECTOR, 'div.g')

                if not search_results:
                    # Method 2: Try alternative selector
                    search_results = driver.find_elements(By.CSS_SELECTOR, 'div[data-sokoban-container]')

                if not search_results:
                    # Method 3: Find all links in search results
                    search_results = driver.find_elements(By.CSS_SELECTOR, 'div#search a')

                print(f"    Found {len(search_results)} result elements on page")

                for result in search_results:
                    if results_collected >= max_results:
                        break

                    try:
                        # Try to extract title and URL
                        title = None
                        url = None
                        snippet = ""

                        # Method 1: Standard extraction
                        try:
                            title_elem = result.find_element(By.CSS_SELECTOR, 'h3')
                            title = title_elem.text
                            link_elem = result.find_element(By.CSS_SELECTOR, 'a')
                            url = link_elem.get_attribute('href')
                        except:
                            pass

                        # Method 2: Direct link extraction
                        if not url:
                            try:
                                url = result.get_attribute('href')
                                # Get parent text as title
                                title = result.text.split('\n')[0] if result.text else None
                            except:
                                pass

                        # Try to get snippet
                        try:
                            snippet_elem = result.find_element(By.CSS_SELECTOR, 'div.VwiC3b')
                            snippet = snippet_elem.text
                        except:
                            try:
                                snippet_elem = result.find_element(By.CSS_SELECTOR, 'div.kb0PBd, div.yXK7lf')
                                snippet = snippet_elem.text
                            except:
                                pass

                        # Validation
                        if not url or not title:
                            continue

                        if not url.startswith('http'):
                            continue

                        # Skip non-job URLs
                        if 'google.com' in url or 'youtube.com' in url:
                            continue

                        # Must be from target ATS (pharma/biotech platforms)
                        if not any(ats in url for ats in ['myworkdayjobs.com', 'icims.com', 'greenhouse.io',
                                                          'lever.co', 'careers.hcahealthcare.com',
                                                          'taleo.net', 'successfactors.com']):
                            continue

                        # Filter senior roles
                        if is_senior_role(title):
                            print(f"    FILTERED (senior): {title[:60]}")
                            continue

                        print(f"    ✓ Found: {title[:60]}")

                        jobs.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet[:200]
                        })

                        results_collected += 1

                    except Exception as e:
                        continue

                # Try to go to next page
                if results_collected < max_results and page < 2:
                    try:
                        # Find "Next" button
                        next_button = driver.find_element(By.ID, "pnnext")
                        next_button.click()
                        time.sleep(4)
                        page += 1
                        print(f"    Going to page {page + 1}...")
                    except:
                        # No more pages
                        break
                else:
                    break

            except Exception as e:
                print(f"    Error extracting results: {str(e)[:50]}")
                break

        return jobs

    except Exception as e:
        print(f"    Search error: {str(e)[:80]}")
        return []


def save_to_csv(jobs, filename):
    """Save jobs to CSV"""
    if not jobs:
        return

    file_exists = os.path.exists(filename)

    fieldnames = ['title', 'url', 'snippet', 'role_category', 'ats', 'date_found']

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for job in jobs:
            writer.writerow(job)


def main():
    """Main execution"""
    print("=" * 70)
    print(f"GMP QA & DOCUMENT CONTROL JOB SCRAPER - LAST {HOURS_LOOKBACK} HOURS")
    print(f"Started: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Searching jobs posted after: {lookback_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Google filter: after:{date_filter}")
    print(f"Queries: {len(SEARCHES)}")
    print("=" * 70)

    # Setup browser
    print("\nSetting up Brave browser...")
    driver = setup_brave_driver()
    print("Browser ready!")

    all_jobs = []

    try:
        for idx, search_config in enumerate(SEARCHES, 1):
            print(f"\n[{idx}/{len(SEARCHES)}] {search_config['role']} | {search_config['ats']}")
            print(f"Query: {search_config['query']}")

            jobs = google_search(
                driver,
                search_config['query'],
                max_results=MAX_RESULTS_PER_QUERY,
                date_filter=date_filter  # Pass calculated date
            )

            if jobs:
                # Add metadata
                for job in jobs:
                    job['role_category'] = search_config['role']
                    job['ats'] = search_config['ats']
                    job['date_found'] = datetime.now().strftime('%Y-%m-%d %H:%M')

                print(f"   Found {len(jobs)} jobs")
                all_jobs.extend(jobs)
            else:
                print(f"   No jobs found")

            # Delay between searches to avoid detection
            if idx < len(SEARCHES):
                print(f"   Waiting {DELAY_BETWEEN_SEARCHES} seconds...")
                time.sleep(DELAY_BETWEEN_SEARCHES)

        # Save results
        if all_jobs:
            save_to_csv(all_jobs, OUTPUT_FILE)

            print("\n" + "=" * 70)
            print(f"SUCCESS: Found {len(all_jobs)} total jobs")
            print(f"Saved to: {OUTPUT_FILE}")
            print("=" * 70)

            # Print top 10
            print("\nTOP 10 JOBS:")
            for i, job in enumerate(all_jobs[:10], 1):
                print(f"\n{i}. {job['title']}")
                print(f"   {job['url']}")
        else:
            print("\n" + "=" * 70)
            print("No jobs found this run")
            print("=" * 70)

    finally:
        # Close browser
        print("\nClosing browser...")
        driver.quit()
        print("Done!")


if __name__ == "__main__":
    main()