#!/usr/bin/env python3
"""
Job Scraper - Undetected ChromeDriver Version
Uses undetected-chromedriver to bypass Google's bot detection
"""

import time
import csv
import json
import os
from datetime import datetime
from urllib.parse import urlparse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import requests

OUTPUT_FILE = "ai_ml_jobs_undetected.csv"
SEEN_JOBS_FILE = "seen_jobs_undetected.json"
DELAY_BETWEEN_SEARCHES = 5  # Longer delay to be safe

SEARCH_QUERIES = [
    '("AI Engineer" OR "Machine Learning Engineer") ("New York" OR "NYC") site:ashbyhq.com -senior',
    '("AI Engineer") ("New York" OR "NYC") site:greenhouse.io -senior',
    '("LLM Engineer") ("New York" OR "NYC") site:ashbyhq.com -senior',
    '("AI Engineer" OR "Machine Learning Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com -senior',
    '("LLM Engineer") ("San Francisco") site:ashbyhq.com -senior',
    '("AI Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com -senior',
    '("ML Engineer") ("Boston" OR "Cambridge") site:greenhouse.io -senior',
    '("AI Engineer") ("remote" OR "hybrid") ("US only") site:ashbyhq.com -senior -canada',
    '("Machine Learning Engineer") ("remote US") site:ashbyhq.com -senior',
    '("LLM Engineer") ("remote United States") site:ashbyhq.com -senior',
    'site:openai.com/careers "engineer" -senior',
    'site:anthropic.com/careers "engineer" -senior',
    'site:scale.ai/careers "machine learning" -senior',
]


def setup_driver():
    """Setup undetected Chrome"""
    options = uc.ChromeOptions()

    # Run headless
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Create driver
    driver = uc.Chrome(options=options, version_main=None)
    return driver


def search_google(driver, query):
    """Search Google and extract URLs"""
    search_url = f"https://www.google.com/search?q={query}&tbs=qdr:d"

    try:
        print(f"   Navigating to Google...")
        driver.get(search_url)

        # Wait for page load
        time.sleep(3)

        # Check if we got CAPTCHA
        if 'sorry' in driver.current_url or 'captcha' in driver.page_source.lower():
            print(f"   WARNING: CAPTCHA detected")
            return []

        # Try multiple selectors
        urls = []

        # Try standard selector
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "div.yuRUbf a")
            for elem in elements:
                href = elem.get_attribute('href')
                if href and 'google.com' not in href and href.startswith('http'):
                    urls.append(href)
        except:
            pass

        # Fallback: try all links in search results
        if not urls:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, "#search a")
                for elem in elements:
                    href = elem.get_attribute('href')
                    if href and 'google.com' not in href and href.startswith('http'):
                        if any(domain in href for domain in
                               ['ashbyhq', 'greenhouse', 'lever', 'workday', 'openai', 'anthropic', 'scale']):
                            urls.append(href)
            except:
                pass

        return urls[:10]

    except Exception as e:
        print(f"   Error: {str(e)[:100]}")
        return []


def extract_job_details(url):
    """Extract job details from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title = None
        for tag in ['h1', 'h2', 'h3']:
            elem = soup.find(tag)
            if elem and len(elem.get_text(strip=True)) > 10:
                title = elem.get_text(strip=True)
                break

        # Extract company
        company = extract_company_from_url(url)

        # Extract location
        location = "Not specified"
        text = soup.get_text().lower()
        if 'remote' in text:
            location = "Remote"
        elif 'new york' in text or 'nyc' in text:
            location = "NYC"
        elif 'san francisco' in text or 'bay area' in text:
            location = "SF"
        elif 'boston' in text:
            location = "Boston"

        return {
            'title': title or 'No Title',
            'company': company,
            'location': location,
            'url': url,
            'ats': detect_ats(url),
            'date_found': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'status': 'Not Applied'
        }

    except Exception as e:
        return None


def extract_company_from_url(url):
    """Extract company name"""
    if 'ashbyhq.com' in url:
        parts = url.split('/')
        for i, part in enumerate(parts):
            if 'jobs.ashbyhq.com' in url and i + 1 < len(parts):
                return parts[i + 1].replace('-', ' ').title()

    if 'greenhouse.io' in url:
        parts = url.split('/')
        if 'boards' in parts:
            idx = parts.index('boards')
            if idx + 1 < len(parts):
                return parts[idx + 1].replace('-', ' ').title()

    companies = {
        'openai': 'OpenAI',
        'anthropic': 'Anthropic',
        'scale': 'Scale AI',
        'cohere': 'Cohere',
    }

    for key, name in companies.items():
        if key in url.lower():
            return name

    domain = urlparse(url).netloc
    return domain.replace('www.', '').split('.')[0].title()


def detect_ats(url):
    """Detect ATS"""
    if 'ashbyhq' in url:
        return 'Ashby'
    elif 'greenhouse' in url:
        return 'Greenhouse'
    elif 'lever' in url:
        return 'Lever'
    elif 'workday' in url:
        return 'Workday'
    return 'Direct'


def normalize_url(url):
    """Normalize URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/').lower()


def load_seen_jobs():
    """Load seen jobs"""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(seen_jobs):
    """Save seen jobs"""
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(list(seen_jobs), f)


def save_to_csv(jobs, filename):
    """Save to CSV"""
    if not jobs:
        return

    file_exists = os.path.exists(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['title', 'company', 'location', 'ats', 'url', 'date_found', 'status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for job in jobs:
            writer.writerow(job)


def main():
    """Main execution"""
    print("=" * 60)
    print("JOB SCRAPER - UNDETECTED CHROMEDRIVER")
    print("Time:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("Total Searches:", len(SEARCH_QUERIES))
    print("=" * 60)

    print("\nInitializing undetected Chrome...")
    driver = setup_driver()
    print("Chrome ready!\n")

    seen_jobs = load_seen_jobs()
    all_new_jobs = []

    try:
        for idx, query in enumerate(SEARCH_QUERIES, 1):
            print(f"[{idx}/{len(SEARCH_QUERIES)}] {query[:60]}...")

            urls = search_google(driver, query)

            if urls:
                print(f"   Found {len(urls)} URLs")

                for url in urls:
                    normalized = normalize_url(url)

                    if normalized in seen_jobs:
                        continue

                    job_data = extract_job_details(url)

                    if job_data:
                        all_new_jobs.append(job_data)
                        seen_jobs.add(normalized)
                        print(f"   NEW: {job_data['company']} - {job_data['title'][:40]}")
            else:
                print(f"   No URLs found (possible CAPTCHA)")

            # Longer delay between searches
            if idx < len(SEARCH_QUERIES):
                time.sleep(DELAY_BETWEEN_SEARCHES)

    finally:
        driver.quit()
        print("\nChrome closed.")

    # Save results
    if all_new_jobs:
        save_to_csv(all_new_jobs, OUTPUT_FILE)
        save_seen_jobs(seen_jobs)

        print("\n" + "=" * 60)
        print(f"SUCCESS! Found {len(all_new_jobs)} NEW jobs")
        print(f"Total tracked: {len(seen_jobs)}")
        print(f"Saved to: {OUTPUT_FILE}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("No new jobs found")
        print(f"Total tracked: {len(seen_jobs)}")
        print("=" * 60)


if __name__ == "__main__":
    main()