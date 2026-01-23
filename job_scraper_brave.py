#!/usr/bin/env python3
"""
AI/ML Job Scraper - PRODUCTION VERSION
- Brave Search API with correct pagination
- ATS page verification for posted dates
- Relaxed US filtering with verification
- Improved keyword matching (separator-tolerant)
- Better deduplication and scoring
- Enhanced CSV output with actionable data
"""

import requests
import csv
import time
from datetime import datetime, timedelta
import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv(Path(__file__).with_name(".env"), override=True)

# Configuration
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY', '').strip()
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'ai_ml_jobs.csv')
TOP_JOBS_FILE = 'ai_ml_jobs_top10_today.csv'
SEEN_JOBS_FILE = os.getenv('SEEN_JOBS_FILE', 'seen_jobs.json')
DELAY_BETWEEN_SEARCHES = float(os.getenv('DELAY_BETWEEN_SEARCHES', '1'))
MAX_RESULTS_PER_QUERY = int(os.getenv('MAX_RESULTS_PER_QUERY', '20'))
VERIFY_JOB_PAGES = os.getenv('VERIFY_JOB_PAGES', 'false').lower() == 'true'
MAX_HOURS_OLD = int(os.getenv('MAX_HOURS_OLD', '24'))
FRESHNESS = os.getenv('FRESHNESS', 'pd')  # pd=past day, pw=past week, pm=past month

if not BRAVE_API_KEY:
    raise ValueError("Missing BRAVE_API_KEY in .env file")

print(f"Brave API Key: {BRAVE_API_KEY[:10]}...")
print(f"Freshness filter: {FRESHNESS} (pd=24h, pw=7d, pm=30d)")
print(f"Verify job pages: {VERIFY_JOB_PAGES}")
print(f"Max hours old: {MAX_HOURS_OLD}")

# Resume keyword categories
KEYWORDS_LLM = ["llm", "generative ai", "rag", "retrieval augmented", "agent", "agentic",
                "langchain", "bedrock", "faiss", "pinecone", "chroma", "vector database",
                "embedding", "prompt engineering"]

KEYWORDS_CV = ["computer vision", "vision", "multimodal", "clip", "openclip", "grad-cam",
               "resnet", "efficientnet", "semantic search", "image classification",
               "object detection", "segmentation"]

KEYWORDS_MLOPS = ["aws", "ecs", "eks", "docker", "kubernetes", "fastapi", "onnx",
                  "quantization", "ci/cd", "github actions", "mlops", "ml infrastructure",
                  "terraform", "cloudformation"]

# Location filters
US_NEGATIVE = ["canada", "uk", "london", "europe", "india", "singapore", "australia",
               "bangalore", "toronto", "berlin", "paris", "tokyo", "remote - eu", "remote eu"]

US_POSITIVE = ["united states", "u.s.", "usa", "massachusetts", "boston", "cambridge",
               "new york", "nyc", "california", "san francisco", "seattle", "austin",
               "remote (us", "remote - us", "remote us", "us only", "us-remote"]

# Senior role patterns
SENIOR_PATTERNS = [
    r'\b(senior|sr\.?)\b',
    r'\b(staff|principal|director)\b',
    r'\b(vp|vice president|head of|chief)\b',
    r'\b(engineering manager)\b'
]

# Entry-level hints (exceptions to senior filter)
ENTRY_HINTS = ["new grad", "new graduate", "intern", "entry level", "junior", "associate"]

# Target title patterns
TARGET_TITLE_PATTERNS = [
    r'\bai engineer\b',
    r'\bmachine learning engineer\b',
    r'\bml engineer\b',
    r'\bllm engineer\b',
    r'\bgenerative ai\b',
    r'\bapplied scientist\b',
    r'\bresearch scientist\b',
    r'\bdata scientist\b',
    r'\bcomputer vision\b',
    r'\bmlops engineer\b'
]

# Negative hints in description (reduce false positives)
NEGATIVE_HINTS = ["phd required", "10+ years", "12+ years", "15+ years",
                  "principal engineer", "staff engineer", "director"]

# Search queries
SEARCHES = [
    # US-wide
    {"query": '("AI Engineer" OR "Machine Learning Engineer") "United States" site:ashbyhq.com',
     "location": "United States", "role": "AI/ML Engineer", "ats": "Ashby", "tag": "us-wide"},

    {"query": '("AI Engineer" OR "ML Engineer") "United States" site:greenhouse.io',
     "location": "United States", "role": "AI/ML Engineer", "ats": "Greenhouse", "tag": "us-wide"},

    {"query": '("LLM Engineer" OR "Generative AI Engineer") "United States" site:ashbyhq.com',
     "location": "United States", "role": "LLM Engineer", "ats": "Ashby", "tag": "us-wide"},

    # NYC
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("New York" OR "NYC") site:ashbyhq.com',
     "location": "NYC", "role": "AI/ML Engineer", "ats": "Ashby", "tag": "nyc"},

    {"query": '("LLM Engineer") ("New York" OR "NYC") site:ashbyhq.com',
     "location": "NYC", "role": "LLM Engineer", "ats": "Ashby", "tag": "nyc"},

    # SF/Bay Area
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com',
     "location": "SF/Bay Area", "role": "AI/ML Engineer", "ats": "Ashby", "tag": "sf-bay"},

    {"query": '("LLM Engineer") ("San Francisco") site:ashbyhq.com',
     "location": "SF/Bay Area", "role": "LLM Engineer", "ats": "Ashby", "tag": "sf-bay"},

    # Boston
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com',
     "location": "Boston", "role": "AI/ML Engineer", "ats": "Ashby", "tag": "boston"},

    {"query": '("ML Engineer") ("Boston" OR "Cambridge") site:greenhouse.io',
     "location": "Boston", "role": "ML Engineer", "ats": "Greenhouse", "tag": "boston"},

    # Remote
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("remote" OR "hybrid") site:ashbyhq.com -canada -uk',
     "location": "Remote US", "role": "AI/ML Engineer", "ats": "Ashby", "tag": "remote"},

    {"query": '("LLM Engineer") ("remote") site:ashbyhq.com -canada',
     "location": "Remote US", "role": "LLM Engineer", "ats": "Ashby", "tag": "remote"},
]


def normalize_url(url):
    """Normalize URL for deduplication - remove fragments, tracking params, apply suffix"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Remove tracking parameters
    clean_params = {k: v for k, v in query_params.items()
                    if not k.startswith('utm_') and k not in ['ref', 'source', 'lever-source', 'gh_jid']}

    clean_query = urlencode(clean_params, doseq=True)

    # Remove /apply suffix for Lever
    path = parsed.path.rstrip('/')
    if path.endswith('/apply'):
        path = path[:-6]

    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        '',
        clean_query,
        ''  # Remove fragment
    ))


def extract_job_id(url):
    """Extract unique job ID from ATS URLs"""
    if 'greenhouse.io' in url:
        match = re.search(r'/jobs/(\d+)', url)
        if match:
            return f"greenhouse_{match.group(1)}"

    if 'ashbyhq.com' in url:
        match = re.search(r'/([a-f0-9\-]{36})', url)
        if match:
            return f"ashby_{match.group(1)}"

    if 'lever.co' in url:
        match = re.search(r'/([a-f0-9\-]+)(?:/apply)?$', url.rstrip('/'))
        if match:
            return f"lever_{match.group(1)}"

    if 'myworkdayjobs.com' in url:
        match = re.search(r'/job/[^/]+/([^/]+)', url)
        if match:
            return f"workday_{match.group(1)}"

    return normalize_url(url)


def detect_ats(url):
    """Detect ATS type from URL"""
    url_lower = url.lower()
    if 'ashbyhq.com' in url_lower:
        return 'Ashby'
    elif 'greenhouse.io' in url_lower:
        return 'Greenhouse'
    elif 'lever.co' in url_lower:
        return 'Lever'
    elif 'myworkdayjobs.com' in url_lower:
        return 'Workday'
    elif 'icims.com' in url_lower:
        return 'iCIMS'
    else:
        return 'Other'


def load_seen_jobs():
    """Load previously seen job IDs"""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(seen_jobs):
    """Save seen job IDs to file"""
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(sorted(list(seen_jobs)), f, indent=2)


def brave_search_paginated(query, max_results=20, freshness='pd'):
    """
    Execute Brave Search API with CORRECT pagination
    Fix: offset is result index, not page number

    freshness options:
    - 'pd' = past day (24 hours)
    - 'pw' = past week
    - 'pm' = past month
    - 'py' = past year
    """
    base_url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY
    }

    all_results = []
    offset = 0
    count_per_page = 20

    while len(all_results) < max_results:
        remaining = max_results - len(all_results)
        count_this_request = min(count_per_page, remaining)

        params = {
            "q": query,
            "count": count_this_request,
            "offset": offset,
            "country": "us",
            "search_lang": "en",
            "safesearch": "off",
            "freshness": freshness  # Filter by recency
        }

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=15)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Unknown error')
                except:
                    error_msg = response.text[:100]

                print(f"   Brave API Error {response.status_code}: {error_msg}")
                break

            data = response.json()
            web_results = data.get('web', {}).get('results', [])

            if not web_results:
                break

            all_results.extend(web_results)

            # FIXED: offset is result index, not page number
            returned_count = len(web_results)
            offset += returned_count

            # Check if more results available
            query_info = data.get('query', {})
            if not query_info.get('more_results_available', False):
                break

            if returned_count == 0:
                break

            time.sleep(0.3)

        except requests.exceptions.RequestException as e:
            print(f"   Request error: {str(e)[:60]}")
            break

    return all_results[:max_results]


def is_senior_role(title):
    """Check if title indicates senior/lead role with exceptions for entry-level"""
    title_lower = title.lower()

    # Check for entry-level hints first (exceptions)
    if any(hint in title_lower for hint in ENTRY_HINTS):
        return False

    return any(re.search(pattern, title_lower, re.IGNORECASE) for pattern in SENIOR_PATTERNS)


def is_us_location_relaxed(title, description):
    """
    Relaxed US location filter (3-tier):
    1. Reject if explicitly non-US
    2. Accept if explicitly US
    3. Accept if unknown (verify later via ATS page)
    """
    text = f"{title} {description}".lower()

    has_negative = any(neg in text for neg in US_NEGATIVE)
    has_positive = any(pos in text for pos in US_POSITIVE)

    # Tier 1: Explicitly non-US
    if has_negative and not has_positive:
        return False

    # Tier 2 & 3: Explicitly US or unknown (accept both)
    return True


def phrase_pattern(keyword):
    """
    Create separator-tolerant regex pattern for multi-word phrases
    Handles: "generative-ai", "retrieval augmented", "RAG (retrieval augmented)"
    """
    parts = [re.escape(p) for p in keyword.strip().split()]
    if len(parts) > 1:
        return r'\b' + r'[\s\-_\/]+'.join(parts) + r'\b'
    return r'\b' + re.escape(keyword) + r'\b'


def count_keyword_matches(text, keywords):
    """Count keyword matches using separator-tolerant patterns"""
    matches = []
    for keyword in keywords:
        pattern = phrase_pattern(keyword)
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(keyword)
    return matches


def compute_fit_score(title, description):
    """
    Improved fit scoring with negative hints and better keyword matching
    """
    text = f"{title} {description}".lower()
    score = 0
    reasons = []

    # Target title match (30 points)
    if any(re.search(pattern, title.lower()) for pattern in TARGET_TITLE_PATTERNS):
        score += 30
        reasons.append("target_title")
    else:
        # If no title match, require at least some ML keywords
        has_ml_keywords = any(kw in text for kw in ["machine learning", "ml", "ai", "llm"])
        if not has_ml_keywords:
            return 0, "no_ml_content", ""

    # LLM/GenAI keywords (25 points)
    llm_matches = count_keyword_matches(text, KEYWORDS_LLM)
    if llm_matches:
        score += 25
        reasons.append("llm_genai")

    # Computer Vision keywords (20 points)
    cv_matches = count_keyword_matches(text, KEYWORDS_CV)
    if cv_matches:
        score += 20
        reasons.append("cv_multimodal")

    # MLOps keywords (15 points)
    mlops_matches = count_keyword_matches(text, KEYWORDS_MLOPS)
    if mlops_matches:
        score += 15
        reasons.append("mlops_infra")

    # Negative hints penalty
    negative_count = sum(1 for hint in NEGATIVE_HINTS if hint in text)
    if negative_count > 0:
        penalty = min(negative_count * 10, 30)
        score -= penalty
        reasons.append(f"negative_hints_{negative_count}")

    # Lead penalty
    if re.search(r'\blead\s', title.lower()) or title.lower().startswith('lead '):
        score -= 15
        reasons.append("lead_penalty")

    all_matches = llm_matches + cv_matches + mlops_matches
    keywords_str = ", ".join(all_matches[:5])

    return max(score, 0), ", ".join(reasons), keywords_str


def extract_company_name(url, title):
    """Extract company name from URL or title"""
    if 'ashbyhq.com' in url:
        match = re.search(r'jobs\.ashbyhq\.com/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'greenhouse.io' in url:
        match = re.search(r'boards\.greenhouse\.io/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if 'lever.co' in url:
        match = re.search(r'jobs\.lever\.co/([^/]+)', url)
        if match:
            return match.group(1).replace('-', ' ').title()

    if ' at ' in title:
        return title.split(' at ')[-1].strip()

    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) > 1:
            return parts[-1].strip()

    return "Unknown"


def verify_ats_job_page(url):
    """
    Fetch ATS job page and extract:
    - posted_at (datetime)
    - location (verified)
    - employment_type (full-time/intern/contract)
    - remote_status (remote/hybrid/on-site)
    """
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        ats_type = detect_ats(url)

        result = {
            'posted_at': None,
            'location': None,
            'employment_type': None,
            'remote_status': None
        }

        # Ashby-specific parsing
        if ats_type == 'Ashby':
            # Ashby often embeds JSON in script tags
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if '@type' in data and data['@type'] == 'JobPosting':
                        result['posted_at'] = data.get('datePosted')
                        result['location'] = data.get('jobLocation', {}).get('address', {}).get('addressLocality')
                        result['employment_type'] = data.get('employmentType')
                except:
                    pass

        # Greenhouse-specific parsing
        elif ats_type == 'Greenhouse':
            # Look for posted date in metadata
            meta_date = soup.find('meta', property='og:published_time') or soup.find('time')
            if meta_date:
                result['posted_at'] = meta_date.get('content') or meta_date.get('datetime')

            # Location
            location_div = soup.find('div', class_='location')
            if location_div:
                result['location'] = location_div.text.strip()

        # Parse text for remote status
        page_text = soup.get_text().lower()
        if 'remote' in page_text or 'work from home' in page_text:
            if 'hybrid' in page_text:
                result['remote_status'] = 'hybrid'
            else:
                result['remote_status'] = 'remote'
        else:
            result['remote_status'] = 'on-site'

        return result

    except Exception as e:
        return None


def parse_brave_results(results, metadata):
    """Parse Brave Search results with improved filtering"""
    jobs = []

    for item in results:
        url = item.get('url', '')
        title = item.get('title', 'No Title')
        description = item.get('description', '')

        # Detect actual ATS from URL (not from query metadata)
        actual_ats = detect_ats(url)

        # Filter 1: Senior roles (with entry-level exceptions)
        if is_senior_role(title):
            continue

        # Filter 2: Relaxed US location filter
        if not is_us_location_relaxed(title, description):
            continue

        # Compute fit score
        fit_score, fit_reasons, keywords_matched = compute_fit_score(title, description)

        # Filter 3: Low fit score or no ML content
        if fit_score < 35:
            continue

        job_id = extract_job_id(url)

        job = {
            'title': title,
            'company': extract_company_name(url, title),
            'url': url,
            'job_id': job_id,
            'snippet': description[:200],
            'location': metadata['location'],
            'role_category': metadata['role'],
            'ats': actual_ats,  # Use detected ATS, not query metadata
            'query_tag': metadata['tag'],
            'fit_score': fit_score,
            'fit_reasons': fit_reasons,
            'keywords_matched': keywords_matched,
            'date_found': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'posted_at': None,
            'hours_old': None,
            'employment_type': None,
            'remote_status': None,
            'verified_location': None,
            'status': 'Not Applied'
        }
        jobs.append(job)

    return jobs


def verify_jobs_batch(jobs):
    """Verify job pages in parallel to extract posted dates and metadata"""
    if not VERIFY_JOB_PAGES:
        return jobs

    print(f"\n   Verifying {len(jobs)} job pages for posted dates...")

    def verify_job(job):
        verification = verify_ats_job_page(job['url'])
        if verification:
            job['posted_at'] = verification['posted_at']
            job['verified_location'] = verification['location']
            job['employment_type'] = verification['employment_type']
            job['remote_status'] = verification['remote_status']

            # Compute hours_old
            if job['posted_at']:
                try:
                    posted_dt = datetime.fromisoformat(job['posted_at'].replace('Z', '+00:00'))
                    hours_old = (datetime.now(posted_dt.tzinfo) - posted_dt).total_seconds() / 3600
                    job['hours_old'] = round(hours_old, 1)
                except:
                    pass

        return job

    # Use thread pool for concurrent verification (rate-limited)
    verified_jobs = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_job = {executor.submit(verify_job, job): job for job in jobs}

        for future in as_completed(future_to_job):
            try:
                verified_job = future.result(timeout=15)
                verified_jobs.append(verified_job)
            except Exception as e:
                job = future_to_job[future]
                verified_jobs.append(job)

            time.sleep(0.2)  # Rate limit

    print(f"   Verified {len(verified_jobs)} jobs")
    return verified_jobs


def filter_by_posted_date(jobs, max_hours=48):
    """Filter jobs by posted date (only keep recent)"""
    if not VERIFY_JOB_PAGES:
        return jobs

    recent_jobs = []
    for job in jobs:
        if job['hours_old'] is not None:
            if job['hours_old'] <= max_hours:
                recent_jobs.append(job)
        else:
            # Keep jobs where we couldn't verify date (don't lose them)
            recent_jobs.append(job)

    return recent_jobs


def save_to_csv(jobs, filename):
    """Save jobs to CSV with enhanced columns"""
    if not jobs:
        return

    file_exists = os.path.exists(filename)

    fieldnames = [
        'fit_score', 'hours_old', 'title', 'company', 'location', 'verified_location',
        'remote_status', 'employment_type', 'role_category', 'ats', 'query_tag',
        'keywords_matched', 'fit_reasons', 'url', 'posted_at', 'date_found', 'status', 'snippet'
    ]

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for job in jobs:
            row = {k: job.get(k, '') for k in fieldnames}
            writer.writerow(row)


def save_top_jobs(jobs, filename, limit=10):
    """Save top N jobs to separate file for quick review"""
    if not jobs:
        return

    # Sort by fit score, then by hours_old (newer first)
    sorted_jobs = sorted(jobs, key=lambda x: (x['fit_score'], -(x['hours_old'] or 999)), reverse=True)
    top_jobs = sorted_jobs[:limit]

    fieldnames = [
        'fit_score', 'hours_old', 'title', 'company', 'location', 'remote_status',
        'url', 'posted_at', 'keywords_matched'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for job in top_jobs:
            row = {k: job.get(k, '') for k in fieldnames}
            writer.writerow(row)


def main():
    """Main execution"""
    print("=" * 70)
    print("AI/ML JOB SCRAPER - LAST 24 HOURS ONLY")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Queries: {len(SEARCHES)}")
    print(f"Freshness: {FRESHNESS} (searching jobs from last 24 hours)")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 70)

    seen_jobs = load_seen_jobs()
    all_new_jobs = []

    for idx, search_config in enumerate(SEARCHES, 1):
        print(
            f"\n[{idx}/{len(SEARCHES)}] {search_config['role']} | {search_config['location']} | {search_config['ats']}")

        results = brave_search_paginated(
            query=search_config['query'],
            max_results=MAX_RESULTS_PER_QUERY,
            freshness=FRESHNESS  # Use configured freshness
        )

        if results:
            jobs = parse_brave_results(results, search_config)
            new_jobs = [job for job in jobs if job['job_id'] not in seen_jobs]

            if new_jobs:
                print(f"   Found {len(new_jobs)} new high-fit jobs")

                # Verify jobs to get posted dates
                verified_jobs = verify_jobs_batch(new_jobs)

                # Filter by posted date
                recent_jobs = filter_by_posted_date(verified_jobs, MAX_HOURS_OLD)

                if recent_jobs:
                    print(f"   {len(recent_jobs)} jobs posted in last {MAX_HOURS_OLD}h")
                    all_new_jobs.extend(recent_jobs)
                    seen_jobs.update([job['job_id'] for job in recent_jobs])
                else:
                    print(f"   No jobs posted in last {MAX_HOURS_OLD}h")
            else:
                print(f"   No new jobs")
        else:
            print(f"   No results")

        time.sleep(DELAY_BETWEEN_SEARCHES)

    # Sort by fit score descending
    all_new_jobs.sort(key=lambda x: (x['fit_score'], -(x['hours_old'] or 999)), reverse=True)

    if all_new_jobs:
        save_to_csv(all_new_jobs, OUTPUT_FILE)
        save_top_jobs(all_new_jobs, TOP_JOBS_FILE, limit=10)
        save_seen_jobs(seen_jobs)

        print("\n" + "=" * 70)
        print(f"SUCCESS: Found {len(all_new_jobs)} high-fit jobs")
        print(f"Top score: {all_new_jobs[0]['fit_score']}")
        print(f"Saved to: {OUTPUT_FILE}")
        print(f"Top 10 saved to: {TOP_JOBS_FILE}")
        print("=" * 70)

        # Print top 5 for quick review
        print("\nTOP 5 JOBS:")
        for i, job in enumerate(all_new_jobs[:5], 1):
            hours = f"{job['hours_old']}h" if job['hours_old'] else "?"
            print(f"{i}. [{job['fit_score']}] {job['title']} at {job['company']} ({hours} old)")
            print(f"   {job['url']}")
    else:
        print("\n" + "=" * 70)
        print("No new jobs found this run")
        print("=" * 70)


if __name__ == "__main__":
    main()