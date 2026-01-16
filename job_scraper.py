#!/usr/bin/env python3
"""
AI/ML Job Scraper - RATE LIMIT SAFE VERSION
- Smart pagination (only when needed)
- Exponential backoff on 429 errors
- Configurable results per query
- Rate limit handling
"""

import requests
import csv
import time
from datetime import datetime
import json
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'ai_ml_jobs.csv')
SEEN_JOBS_FILE = os.getenv('SEEN_JOBS_FILE', 'seen_jobs.json')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 2))  # Increased to 2 seconds

# Pagination settings (set to False to avoid rate limits)
ENABLE_PAGINATION = False  # Set to True only if you have paid API
RESULTS_PER_QUERY = 10  # 10 if ENABLE_PAGINATION=False, 30 if True

# SEARCHES - Optimized to fit within free tier (100 searches/day)
SEARCHES = [
    # ========================================
    # PRIORITY: NYC + SF + BOSTON + REMOTE
    # ========================================

    # NYC - Core roles
    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("New York" OR "NYC") site:ashbyhq.com -senior -staff -principal',
        "location": "NYC, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby",
        "priority": "high"
    },
    {
        "query": '("AI Engineer" OR "ML Engineer") ("New York" OR "NYC") site:greenhouse.io -senior -staff',
        "location": "NYC, US",
        "role": "AI/ML Engineer",
        "ats": "Greenhouse",
        "priority": "high"
    },
    {
        "query": '("LLM Engineer" OR "Generative AI Engineer") ("New York" OR "NYC") site:ashbyhq.com -senior',
        "location": "NYC, US",
        "role": "LLM Engineer",
        "ats": "Ashby",
        "priority": "high"
    },

    # SF/Bay Area - Core roles
    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com -senior -staff',
        "location": "SF/Bay Area, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby",
        "priority": "high"
    },
    {
        "query": '("LLM Engineer" OR "Generative AI Engineer") ("San Francisco" OR "Palo Alto") site:ashbyhq.com -senior',
        "location": "SF/Bay Area, US",
        "role": "LLM Engineer",
        "ats": "Ashby",
        "priority": "high"
    },
    {
        "query": '("ML Engineer" OR "AI Engineer") ("San Francisco" OR "Mountain View") site:greenhouse.io -senior',
        "location": "SF/Bay Area, US",
        "role": "AI/ML Engineer",
        "ats": "Greenhouse",
        "priority": "high"
    },

    # Boston - Your location
    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com -senior',
        "location": "Boston, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby",
        "priority": "high"
    },
    {
        "query": '("ML Engineer") ("Boston" OR "Cambridge") site:greenhouse.io -senior',
        "location": "Boston, US",
        "role": "ML Engineer",
        "ats": "Greenhouse",
        "priority": "high"
    },
    {
        "query": '("LLM Engineer" OR "NLP Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com -senior',
        "location": "Boston, US",
        "role": "LLM/NLP Engineer",
        "ats": "Ashby",
        "priority": "high"
    },

    # Remote - Critical
    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("remote" OR "hybrid") ("US only" OR "work authorization") site:ashbyhq.com -senior -canada -uk',
        "location": "Remote, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby",
        "priority": "high"
    },
    {
        "query": '("AI Engineer") ("remote US" OR "US remote") site:greenhouse.io -senior -canada',
        "location": "Remote, US",
        "role": "AI Engineer",
        "ats": "Greenhouse",
        "priority": "high"
    },
    {
        "query": '("Machine Learning Engineer") ("remote United States" OR "USA remote") site:ashbyhq.com -senior -canada',
        "location": "Remote, US",
        "role": "ML Engineer",
        "ats": "Ashby",
        "priority": "high"
    },
    {
        "query": '("LLM Engineer") ("remote" OR "work from home") ("US only" OR "authorized to work in the US") site:ashbyhq.com -senior',
        "location": "Remote, US",
        "role": "LLM Engineer",
        "ats": "Ashby",
        "priority": "high"
    },

    # ========================================
    # WIDE NET: Applied Scientist, Research Engineer, etc.
    # ========================================

    {
        "query": '("Applied Scientist") ("New York" OR "San Francisco" OR "Seattle") site:myworkdayjobs.com',
        "location": "Various, US",
        "role": "Applied Scientist",
        "ats": "Workday",
        "priority": "medium"
    },
    {
        "query": '("Applied Scientist") ("remote") ("US only" OR "United States") site:ashbyhq.com -canada',
        "location": "Remote, US",
        "role": "Applied Scientist",
        "ats": "Ashby",
        "priority": "medium"
    },
    {
        "query": '("Research Engineer" OR "ML Research Engineer") ("New York" OR "San Francisco" OR "Boston") site:ashbyhq.com',
        "location": "Various, US",
        "role": "Research Engineer",
        "ats": "Ashby",
        "priority": "medium"
    },
    {
        "query": '("ML Platform Engineer" OR "ML Infrastructure Engineer") ("San Francisco" OR "New York") site:ashbyhq.com',
        "location": "Various, US",
        "role": "ML Platform Engineer",
        "ats": "Ashby",
        "priority": "medium"
    },
    {
        "query": '("Machine Learning Scientist" OR "ML Scientist") ("New York" OR "San Francisco" OR "Boston") site:ashbyhq.com',
        "location": "Various, US",
        "role": "ML Scientist",
        "ats": "Ashby",
        "priority": "medium"
    },

    # ========================================
    # SECONDARY MARKETS
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") "Seattle" site:ashbyhq.com -senior',
        "location": "Seattle, US",
        "role": "AI/ML Engineer",
        "ats": "Ashby",
        "priority": "medium"
    },
    {
        "query": '("ML Engineer") "Seattle" site:greenhouse.io -senior',
        "location": "Seattle, US",
        "role": "ML Engineer",
        "ats": "Greenhouse",
        "priority": "medium"
    },

    # ========================================
    # TOP COMPANIES (Direct searches)
    # ========================================

    {
        "query": 'site:openai.com/careers ("engineer" OR "researcher") -senior',
        "location": "Various, US",
        "role": "Engineer/Researcher",
        "ats": "OpenAI",
        "priority": "high"
    },
    {
        "query": 'site:anthropic.com/careers "engineer" -senior',
        "location": "Various, US",
        "role": "Engineer",
        "ats": "Anthropic",
        "priority": "high"
    },
    {
        "query": 'site:scale.ai/careers ("machine learning" OR "AI") -senior',
        "location": "Various, US",
        "role": "ML/AI",
        "ats": "Scale AI",
        "priority": "high"
    },
    {
        "query": 'site:cohere.com/careers "engineer" -senior',
        "location": "Various, US",
        "role": "Engineer",
        "ats": "Cohere",
        "priority": "medium"
    },
    {
        "query": 'site:huggingface.co/careers ("machine learning" OR "engineer") -senior',
        "location": "Various, US",
        "role": "ML Engineer",
        "ats": "HuggingFace",
        "priority": "medium"
    },
]


# ========================================
# HELPER FUNCTIONS
# ========================================

def normalize_url(url):
    """Normalize URL for better deduplication"""
    parsed = urlparse(url)

    # Remove tracking parameters
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
    """Load previously seen job URLs"""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(seen_jobs):
    """Save seen job URLs"""
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(list(seen_jobs), f)


def search_google_with_retry(query, api_key, search_engine_id, date_restrict='d1', max_retries=3):
    """
    Execute Google Custom Search API query with exponential backoff on rate limits
    """
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
                # Rate limit hit - exponential backoff
                wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s
                print(f"   ⏳ Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if '429' in str(e):
                wait_time = (2 ** attempt) * 5
                print(f"   ⏳ Rate limit. Retry {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
            else:
                print(f"   ❌ HTTP Error: {str(e)[:80]}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {str(e)[:80]}")
            return None

    print(f"   ❌ Failed after {max_retries} retries (rate limit)")
    return None


def extract_company_name(url, title):
    """Extract company name from URL or title"""
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
        if 'jobs.lever.co' in url and len(parts) > 3:
            return parts[3].replace('-', ' ').title()

    company_map = {
        'openai.com': 'OpenAI',
        'anthropic.com': 'Anthropic',
        'scale.ai': 'Scale AI',
        'cohere.com': 'Cohere',
        'nvidia.com': 'NVIDIA',
        'meta.com': 'Meta',
        'google.com': 'Google',
        'amazon.jobs': 'Amazon',
        'huggingface.co': 'HuggingFace',
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
    """Parse Google search results into job data"""
    jobs = []

    if not results or 'items' not in results:
        return jobs

    for item in results['items']:
        url = item.get('link', '')
        normalized_url = normalize_url(url)

        job = {
            'title': item.get('title', 'No Title'),
            'company': extract_company_name(url, item.get('title', '')),
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
    """Save jobs to CSV file"""
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
    """Main execution function"""
    print("=" * 60)
    print("🚀 AI/ML JOB SCRAPER - RATE LIMIT SAFE")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total Searches: {len(SEARCHES)}")
    print(f"⚡ Pagination: {'Enabled (30 results)' if ENABLE_PAGINATION else 'Disabled (10 results)'}")
    print("=" * 60)

    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        print("❌ ERROR: Missing API keys in .env file")
        return

    seen_jobs = load_seen_jobs()
    all_new_jobs = []
    total_searches = len(SEARCHES)

    for idx, search_config in enumerate(SEARCHES, 1):
        priority = search_config.get('priority', 'medium')
        print(
            f"\n[{idx}/{total_searches}] {priority.upper()} | {search_config['role']} in {search_config['location']} ({search_config['ats']})")

        results = search_google_with_retry(
            query=search_config['query'],
            api_key=GOOGLE_API_KEY,
            search_engine_id=SEARCH_ENGINE_ID
        )

        if results:
            jobs = parse_job_results(results, search_config)
            new_jobs = [job for job in jobs if job['normalized_url'] not in seen_jobs]

            if new_jobs:
                print(f"   ✨ Found {len(new_jobs)} new jobs")
                all_new_jobs.extend(new_jobs)
                seen_jobs.update([job['normalized_url'] for job in new_jobs])
            else:
                print(f"   ℹ️  No new jobs")

        if idx < total_searches:
            time.sleep(DELAY_BETWEEN_SEARCHES)

    if all_new_jobs:
        save_to_csv(all_new_jobs, OUTPUT_FILE)
        save_seen_jobs(seen_jobs)

        print("\n" + "=" * 60)
        print(f"🎉 SUCCESS! Found {len(all_new_jobs)} NEW jobs")
        print(f"📊 Total unique jobs tracked: {len(seen_jobs)}")
        print(f"📁 Results: {OUTPUT_FILE}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ℹ️  No new jobs this run")
        print(f"📊 Total tracked: {len(seen_jobs)}")
        print("=" * 60)


if __name__ == "__main__":
    main()