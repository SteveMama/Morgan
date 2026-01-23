# #!/usr/bin/env python3
# """
# AI/ML Job Scraper - QUICK WINS VERSION
# - Fit scoring personalized to your resume
# - Pagination (30 results per query)
# - Smarter senior role filtering
# - Better US-only filtering
# - Enhanced CSV columns
# """
#
# import requests
# import csv
# import time
# from datetime import datetime
# import json
# import os
# import re
# from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
# from dotenv import load_dotenv
#
# from dotenv import load_dotenv
# load_dotenv(override=True)
# from pathlib import Path
# load_dotenv(Path(__file__).with_name(".env"), override=True)
#
#
# # Configuration
# # GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# # SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
# GOOGLE_API_KEY = "AIzaSyB9Yuy0xXDVO0llKjTKWC2RaxBp85QPZ9M"
# SEARCH_ENGINE_ID = "53b9b86c3baf14a13"
#
#
#
# OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'ai_ml_jobs.csv')
# SEEN_JOBS_FILE = os.getenv('SEEN_JOBS_FILE', 'seen_jobs.json')
# DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 2))
#
# print("KEY prefix:", (GOOGLE_API_KEY or "")[:10])
# print("CX:", SEARCH_ENGINE_ID)
#
#
# # Fit scoring keywords (personalized to your resume)
# KEYWORDS_LLM = ["llm", "generative ai", "rag", "retrieval augmented", "agent", "agentic",
#                 "langchain", "bedrock", "faiss", "pinecone", "chroma", "vector database", "embedding"]
# KEYWORDS_CV = ["computer vision", "vision", "multimodal", "clip", "openclip", "grad-cam",
#                "resnet", "efficientnet", "semantic search", "image classification"]
# KEYWORDS_MLOPS = ["aws", "ecs", "eks", "docker", "kubernetes", "fastapi", "onnx",
#                   "quantization", "ci/cd", "github actions", "mlops", "ml infrastructure"]
#
# # US location indicators
# US_NEGATIVE = ["canada", "uk", "london", "europe", "india", "singapore", "australia", "bangalore", "toronto"]
# US_POSITIVE = ["united states", "u.s.", "usa", "ma", "massachusetts", "boston", "cambridge",
#                "ny", "new york", "nyc", "ca", "california", "san francisco", "seattle", "wa",
#                "remote (us", "remote - us", "remote us", "us only"]
#
# # Hard senior role patterns (regex on title)
# HARD_SENIOR_PATTERNS = [
#     r'\bsenior\b', r'\bsr\.?\s', r'\bstaff\b', r'\bprincipal\b',
#     r'\bdirector\b', r'\bvp\b', r'\bvice president\b', r'\bhead of\b',
#     r'\bchief\b', r'\bmanager\b.*engineer', r'\bengineering manager\b'
# ]
#
# # Target title patterns
# TARGET_TITLE_PATTERNS = [
#     r'\bai engineer\b', r'\bmachine learning engineer\b', r'\bml engineer\b',
#     r'\bllm engineer\b', r'\bgenerative ai\b',
#     r'\bapplied scientist\b', r'\bresearch scientist\b',
#     r'\bdata scientist\b', r'\bmachine learning scientist\b',
#     r'\bcomputer vision\b', r'\bmlops engineer\b'
# ]
#
# # Searches
# SEARCHES = [
#     # US-wide
#     {"query": '("AI Engineer" OR "Machine Learning Engineer") "United States" site:ashbyhq.com', "location": "United States", "role": "AI/ML Engineer", "ats": "Ashby"},
#     {"query": '("AI Engineer" OR "ML Engineer") "United States" site:greenhouse.io', "location": "United States", "role": "AI/ML Engineer", "ats": "Greenhouse"},
#     {"query": '("LLM Engineer" OR "Generative AI Engineer") "United States" site:ashbyhq.com', "location": "United States", "role": "LLM Engineer", "ats": "Ashby"},
#
#     # NYC
#     {"query": '("AI Engineer" OR "Machine Learning Engineer") ("New York" OR "NYC") site:ashbyhq.com', "location": "NYC, US", "role": "AI/ML Engineer", "ats": "Ashby"},
#     {"query": '("LLM Engineer") ("New York" OR "NYC") site:ashbyhq.com', "location": "NYC, US", "role": "LLM Engineer", "ats": "Ashby"},
#
#     # SF/Bay Area
#     {"query": '("AI Engineer" OR "Machine Learning Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com', "location": "SF/Bay Area, US", "role": "AI/ML Engineer", "ats": "Ashby"},
#     {"query": '("LLM Engineer") ("San Francisco") site:ashbyhq.com', "location": "SF/Bay Area, US", "role": "LLM Engineer", "ats": "Ashby"},
#
#     # Boston
#     {"query": '("AI Engineer" OR "Machine Learning Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com', "location": "Boston, US", "role": "AI/ML Engineer", "ats": "Ashby"},
#     {"query": '("ML Engineer") ("Boston" OR "Cambridge") site:greenhouse.io', "location": "Boston, US", "role": "ML Engineer", "ats": "Greenhouse"},
#
#     # Remote
#     {"query": '("AI Engineer" OR "Machine Learning Engineer") ("remote" OR "hybrid") site:ashbyhq.com -canada -uk', "location": "Remote, US", "role": "AI/ML Engineer", "ats": "Ashby"},
#     {"query": '("LLM Engineer") ("remote") site:ashbyhq.com -canada', "location": "Remote, US", "role": "LLM Engineer", "ats": "Ashby"},
# ]
#
#
# def normalize_url(url):
#     """Normalize URL for deduplication"""
#     parsed = urlparse(url)
#     query_params = parse_qs(parsed.query)
#     clean_params = {k: v for k, v in query_params.items()
#                    if not k.startswith('utm_') and k not in ['ref', 'source', 'lever-source']}
#     clean_query = urlencode(clean_params, doseq=True)
#
#     normalized = urlunparse((
#         parsed.scheme.lower(),
#         parsed.netloc.lower(),
#         parsed.path.rstrip('/'),
#         '',
#         clean_query,
#         ''
#     ))
#     return normalized
#
#
# def extract_job_id(url):
#     """Extract job ID from ATS URLs for better deduplication"""
#     # Greenhouse: extract numeric ID
#     if 'greenhouse.io' in url:
#         match = re.search(r'/jobs/(\d+)', url)
#         if match:
#             return f"greenhouse_{match.group(1)}"
#
#     # Ashby: extract UUID
#     if 'ashbyhq.com' in url:
#         match = re.search(r'/([a-f0-9\-]{36})', url)
#         if match:
#             return f"ashby_{match.group(1)}"
#
#     # Lever: extract job ID
#     if 'lever.co' in url:
#         match = re.search(r'/([a-f0-9\-]+)(?:/apply)?$', url)
#         if match:
#             return f"lever_{match.group(1)}"
#
#     # Workday: extract requisition ID
#     if 'myworkdayjobs.com' in url:
#         match = re.search(r'/job/[^/]+/([^/]+)', url)
#         if match:
#             return f"workday_{match.group(1)}"
#
#     # Fallback to normalized URL
#     return normalize_url(url)
#
#
# def load_seen_jobs():
#     """Load seen jobs"""
#     if os.path.exists(SEEN_JOBS_FILE):
#         with open(SEEN_JOBS_FILE, 'r') as f:
#             return set(json.load(f))
#     return set()
#
#
# def save_seen_jobs(seen_jobs):
#     """Save seen jobs"""
#     with open(SEEN_JOBS_FILE, 'w') as f:
#         json.dump(list(seen_jobs), f)
#
#
# def search_google_paginated(query, api_key, search_engine_id, date_restrict='d1', max_results=30):
#     """Execute Google API search with pagination (up to 30 results)"""
#     base_url = "https://www.googleapis.com/customsearch/v1"
#     all_items = []
#
#     # Fetch 3 pages: start=1, 11, 21
#     for start in [1, 11, 21]:
#         if len(all_items) >= max_results:
#             break
#
#         params = {
#             'key': api_key,
#             'cx': search_engine_id,
#             'q': query,
#             'dateRestrict': date_restrict,
#             'num': 10,
#             'start': start
#         }
#
#         try:
#             response = requests.get(base_url, params=params, timeout=10)
#
#             if response.status_code != 200:
#                 # Google usually returns JSON with details like: error.message, error.errors[0].reason
#                 try:
#                     err = response.json()
#                 except Exception:
#                     err = response.text
#                 print(f"   HTTP {response.status_code} at page {start // 10 + 1}: {err}")
#                 break
#
#             data = response.json()
#
#             if 'items' in data:
#                 all_items.extend(data['items'])
#             else:
#                 break
#
#         except requests.exceptions.RequestException as e:
#             print(f"   Error at page {start//10 + 1}: {str(e)[:50]}")
#             break
#
#         time.sleep(0.5)  # Brief delay between pages
#
#     return {'items': all_items} if all_items else None
#
#
# def is_hard_senior(title):
#     """Check if title contains hard senior role indicators"""
#     title_lower = title.lower()
#     return any(re.search(pattern, title_lower) for pattern in HARD_SENIOR_PATTERNS)
#
#
# def is_us_location(title, snippet):
#     """Check if job is likely US-based"""
#     text = f"{title} {snippet}".lower()
#
#     # If contains negative indicators and no positive ones, reject
#     has_negative = any(neg in text for neg in US_NEGATIVE)
#     has_positive = any(pos in text for pos in US_POSITIVE)
#
#     if has_negative and not has_positive:
#         return False
#
#     return True
#
#
# def compute_fit_score(title, snippet):
#     """Compute fit score (0-100) based on your resume strengths"""
#     text = f"{title} {snippet}".lower()
#     score = 0
#     reasons = []
#     matched_keywords = []
#
#     # Target title match (+30)
#     if any(re.search(pattern, title.lower()) for pattern in TARGET_TITLE_PATTERNS):
#         score += 30
#         reasons.append("target_title")
#
#     # LLM/GenAI keywords (+25)
#     llm_matches = [k for k in KEYWORDS_LLM if k in text]
#     if llm_matches:
#         score += 25
#         reasons.append("llm_genai")
#         matched_keywords.extend(llm_matches[:3])
#
#     # Computer Vision keywords (+20)
#     cv_matches = [k for k in KEYWORDS_CV if k in text]
#     if cv_matches:
#         score += 20
#         reasons.append("cv_multimodal")
#         matched_keywords.extend(cv_matches[:3])
#
#     # MLOps keywords (+15)
#     mlops_matches = [k for k in KEYWORDS_MLOPS if k in text]
#     if mlops_matches:
#         score += 15
#         reasons.append("mlops_aws")
#         matched_keywords.extend(mlops_matches[:3])
#
#     # Soft penalties for ambiguous senior indicators
#     if re.search(r'\blead\s', title.lower()) or title.lower().startswith('lead '):
#         score -= 15
#         reasons.append("lead_penalty")
#
#     return score, ", ".join(reasons), ", ".join(matched_keywords[:5])
#
#
# def extract_company_name(url, title):
#     """Extract company name"""
#     if 'ashbyhq.com' in url:
#         parts = url.split('/')
#         for i, part in enumerate(parts):
#             if 'jobs.ashbyhq.com' in url and i + 1 < len(parts):
#                 return parts[i + 1].replace('-', ' ').title()
#
#     if 'greenhouse.io' in url:
#         parts = url.split('/')
#         if 'boards' in parts:
#             idx = parts.index('boards')
#             if idx + 1 < len(parts):
#                 return parts[idx + 1].replace('-', ' ').title()
#
#     if 'lever.co' in url:
#         parts = url.split('/')
#         if len(parts) > 3:
#             return parts[3].replace('-', ' ').title()
#
#     if ' at ' in title:
#         return title.split(' at ')[-1].strip()
#     if ' - ' in title:
#         parts = title.split(' - ')
#         if len(parts) > 1:
#             return parts[-1].strip()
#
#     return "Unknown Company"
#
#
# def parse_job_results(results, metadata):
#     """Parse results with fit scoring and smart filtering"""
#     jobs = []
#
#     if not results or 'items' not in results:
#         return jobs
#
#     for item in results['items']:
#         url = item.get('link', '')
#         title = item.get('title', 'No Title')
#         snippet = item.get('snippet', '')
#
#         # Hard filters
#         if is_hard_senior(title):
#             print(f"   FILTERED (senior): {title[:50]}")
#             continue
#
#         if not is_us_location(title, snippet):
#             print(f"   FILTERED (non-US): {title[:50]}")
#             continue
#
#         # Compute fit score
#         fit_score, fit_reasons, keywords_matched = compute_fit_score(title, snippet)
#
#         # Only keep jobs with fit score >= 35
#         if fit_score < 35:
#             print(f"   FILTERED (low fit={fit_score}): {title[:50]}")
#             continue
#
#         job_id = extract_job_id(url)
#
#         job = {
#             'title': title,
#             'company': extract_company_name(url, title),
#             'url': url,
#             'job_id': job_id,
#             'snippet': snippet,
#             'location': metadata['location'],
#             'role_category': metadata['role'],
#             'ats': metadata['ats'],
#             'source_query': metadata['query'][:60],
#             'fit_score': fit_score,
#             'fit_reasons': fit_reasons,
#             'keywords_matched': keywords_matched,
#             'date_found': datetime.now().strftime('%Y-%m-%d %H:%M'),
#             'status': 'Not Applied'
#         }
#         jobs.append(job)
#
#     return jobs
#
#
# def save_to_csv(jobs, filename):
#     """Save to CSV with enhanced columns"""
#     if not jobs:
#         return
#
#     file_exists = os.path.exists(filename)
#
#     with open(filename, 'a', newline='', encoding='utf-8') as f:
#         fieldnames = ['fit_score', 'title', 'company', 'location', 'role_category', 'ats',
#                      'keywords_matched', 'fit_reasons', 'url', 'date_found', 'status', 'snippet']
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#
#         if not file_exists:
#             writer.writeheader()
#
#         for job in jobs:
#             row = {k: v for k, v in job.items() if k != 'job_id' and k != 'source_query'}
#             writer.writerow(row)
#
#
# def main():
#     """Main execution"""
#     print("=" * 60)
#     print("AI/ML JOB SCRAPER - QUICK WINS VERSION")
#     print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     print(f"Searches: {len(SEARCHES)}")
#     print("Features: Fit scoring, Pagination, Smart filtering")
#     print("=" * 60)
#
#     if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
#         print("ERROR: Missing API keys")
#         return
#
#     seen_jobs = load_seen_jobs()
#     all_new_jobs = []
#
#     for idx, search_config in enumerate(SEARCHES, 1):
#         print(f"\n[{idx}/{len(SEARCHES)}] {search_config['role']} in {search_config['location']} ({search_config['ats']})")
#
#         results = search_google_paginated(
#             query=search_config['query'],
#             api_key=GOOGLE_API_KEY,
#             search_engine_id=SEARCH_ENGINE_ID,
#             max_results=30
#         )
#
#         if results:
#             jobs = parse_job_results(results, search_config)
#             new_jobs = [job for job in jobs if job['job_id'] not in seen_jobs]
#
#             if new_jobs:
#                 print(f"   Found {len(new_jobs)} high-fit jobs")
#                 all_new_jobs.extend(new_jobs)
#                 seen_jobs.update([job['job_id'] for job in new_jobs])
#             else:
#                 print(f"   No new jobs")
#
#         time.sleep(DELAY_BETWEEN_SEARCHES)
#
#     # Sort by fit score
#     all_new_jobs.sort(key=lambda x: x['fit_score'], reverse=True)
#
#     if all_new_jobs:
#         save_to_csv(all_new_jobs, OUTPUT_FILE)
#         save_seen_jobs(seen_jobs)
#
#         print("\n" + "=" * 60)
#         print(f"SUCCESS! Found {len(all_new_jobs)} high-fit jobs")
#         print(f"Top score: {all_new_jobs[0]['fit_score']}")
#         print(f"Saved to: {OUTPUT_FILE}")
#         print("=" * 60)
#     else:
#         print("\n" + "=" * 60)
#         print("No new jobs this run")
#         print("=" * 60)
#
#
# if __name__ == "__main__":
#     main()

# !/usr/bin/env python3
"""
AI/ML Job Scraper
- Fit scoring based on resume keywords
- Pagination (30 results per query)
- Senior role filtering
- US-only filtering
- CSV output with scoring
"""

import requests
import csv
import time
from datetime import datetime
import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).with_name(".env"), override=True)

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'ai_ml_jobs.csv')
SEEN_JOBS_FILE = os.getenv('SEEN_JOBS_FILE', 'seen_jobs.json')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 2))

if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
    raise ValueError("Missing GOOGLE_API_KEY or SEARCH_ENGINE_ID in .env")

print(f"API Key prefix: {GOOGLE_API_KEY[:10]}...")
print(f"Search Engine ID: {SEARCH_ENGINE_ID}")

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
               "bangalore", "toronto", "berlin", "paris", "tokyo"]

US_POSITIVE = ["united states", "u.s.", "usa", "massachusetts", "boston", "cambridge",
               "new york", "nyc", "california", "san francisco", "seattle", "austin",
               "remote (us", "remote - us", "remote us", "us only", "us-remote"]

# Senior role patterns (title only)
SENIOR_PATTERNS = [
    r'\b(senior|sr\.?)\b',
    r'\b(staff|principal|lead|director)\b',
    r'\b(vp|vice president|head of|chief)\b',
    r'\b(manager|engineering manager)\b'
]

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

# Search queries
SEARCHES = [
    # US-wide
    {"query": '("AI Engineer" OR "Machine Learning Engineer") "United States" site:ashbyhq.com',
     "location": "United States", "role": "AI/ML Engineer", "ats": "Ashby"},

    {"query": '("AI Engineer" OR "ML Engineer") "United States" site:greenhouse.io',
     "location": "United States", "role": "AI/ML Engineer", "ats": "Greenhouse"},

    {"query": '("LLM Engineer" OR "Generative AI Engineer") "United States" site:ashbyhq.com',
     "location": "United States", "role": "LLM Engineer", "ats": "Ashby"},

    # NYC
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("New York" OR "NYC") site:ashbyhq.com',
     "location": "NYC", "role": "AI/ML Engineer", "ats": "Ashby"},

    {"query": '("LLM Engineer") ("New York" OR "NYC") site:ashbyhq.com',
     "location": "NYC", "role": "LLM Engineer", "ats": "Ashby"},

    # SF/Bay Area
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com',
     "location": "SF/Bay Area", "role": "AI/ML Engineer", "ats": "Ashby"},

    {"query": '("LLM Engineer") ("San Francisco") site:ashbyhq.com',
     "location": "SF/Bay Area", "role": "LLM Engineer", "ats": "Ashby"},

    # Boston
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com',
     "location": "Boston", "role": "AI/ML Engineer", "ats": "Ashby"},

    {"query": '("ML Engineer") ("Boston" OR "Cambridge") site:greenhouse.io',
     "location": "Boston", "role": "ML Engineer", "ats": "Greenhouse"},

    # Remote
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("remote" OR "hybrid") site:ashbyhq.com -canada -uk',
     "location": "Remote US", "role": "AI/ML Engineer", "ats": "Ashby"},

    {"query": '("LLM Engineer") ("remote") site:ashbyhq.com -canada',
     "location": "Remote US", "role": "LLM Engineer", "ats": "Ashby"},
]


def normalize_url(url):
    """Normalize URL for deduplication by removing tracking parameters"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    clean_params = {k: v for k, v in query_params.items()
                    if not k.startswith('utm_') and k not in ['ref', 'source', 'lever-source']}

    clean_query = urlencode(clean_params, doseq=True)

    return urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip('/'),
        '',
        clean_query,
        ''
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
        match = re.search(r'/([a-f0-9\-]+)(?:/apply)?$', url)
        if match:
            return f"lever_{match.group(1)}"

    if 'myworkdayjobs.com' in url:
        match = re.search(r'/job/[^/]+/([^/]+)', url)
        if match:
            return f"workday_{match.group(1)}"

    return normalize_url(url)


def load_seen_jobs():
    """Load previously seen job IDs"""
    if os.path.exists(SEEN_JOBS_FILE):
        with open(SEEN_JOBS_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(seen_jobs):
    """Save seen job IDs to file"""
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(list(seen_jobs), f, indent=2)


def search_google_paginated(query, api_key, search_engine_id, date_restrict='d1', max_results=30):
    """Execute Google Custom Search with pagination (up to 30 results)"""
    base_url = "https://www.googleapis.com/customsearch/v1"
    all_items = []

    # Google allows 10 results per page, starting at 1, 11, 21
    for start in [1, 11, 21]:
        if len(all_items) >= max_results:
            break

        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': query,
            'dateRestrict': date_restrict,
            'num': 10,
            'start': start
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)

            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                except:
                    error_msg = response.text[:100]

                print(f"   HTTP {response.status_code} at page {start // 10 + 1}: {error_msg}")
                break

            data = response.json()

            if 'items' in data:
                all_items.extend(data['items'])
            else:
                break

        except requests.exceptions.RequestException as e:
            print(f"   Request error at page {start // 10 + 1}: {str(e)[:60]}")
            break

        time.sleep(0.5)

    return {'items': all_items} if all_items else None


def is_senior_role(title):
    """Check if title indicates senior/lead role"""
    title_lower = title.lower()
    return any(re.search(pattern, title_lower, re.IGNORECASE) for pattern in SENIOR_PATTERNS)


def is_us_location(title, snippet):
    """Check if job is US-based using location indicators"""
    text = f"{title} {snippet}".lower()

    has_negative = any(neg in text for neg in US_NEGATIVE)
    has_positive = any(pos in text for pos in US_POSITIVE)

    # Require at least one positive indicator
    if has_negative and not has_positive:
        return False

    # If remote without location, check for US-specific patterns
    if 'remote' in text and not has_positive and not has_negative:
        return False

    return has_positive


def count_keyword_matches(text, keywords):
    """Count keyword matches using word boundaries"""
    matches = []
    for keyword in keywords:
        # Use word boundaries for multi-word phrases
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            matches.append(keyword)
    return matches


def compute_fit_score(title, snippet):
    """Compute fit score (0-100) based on resume alignment"""
    text = f"{title} {snippet}".lower()
    score = 0
    reasons = []

    # Target title match (30 points)
    if any(re.search(pattern, title.lower()) for pattern in TARGET_TITLE_PATTERNS):
        score += 30
        reasons.append("target_title")

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

    # Penalty for ambiguous lead indicators
    if re.search(r'\blead\s', title.lower()) or title.lower().startswith('lead '):
        score -= 15
        reasons.append("lead_penalty")

    all_matches = llm_matches + cv_matches + mlops_matches
    keywords_str = ", ".join(all_matches[:5])

    return score, ", ".join(reasons), keywords_str


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

    # Extract from title patterns
    if ' at ' in title:
        return title.split(' at ')[-1].strip()

    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) > 1:
            return parts[-1].strip()

    return "Unknown"


def parse_job_results(results, metadata):
    """Parse search results with filtering and scoring"""
    jobs = []

    if not results or 'items' not in results:
        return jobs

    for item in results['items']:
        url = item.get('link', '')
        title = item.get('title', 'No Title')
        snippet = item.get('snippet', '')

        # Filter 1: Senior roles
        if is_senior_role(title):
            print(f"   FILTERED (senior): {title[:60]}")
            continue

        # Filter 2: Non-US locations
        if not is_us_location(title, snippet):
            print(f"   FILTERED (non-US): {title[:60]}")
            continue

        # Compute fit score
        fit_score, fit_reasons, keywords_matched = compute_fit_score(title, snippet)

        # Filter 3: Low fit score
        if fit_score < 35:
            print(f"   FILTERED (fit={fit_score}): {title[:60]}")
            continue

        job_id = extract_job_id(url)

        job = {
            'title': title,
            'company': extract_company_name(url, title),
            'url': url,
            'job_id': job_id,
            'snippet': snippet[:200],
            'location': metadata['location'],
            'role_category': metadata['role'],
            'ats': metadata['ats'],
            'fit_score': fit_score,
            'fit_reasons': fit_reasons,
            'keywords_matched': keywords_matched,
            'date_found': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'status': 'Not Applied'
        }
        jobs.append(job)

    return jobs


def save_to_csv(jobs, filename):
    """Save jobs to CSV with fit scoring columns"""
    if not jobs:
        return

    file_exists = os.path.exists(filename)

    fieldnames = [
        'fit_score', 'title', 'company', 'location', 'role_category', 'ats',
        'keywords_matched', 'fit_reasons', 'url', 'date_found', 'status', 'snippet'
    ]

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for job in jobs:
            row = {k: job[k] for k in fieldnames}
            writer.writerow(row)


def main():
    """Main execution"""
    print("=" * 70)
    print("AI/ML JOB SCRAPER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Queries: {len(SEARCHES)}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 70)

    seen_jobs = load_seen_jobs()
    all_new_jobs = []

    for idx, search_config in enumerate(SEARCHES, 1):
        print(
            f"\n[{idx}/{len(SEARCHES)}] {search_config['role']} | {search_config['location']} | {search_config['ats']}")

        results = search_google_paginated(
            query=search_config['query'],
            api_key=GOOGLE_API_KEY,
            search_engine_id=SEARCH_ENGINE_ID,
            max_results=30
        )

        if results:
            jobs = parse_job_results(results, search_config)
            new_jobs = [job for job in jobs if job['job_id'] not in seen_jobs]

            if new_jobs:
                print(f"   Found {len(new_jobs)} new high-fit jobs")
                all_new_jobs.extend(new_jobs)
                seen_jobs.update([job['job_id'] for job in new_jobs])
            else:
                print(f"   No new jobs")
        else:
            print(f"   No results")

        time.sleep(DELAY_BETWEEN_SEARCHES)

    # Sort by fit score descending
    all_new_jobs.sort(key=lambda x: x['fit_score'], reverse=True)

    if all_new_jobs:
        save_to_csv(all_new_jobs, OUTPUT_FILE)
        save_seen_jobs(seen_jobs)

        print("\n" + "=" * 70)
        print(f"SUCCESS: Found {len(all_new_jobs)} high-fit jobs")
        print(f"Top score: {all_new_jobs[0]['fit_score']}")
        print(f"Saved to: {OUTPUT_FILE}")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("No new jobs found this run")
        print("=" * 70)


if __name__ == "__main__":
    main()


# ## Required .env File
# ```
# GOOGLE_API_KEY = your_actual_key_here
# SEARCH_ENGINE_ID = your_actual_cx_here
# OUTPUT_FILE = ai_ml_jobs.csv
# SEEN_JOBS_FILE = seen_jobs.json
# DELAY_BETWEEN_SEARCHES = 2