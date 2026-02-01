#!/usr/bin/env python3
"""
AI/ML Job Scraper - US ONLY + COMPREHENSIVE
All improvements:
- US location filter in all queries
- Correct ATS subdomains
- Global deduplication
- Better senior filtering
- 24-hour time filter
"""

import time
import csv
import re
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

load_dotenv(Path(__file__).with_name(".env"), override=True)

# Configuration
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'ai_ml_jobs_output')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 20))  # 20 seconds to avoid CAPTCHA
MAX_RESULTS_PER_QUERY = int(os.getenv('MAX_RESULTS_PER_QUERY', 20))
HOURS_LOOKBACK = int(os.getenv('HOURS_LOOKBACK', 24))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Calculate date filter
now = datetime.now()
lookback_date = now - timedelta(hours=HOURS_LOOKBACK)
date_filter = lookback_date.strftime('%Y-%m-%d')

print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Filtering: Last {HOURS_LOOKBACK} hours (after:{date_filter})")
print(f"Location: United States only")

# Senior patterns
SENIOR_PATTERNS = [
    r'\bsenior\b', r'\bsr\.?\b', r'\bstaff\b', r'\bprincipal\b',
    r'\bdirector\b', r'\bhead of\b', r'\bchief\b',
    r'\bvp\b', r'\bvice president\b',
    r'\b(engineering manager|manager.*engineer)\b'
]

ENTRY_HINTS = ["associate", "entry level", "junior", "early career"]

# ATS allowlist
ATS_ALLOW = [
    "jobs.ashbyhq.com", "ashbyhq.com",
    "boards.greenhouse.io", "greenhouse.io",
    "jobs.lever.co", "lever.co",
    "myworkdayjobs.com",
    "apply.workable.com", "workable.com",
    "jobs.smartrecruiters.com", "smartrecruiters.com",
    "jobs.jobvite.com", "jobvite.com",
    "pinpointhq.com",
    "bamboohr.com"
]

# SEARCHES - US LOCATION FILTER ADDED TO ALL QUERIES
SEARCHES_BY_CATEGORY = {

    # LLM / GENERATIVE AI ENGINEER
    'llm_genai_engineer': [
        {
            "query": '("LLM Engineer" OR "Generative AI Engineer") ("United States" OR "USA" OR "US") site:jobs.ashbyhq.com',
            "ats": "Ashby"},
        {"query": '("LLM Engineer" OR "GenAI Engineer") ("United States" OR "USA") site:boards.greenhouse.io',
         "ats": "Greenhouse"},
        {"query": '"Foundation Model Engineer" ("United States" OR "USA") site:jobs.ashbyhq.com', "ats": "Ashby"},
        {"query": '("LLM" OR "Generative AI") "engineer" ("United States" OR "USA") site:jobs.lever.co',
         "ats": "Lever"},
        {"query": '"LLM Engineer" ("United States" OR "USA") site:apply.workable.com', "ats": "Workable"},
    ],

    # AI ENGINEER (GENERAL)
    'ai_engineer': [
        {
            "query": '("AI Engineer" OR "Artificial Intelligence Engineer") ("United States" OR "USA") site:jobs.ashbyhq.com',
            "ats": "Ashby"},
        {"query": '("AI Engineer" OR "Applied AI Engineer") ("United States" OR "USA") site:boards.greenhouse.io',
         "ats": "Greenhouse"},
        {"query": '"AI Engineer" ("United States" OR "USA") site:jobs.lever.co', "ats": "Lever"},
        {"query": '"AI Engineer" ("United States" OR "USA") site:myworkdayjobs.com', "ats": "Workday"},
        {"query": '("AI Engineer" OR "Applied AI") ("United States" OR "USA") site:apply.workable.com',
         "ats": "Workable"},
    ],

    # MACHINE LEARNING ENGINEER
    'ml_engineer': [
        {"query": '("Machine Learning Engineer" OR "ML Engineer") ("United States" OR "USA") site:jobs.ashbyhq.com',
         "ats": "Ashby"},
        {
            "query": '("Machine Learning Engineer" OR "Applied ML Engineer") ("United States" OR "USA") site:boards.greenhouse.io',
            "ats": "Greenhouse"},
        {"query": '"ML Engineer" ("United States" OR "USA") site:jobs.lever.co', "ats": "Lever"},
        {"query": '"Machine Learning Engineer" ("United States" OR "USA") site:myworkdayjobs.com', "ats": "Workday"},
        {"query": '("ML Engineer" OR "Machine Learning") ("United States" OR "USA") site:jobs.smartrecruiters.com',
         "ats": "SmartRecruiters"},
    ],

    # RESEARCH SCIENTIST / APPLIED SCIENTIST
    'research_scientist': [
        {"query": '("Machine Learning Scientist" OR "ML Scientist") ("United States" OR "USA") site:jobs.ashbyhq.com',
         "ats": "Ashby"},
        {"query": '("Applied Scientist") ("United States" OR "USA") site:myworkdayjobs.com', "ats": "Workday"},
        {
            "query": '("Research Scientist" OR "AI Research Scientist") ("United States" OR "USA") site:boards.greenhouse.io',
            "ats": "Greenhouse"},
        {"query": '"Research Engineer" (AI OR ML) ("United States" OR "USA") site:jobs.lever.co', "ats": "Lever"},
    ],

    # NLP ENGINEER
    'nlp_engineer': [
        {"query": '"NLP Engineer" ("United States" OR "USA") site:jobs.ashbyhq.com', "ats": "Ashby"},
        {
            "query": '("NLP Engineer" OR "Natural Language Processing") ("United States" OR "USA") site:boards.greenhouse.io',
            "ats": "Greenhouse"},
        {"query": '"NLP" "engineer" ("United States" OR "USA") site:jobs.lever.co', "ats": "Lever"},
    ],

    # COMPUTER VISION ENGINEER
    'computer_vision': [
        {"query": '("Computer Vision Engineer" OR "CV Engineer") ("United States" OR "USA") site:jobs.ashbyhq.com',
         "ats": "Ashby"},
        {"query": '"Computer Vision" "engineer" ("United States" OR "USA") site:boards.greenhouse.io',
         "ats": "Greenhouse"},
        {"query": '("Computer Vision" OR "Multimodal") "engineer" ("United States" OR "USA") site:jobs.lever.co',
         "ats": "Lever"},
    ],

    # MLOPS / ML INFRASTRUCTURE
    'mlops_infrastructure': [
        {"query": '("MLOps Engineer" OR "ML Infrastructure Engineer") ("United States" OR "USA") site:jobs.ashbyhq.com',
         "ats": "Ashby"},
        {"query": '"MLOps Engineer" ("United States" OR "USA") site:boards.greenhouse.io', "ats": "Greenhouse"},
        {"query": '("ML Platform Engineer" OR "AI Infrastructure") ("United States" OR "USA") site:jobs.lever.co',
         "ats": "Lever"},
    ],

    # DEEP LEARNING ENGINEER
    'deep_learning': [
        {"query": '"Deep Learning Engineer" ("United States" OR "USA") site:jobs.ashbyhq.com', "ats": "Ashby"},
        {
            "query": '("Deep Learning" OR "Neural Networks") "engineer" ("United States" OR "USA") site:boards.greenhouse.io',
            "ats": "Greenhouse"},
    ],
}


def setup_brave_driver():
    """
    Setup Brave browser with anti-detection measures
    - Incognito mode (no cookies/tracking)
    - Disable automation flags
    - Random user agent
    """
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    if not os.path.exists(brave_path):
        print("ERROR: Brave not found at:", brave_path)
        exit(1)

    options = Options()
    options.binary_location = brave_path

    # CRITICAL: Incognito mode
    options.add_argument('--incognito')

    # Anti-detection flags
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Additional stealth
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-gpu')

    # Random realistic user agent
    options.add_argument(
        'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(options=options)

        # Hide webdriver property
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

        return driver
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


def normalize_url(url):
    """Remove # anchors AND tracking parameters"""
    if not url:
        return None

    # Remove fragment
    if '#' in url:
        url = url.split('#')[0]

    # Parse URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Remove tracking params
    tracking_params = ['gh_src', 'gh_jid', 'source', 'utm_source', 'utm_medium',
                       'utm_campaign', 'ref', 'gclid', 'lever-source']

    cleaned_params = {k: v for k, v in query_params.items() if k not in tracking_params}

    # Rebuild query
    new_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''

    # Rebuild URL
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        '', new_query, ''
    ))

    return normalized.rstrip('/')


def extract_company(url):
    """Extract company from URL"""
    if 'jobs.ashbyhq.com' in url:
        match = re.search(r'jobs\.ashbyhq\.com/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'ashbyhq.com' in url:
        match = re.search(r'//([^.]+)\.ashbyhq\.com', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'boards.greenhouse.io' in url:
        match = re.search(r'boards\.greenhouse\.io/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'greenhouse.io' in url:
        match = re.search(r'//([^.]+)\.greenhouse\.io', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'jobs.lever.co' in url:
        match = re.search(r'jobs\.lever\.co/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'lever.co' in url:
        match = re.search(r'//([^.]+)\.lever\.co', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'myworkdayjobs.com' in url:
        match = re.search(r'//([^.]+)\.wd\d+\.myworkdayjobs', url)
        if match:
            return match.group(1).title()

    if 'apply.workable.com' in url:
        match = re.search(r'apply\.workable\.com/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'jobs.smartrecruiters.com' in url:
        match = re.search(r'jobs\.smartrecruiters\.com/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    return "Unknown"


def is_senior_role(title):
    """Check if senior role"""
    title_lower = title.lower()

    if any(hint in title_lower for hint in ENTRY_HINTS):
        return False

    # Level III, IV are senior
    if re.search(r'\b(iii|iv|v)\b', title_lower):
        return True

    return any(re.search(pattern, title_lower) for pattern in SENIOR_PATTERNS)


def google_search(driver, query, date_filter, seen_urls_global, max_results=20):
    """Search Google with after:DATE filter + GLOBAL deduplication"""
    jobs = []

    try:
        driver.get("https://www.google.com")
        time.sleep(2)

        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()

        query_with_filter = f"{query} after:{date_filter}"
        search_box.send_keys(query_with_filter)
        search_box.send_keys(Keys.RETURN)

        print(f"    Query: {query_with_filter}")
        time.sleep(6)  # Increased wait for results to load

        page = 0

        while len(jobs) < max_results and page < 3:
            # Primary selector
            results = driver.find_elements(By.CSS_SELECTOR, 'div.tF2Cxc')

            # Fallback
            if not results:
                results = driver.find_elements(By.CSS_SELECTOR, 'div.g')

            print(f"    Page {page + 1}: {len(results)} results")

            if not results:
                break

            for result in results:
                if len(jobs) >= max_results:
                    break

                try:
                    h3 = result.find_element(By.CSS_SELECTOR, 'h3')
                    title = h3.text.strip()

                    link = result.find_element(By.CSS_SELECTOR, 'a')
                    url = link.get_attribute('href')

                    if not title or not url or len(title) < 5:
                        continue

                    if not url.startswith('http'):
                        continue

                    # Must be from ATS allowlist
                    if not any(ats in url for ats in ATS_ALLOW):
                        continue

                    # Normalize URL
                    normalized = normalize_url(url)

                    # Global deduplication
                    if normalized in seen_urls_global:
                        continue
                    seen_urls_global.add(normalized)

                    # Filter senior
                    if is_senior_role(title):
                        continue

                    company = extract_company(url)

                    print(f"    ✓ {company} - {title[:55]}")

                    jobs.append({
                        'title': title,
                        'company': company,
                        'url': url
                    })

                except Exception as e:
                    continue

            # Next page
            if len(jobs) < max_results and page < 2:
                try:
                    next_btn = driver.find_element(By.ID, "pnnext")
                    next_btn.click()
                    time.sleep(4)
                    page += 1
                except:
                    break
            else:
                break

        return jobs

    except Exception as e:
        print(f"    Error: {str(e)[:80]}")
        return []


def save_category_csv(jobs, category_name):
    """Save to CSV"""
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
    print("AI/ML JOB SCRAPER - US ONLY - LAST 24 HOURS")
    print(f"Started: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categories: {len(SEARCHES_BY_CATEGORY)}")
    print(f"Total searches: {sum(len(s) for s in SEARCHES_BY_CATEGORY.values())}")
    print(f"Output: {OUTPUT_DIR}/")
    print("=" * 70)

    driver = setup_brave_driver()
    print("Browser ready!\n")

    # Global deduplication
    seen_urls_global = set()

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
                    date_filter,
                    seen_urls_global,
                    MAX_RESULTS_PER_QUERY
                )

                if jobs:
                    for job in jobs:
                        job['ats'] = search_config['ats']
                        job['date_found'] = datetime.now().strftime('%Y-%m-%d %H:%M')

                    print(f"   Found: {len(jobs)} new jobs")
                    category_jobs.extend(jobs)
                else:
                    print(f"   No new jobs")

                if idx < len(searches):
                    # Random delay between 18-22 seconds (more human-like)
                    delay = random.randint(18, 22)
                    print(f"   Waiting {delay}s (anti-CAPTCHA delay)...")
                    time.sleep(delay)

            if category_jobs:
                filename = save_category_csv(category_jobs, category_name)
                category_results[category_name] = {
                    'count': len(category_jobs),
                    'file': filename
                }
                print(f"\n✓ Saved {len(category_jobs)} jobs → {filename}")

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY - LAST 24 HOURS - US ONLY")
        print("=" * 70)

        total = sum(r['count'] for r in category_results.values())

        print(f"\nTotal unique jobs: {total}")
        print(f"Total URLs checked: {len(seen_urls_global)}")
        print(f"Duplicates removed: {len(seen_urls_global) - total}\n")

        if total > 0:
            for category, result in category_results.items():
                cat_name = category.replace('_', ' ').title()
                print(f"{cat_name}: {result['count']} jobs")
                print(f"  → {result['file']}")
        else:
            print("No jobs found in last 24 hours")
            print("\nTip: Try HOURS_LOOKBACK=24 or 72")

        print("\n" + "=" * 70)

    finally:
        print("\nClosing...")
        driver.quit()
        print("Done!")


if __name__ == "__main__":
    main()