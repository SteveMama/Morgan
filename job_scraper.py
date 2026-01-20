#!/usr/bin/env python3
"""
AI/ML Job Scraper - CORRECTED VERSION
- Filters senior roles AFTER search (Google ignores -senior in queries)
- Rate limit safe with exponential backoff
- US-only positions
"""

import requests
import csv
import time
from datetime import datetime
import json
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'ai_ml_jobs.csv')
SEEN_JOBS_FILE = os.getenv('SEEN_JOBS_FILE', 'seen_jobs.json')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 2))

# SEARCHES (removed -senior filters since Google ignores them anyway)
SEARCHES = [
    # ========================================
    # UNITED STATES - NATIONWIDE (NEW)
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") "United States" site:ashbyhq.com',
        "location": "United States",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("AI Engineer" OR "ML Engineer") "United States" site:greenhouse.io',
        "location": "United States",
        "role": "AI/ML Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("LLM Engineer" OR "Generative AI Engineer") "United States" site:ashbyhq.com',
        "location": "United States",
        "role": "LLM Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("Applied Scientist") "United States" site:myworkdayjobs.com',
        "location": "United States",
        "role": "Applied Scientist",
        "ats": "Workday"
    },
    {
        "query": '("Machine Learning Engineer" OR "ML Engineer") "USA" site:lever.co',
        "location": "United States",
        "role": "ML Engineer",
        "ats": "Lever"
    },

    # ========================================
    # NYC - CITY SPECIFIC
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("New York" OR "NYC") site:ashbyhq.com',
        "location": "NYC, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("AI Engineer" OR "ML Engineer") ("New York" OR "NYC") site:greenhouse.io',
        "location": "NYC, US",
        "role": "AI/ML Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("LLM Engineer") ("New York" OR "NYC") site:ashbyhq.com',
        "location": "NYC, US",
        "role": "LLM Engineer",
        "ats": "Ashby"
    },

    # ========================================
    # SF/BAY AREA - CITY SPECIFIC
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com',
        "location": "SF/Bay Area, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("LLM Engineer") ("San Francisco") site:ashbyhq.com',
        "location": "SF/Bay Area, US",
        "role": "LLM Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("ML Engineer" OR "AI Engineer") ("San Francisco") site:greenhouse.io',
        "location": "SF/Bay Area, US",
        "role": "AI/ML Engineer",
        "ats": "Greenhouse"
    },

    # ========================================
    # BOSTON - CITY SPECIFIC
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com',
        "location": "Boston, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("ML Engineer") ("Boston" OR "Cambridge") site:greenhouse.io',
        "location": "Boston, US",
        "role": "ML Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("LLM Engineer") ("Boston") site:ashbyhq.com',
        "location": "Boston, US",
        "role": "LLM Engineer",
        "ats": "Ashby"
    },

    # ========================================
    # SEATTLE - CITY SPECIFIC
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") "Seattle" site:ashbyhq.com',
        "location": "Seattle, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("ML Engineer") "Seattle" site:greenhouse.io',
        "location": "Seattle, US",
        "role": "ML Engineer",
        "ats": "Greenhouse"
    },

    # ========================================
    # REMOTE - US ONLY
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("remote" OR "hybrid") site:ashbyhq.com -canada -uk',
        "location": "Remote, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("AI Engineer") ("remote US") site:greenhouse.io -canada',
        "location": "Remote, US",
        "role": "AI Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("Machine Learning Engineer") ("remote United States") site:ashbyhq.com -canada',
        "location": "Remote, US",
        "role": "ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("LLM Engineer") ("remote") site:ashbyhq.com -canada',
        "location": "Remote, US",
        "role": "LLM Engineer",
        "ats": "Ashby"
    },

    # ========================================
    # APPLIED SCIENTIST - VARIOUS LOCATIONS
    # ========================================

    {
        "query": '("Applied Scientist") ("New York" OR "San Francisco" OR "Seattle") site:myworkdayjobs.com',
        "location": "Various, US",
        "role": "Applied Scientist",
        "ats": "Workday"
    },
    {
        "query": '("Applied Scientist") ("remote") site:ashbyhq.com -canada',
        "location": "Remote, US",
        "role": "Applied Scientist",
        "ats": "Ashby"
    },
]


def normalize_url(url):
    """Normalize URL for deduplication"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    clean_params = {k: v for k, v in query_params.items()
                    if not k.startswith('utm_') and k not in ['ref', 'source']}
    clean_query = urlencode(clean_params, doseq=True)

    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip('/'),
        '',
        clean_query,
        ''
    ))
    return normalized


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


def search_google_with_retry(query, api_key, search_engine_id, date_restrict='d1', max_retries=3):
    """Execute Google API search with retry"""
    base_url = "https://www.googleapis.com/customsearch/v1"

    for attempt in range(max_retries):
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': query,
            'dateRestrict': date_restrict,
            'num': 10
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)

            if response.status_code == 429:
                wait_time = (2 ** attempt) * 5
                print(f"   Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if '429' in str(e):
                wait_time = (2 ** attempt) * 5
                print(f"   Rate limit. Retry {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
            else:
                print(f"   HTTP Error: {str(e)[:80]}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"   Error: {str(e)[:80]}")
            return None

    print(f"   Failed after {max_retries} retries")
    return None


def extract_company_name(url, title):
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

    if 'lever.co' in url:
        parts = url.split('/')
        if len(parts) > 3:
            return parts[3].replace('-', ' ').title()

    company_map = {
        'openai.com': 'OpenAI',
        'anthropic.com': 'Anthropic',
        'scale.ai': 'Scale AI',
        'cohere.com': 'Cohere',
    }

    for domain, name in company_map.items():
        if domain in url:
            return name

    if ' at ' in title:
        return title.split(' at ')[-1].strip()
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) > 1:
            return parts[-1].strip()

    return "Unknown Company"


def parse_job_results(results, metadata):
    """Parse results and FILTER OUT senior roles here"""
    jobs = []

    if not results or 'items' not in results:
        return jobs

    # Keywords that indicate senior roles (will filter these out)
    exclude_keywords = [
        'senior', 'sr.', 'sr ',
        'staff',
        'principal',
        'lead', 'tech lead', 'team lead',
        'director',
        'head of',
        'vp', 'vice president',
        'chief', 'cto', 'ceo',
        'manager', 'engineering manager'
    ]

    for item in results['items']:
        url = item.get('link', '')
        title = item.get('title', 'No Title')
        normalized_url = normalize_url(url)

        # CRITICAL: Filter here (Google ignores -senior in queries)
        title_lower = title.lower()

        # Check if title contains any exclude keywords
        if any(keyword in title_lower for keyword in exclude_keywords):
            print(f"   FILTERED: {title[:60]}")
            continue  # Skip this job

        job = {
            'title': title,
            'company': extract_company_name(url, title),
            'url': url,
            'normalized_url': normalized_url,
            'snippet': item.get('snippet', ''),
            'location': metadata['location'],
            'role_category': metadata['role'],
            'ats': metadata['ats'],
            'date_found': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'status': 'Not Applied'
        }
        jobs.append(job)

    return jobs


def save_to_csv(jobs, filename):
    """Save to CSV"""
    if not jobs:
        return

    file_exists = os.path.exists(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['title', 'company', 'location', 'role_category', 'ats', 'url', 'date_found', 'status', 'snippet']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for job in jobs:
            row = {k: v for k, v in job.items() if k != 'normalized_url'}
            writer.writerow(row)


def main():
    """Main execution"""
    print("=" * 60)
    print("AI/ML JOB SCRAPER - CORRECTED VERSION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Searches: {len(SEARCHES)}")
    print("Filters: Entry to Mid-level ONLY (post-search filtering)")
    print("=" * 60)

    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        print("ERROR: Missing API keys in .env file")
        return

    seen_jobs = load_seen_jobs()
    all_new_jobs = []
    total_searches = len(SEARCHES)

    for idx, search_config in enumerate(SEARCHES, 1):
        print(
            f"\n[{idx}/{total_searches}] {search_config['role']} in {search_config['location']} ({search_config['ats']})")

        results = search_google_with_retry(
            query=search_config['query'],
            api_key=GOOGLE_API_KEY,
            search_engine_id=SEARCH_ENGINE_ID
        )

        if results:
            jobs = parse_job_results(results, search_config)
            new_jobs = [job for job in jobs if job['normalized_url'] not in seen_jobs]

            if new_jobs:
                print(f"   Found {len(new_jobs)} new entry/mid-level jobs")
                all_new_jobs.extend(new_jobs)
                seen_jobs.update([job['normalized_url'] for job in new_jobs])
            else:
                print(f"   No new jobs")

        if idx < total_searches:
            time.sleep(DELAY_BETWEEN_SEARCHES)

    if all_new_jobs:
        save_to_csv(all_new_jobs, OUTPUT_FILE)
        save_seen_jobs(seen_jobs)

        print("\n" + "=" * 60)
        print(f"SUCCESS! Found {len(all_new_jobs)} NEW entry/mid-level jobs")
        print(f"Total tracked: {len(seen_jobs)}")
        print(f"Saved to: {OUTPUT_FILE}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("No new jobs this run")
        print(f"Total tracked: {len(seen_jobs)}")
        print("=" * 60)


if __name__ == "__main__":
    main()