#!/usr/bin/env python3
"""
AI/ML Job Scraper - COMPLETE VERSION
- Role packs tailored to your resume (LLM/GenAI, CV/Multimodal, Applied Scientist)
- 10+ ATS platforms (Ashby, Greenhouse, Lever, Workday, iCIMS, SmartRecruiters, etc.)
- Pagination (30 results per query)
- Advanced fit scoring
- Better deduplication
- Comprehensive US coverage
"""

import requests
import csv
import time
from datetime import datetime
import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'ai_ml_jobs_complete.csv')
SEEN_JOBS_FILE = os.getenv('SEEN_JOBS_FILE', 'seen_jobs_complete.json')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 2))

# Fit scoring keywords
KEYWORDS_LLM = ["llm", "large language model", "generative ai", "rag", "retrieval augmented", 
                "agent", "agentic", "langchain", "bedrock", "faiss", "pinecone", "chroma", 
                "vector database", "embedding", "prompt engineering", "fine-tuning", "lora"]
KEYWORDS_CV = ["computer vision", "vision", "multimodal", "clip", "openclip", "grad-cam", 
               "resnet", "efficientnet", "vit", "semantic search", "image classification",
               "object detection", "segmentation"]
KEYWORDS_MLOPS = ["aws", "ecs", "eks", "sagemaker", "docker", "kubernetes", "fastapi", "onnx", 
                  "quantization", "ci/cd", "github actions", "mlops", "ml infrastructure",
                  "ml platform", "model deployment", "inference"]

US_NEGATIVE = ["canada", "uk", "london", "europe", "india", "singapore", "australia", "bangalore", "toronto", "berlin", "amsterdam"]
US_POSITIVE = ["united states", "u.s.", "usa", "ma", "massachusetts", "boston", "cambridge", 
               "ny", "new york", "nyc", "ca", "california", "sf", "san francisco", "seattle", 
               "wa", "texas", "austin", "remote (us", "remote - us", "remote us", "us only"]

HARD_SENIOR_PATTERNS = [
    r'\bsenior\b', r'\bsr\.?\s', r'\bstaff\b', r'\bprincipal\b',
    r'\bdirector\b', r'\bvp\b', r'\bvice president\b', r'\bhead of\b', 
    r'\bchief\b', r'\bmanager\b.*engineer', r'\bengineering manager\b'
]

TARGET_TITLE_PATTERNS = [
    r'\bai engineer\b', r'\bmachine learning engineer\b', r'\bml engineer\b',
    r'\bllm engineer\b', r'\bgenerative ai\b', r'\bgenai\b',
    r'\bapplied scientist\b', r'\bresearch scientist\b',
    r'\bdata scientist\b', r'\bmachine learning scientist\b',
    r'\bcomputer vision\b', r'\bmlops engineer\b', r'\bnlp engineer\b'
]

# COMPREHENSIVE SEARCH QUERIES - ROLE PACK STRUCTURE
SEARCHES = [
    # ========================================
    # ROLE PACK 1: LLM / GENERATIVE AI ENGINEER
    # ========================================
    
    # US-wide
    {"query": '("LLM Engineer" OR "Generative AI Engineer" OR "GenAI Engineer") "United States" site:ashbyhq.com', "location": "United States", "role": "LLM Engineer", "ats": "Ashby", "pack": "LLM"},
    {"query": '("LLM Engineer" OR "Generative AI") "United States" site:greenhouse.io', "location": "United States", "role": "LLM Engineer", "ats": "Greenhouse", "pack": "LLM"},
    {"query": '("LLM" OR "Generative AI" OR "RAG") ("engineer" OR "scientist") site:lever.co', "location": "United States", "role": "LLM/GenAI", "ats": "Lever", "pack": "LLM"},
    
    # Major cities
    {"query": '("LLM Engineer" OR "Generative AI Engineer") ("New York" OR "San Francisco" OR "Boston") site:ashbyhq.com', "location": "Major Cities, US", "role": "LLM Engineer", "ats": "Ashby", "pack": "LLM"},
    {"query": '("LLM Engineer") ("remote") site:ashbyhq.com -canada', "location": "Remote, US", "role": "LLM Engineer", "ats": "Ashby", "pack": "LLM"},
    {"query": '("Generative AI") ("remote" OR "hybrid") site:greenhouse.io -canada', "location": "Remote, US", "role": "GenAI Engineer", "ats": "Greenhouse", "pack": "LLM"},
    
    # Additional ATS for LLM roles
    {"query": '("LLM Engineer" OR "Generative AI") site:smartrecruiters.com', "location": "United States", "role": "LLM Engineer", "ats": "SmartRecruiters", "pack": "LLM"},
    {"query": '("LLM" OR "Generative AI") "engineer" site:workable.com', "location": "United States", "role": "LLM Engineer", "ats": "Workable", "pack": "LLM"},
    
    # ========================================
    # ROLE PACK 2: COMPUTER VISION / MULTIMODAL
    # ========================================
    
    # US-wide
    {"query": '("Computer Vision Engineer" OR "CV Engineer") "United States" site:ashbyhq.com', "location": "United States", "role": "CV Engineer", "ats": "Ashby", "pack": "CV"},
    {"query": '("Computer Vision" OR "Multimodal") ("engineer" OR "scientist") site:greenhouse.io', "location": "United States", "role": "CV Engineer", "ats": "Greenhouse", "pack": "CV"},
    
    # Major cities
    {"query": '("Computer Vision Engineer") ("New York" OR "San Francisco" OR "Boston") site:ashbyhq.com', "location": "Major Cities, US", "role": "CV Engineer", "ats": "Ashby", "pack": "CV"},
    {"query": '("Computer Vision") ("remote") site:greenhouse.io -canada', "location": "Remote, US", "role": "CV Engineer", "ats": "Greenhouse", "pack": "CV"},
    
    # ========================================
    # ROLE PACK 3: AI/ML ENGINEER (GENERAL)
    # ========================================
    
    # US-wide
    {"query": '("AI Engineer" OR "Machine Learning Engineer") "United States" site:ashbyhq.com', "location": "United States", "role": "AI/ML Engineer", "ats": "Ashby", "pack": "General"},
    {"query": '("AI Engineer" OR "ML Engineer") "United States" site:greenhouse.io', "location": "United States", "role": "AI/ML Engineer", "ats": "Greenhouse", "pack": "General"},
    {"query": '("Machine Learning Engineer") "United States" site:lever.co', "location": "United States", "role": "ML Engineer", "ats": "Lever", "pack": "General"},
    
    # NYC
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("New York" OR "NYC") site:ashbyhq.com', "location": "NYC, US", "role": "AI/ML Engineer", "ats": "Ashby", "pack": "General"},
    {"query": '("AI Engineer") ("New York" OR "NYC") site:greenhouse.io', "location": "NYC, US", "role": "AI Engineer", "ats": "Greenhouse", "pack": "General"},
    
    # SF/Bay Area
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com', "location": "SF/Bay Area, US", "role": "AI/ML Engineer", "ats": "Ashby", "pack": "General"},
    {"query": '("ML Engineer") ("San Francisco") site:greenhouse.io', "location": "SF/Bay Area, US", "role": "ML Engineer", "ats": "Greenhouse", "pack": "General"},
    
    # Boston
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com', "location": "Boston, US", "role": "AI/ML Engineer", "ats": "Ashby", "pack": "General"},
    {"query": '("ML Engineer") ("Boston" OR "Cambridge") site:greenhouse.io', "location": "Boston, US", "role": "ML Engineer", "ats": "Greenhouse", "pack": "General"},
    
    # Remote
    {"query": '("AI Engineer" OR "Machine Learning Engineer") ("remote" OR "hybrid") site:ashbyhq.com -canada', "location": "Remote, US", "role": "AI/ML Engineer", "ats": "Ashby", "pack": "General"},
    {"query": '("ML Engineer") ("remote US") site:greenhouse.io -canada', "location": "Remote, US", "role": "ML Engineer", "ats": "Greenhouse", "pack": "General"},
    
    # ========================================
    # ROLE PACK 4: APPLIED SCIENTIST
    # ========================================
    
    {"query": '("Applied Scientist") "United States" site:myworkdayjobs.com', "location": "United States", "role": "Applied Scientist", "ats": "Workday", "pack": "Scientist"},
    {"query": '("Applied Scientist" OR "Research Scientist") ("New York" OR "San Francisco" OR "Seattle") site:myworkdayjobs.com', "location": "Major Cities, US", "role": "Applied Scientist", "ats": "Workday", "pack": "Scientist"},
    {"query": '("Applied Scientist") ("remote") site:ashbyhq.com -canada', "location": "Remote, US", "role": "Applied Scientist", "ats": "Ashby", "pack": "Scientist"},
    {"query": '("Machine Learning Scientist") ("United States") site:ashbyhq.com', "location": "United States", "role": "ML Scientist", "ats": "Ashby", "pack": "Scientist"},
    
    # ========================================
    # ROLE PACK 5: MLOPS / ML INFRASTRUCTURE
    # ========================================
    
    {"query": '("MLOps Engineer" OR "ML Infrastructure Engineer") "United States" site:ashbyhq.com', "location": "United States", "role": "MLOps Engineer", "ats": "Ashby", "pack": "MLOps"},
    {"query": '("MLOps" OR "ML Platform") ("engineer") site:greenhouse.io', "location": "United States", "role": "MLOps Engineer", "ats": "Greenhouse", "pack": "MLOps"},
    {"query": '("ML Infrastructure" OR "ML Platform") ("remote") site:lever.co -canada', "location": "Remote, US", "role": "ML Infrastructure", "ats": "Lever", "pack": "MLOps"},
    
    # ========================================
    # ADDITIONAL ATS PLATFORMS (NEW)
    # ========================================
    
    {"query": '("AI Engineer" OR "ML Engineer") ("United States" OR "remote") site:smartrecruiters.com', "location": "United States", "role": "AI/ML Engineer", "ats": "SmartRecruiters", "pack": "General"},
    {"query": '("Machine Learning Engineer") site:jobvite.com', "location": "United States", "role": "ML Engineer", "ats": "Jobvite", "pack": "General"},
    {"query": '("AI Engineer" OR "ML Engineer") site:icims.com', "location": "United States", "role": "AI/ML Engineer", "ats": "iCIMS", "pack": "General"},
    {"query": '("Machine Learning Engineer") site:workable.com', "location": "United States", "role": "ML Engineer", "ats": "Workable", "pack": "General"},
    {"query": '("AI Engineer" OR "LLM Engineer") site:apply.workable.com -canada', "location": "United States", "role": "AI/LLM Engineer", "ats": "Workable", "pack": "LLM"},
]


def normalize_url(url):
    """Normalize URL"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    clean_params = {k: v for k, v in query_params.items() 
                   if not k.startswith('utm_') and k not in ['ref', 'source', 'lever-source']}
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


def extract_job_id(url):
    """Extract job ID from ATS URLs"""
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
    
    if 'icims.com' in url:
        match = re.search(r'/jobs/(\d+)', url)
        if match:
            return f"icims_{match.group(1)}"
    
    return normalize_url(url)


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


def search_google_paginated(query, api_key, search_engine_id, date_restrict='d1', max_results=30):
    """Search with pagination"""
    base_url = "https://www.googleapis.com/customsearch/v1"
    all_items = []
    
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
            
            if response.status_code == 429:
                print(f"   Rate limit at page {start//10 + 1}")
                break
            
            response.raise_for_status()
            data = response.json()
            
            if 'items' in data:
                all_items.extend(data['items'])
            else:
                break
                
        except requests.exceptions.RequestException:
            break
        
        time.sleep(0.5)
    
    return {'items': all_items} if all_items else None


def is_hard_senior(title):
    """Check for hard senior indicators"""
    title_lower = title.lower()
    return any(re.search(pattern, title_lower) for pattern in HARD_SENIOR_PATTERNS)


def is_us_location(title, snippet):
    """Check if US-based"""
    text = f"{title} {snippet}".lower()
    has_negative = any(neg in text for neg in US_NEGATIVE)
    has_positive = any(pos in text for pos in US_POSITIVE)
    
    if has_negative and not has_positive:
        return False
    return True


def compute_fit_score(title, snippet):
    """Compute fit score personalized to your resume"""
    text = f"{title} {snippet}".lower()
    score = 0
    reasons = []
    matched_keywords = []
    
    # Target title (+30)
    if any(re.search(pattern, title.lower()) for pattern in TARGET_TITLE_PATTERNS):
        score += 30
        reasons.append("target_title")
    
    # LLM/GenAI (+25)
    llm_matches = [k for k in KEYWORDS_LLM if k in text]
    if llm_matches:
        score += 25
        reasons.append("llm_genai")
        matched_keywords.extend(llm_matches[:3])
    
    # CV/Multimodal (+20)
    cv_matches = [k for k in KEYWORDS_CV if k in text]
    if cv_matches:
        score += 20
        reasons.append("cv_multimodal")
        matched_keywords.extend(cv_matches[:3])
    
    # MLOps/AWS (+15)
    mlops_matches = [k for k in KEYWORDS_MLOPS if k in text]
    if mlops_matches:
        score += 15
        reasons.append("mlops_aws")
        matched_keywords.extend(mlops_matches[:3])
    
    # Bonus for multiple skill areas
    if len(reasons) >= 3:
        score += 10
        reasons.append("multi_skill")
    
    # Soft penalties
    if re.search(r'\blead\s', title.lower()) or title.lower().startswith('lead '):
        score -= 15
        reasons.append("lead_penalty")
    
    return score, ", ".join(reasons), ", ".join(list(set(matched_keywords))[:5])


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
    
    if ' at ' in title:
        return title.split(' at ')[-1].strip()
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) > 1:
            return parts[-1].strip()
    
    return "Unknown Company"


def parse_job_results(results, metadata):
    """Parse with fit scoring and filtering"""
    jobs = []
    
    if not results or 'items' not in results:
        return jobs
    
    for item in results['items']:
        url = item.get('link', '')
        title = item.get('title', 'No Title')
        snippet = item.get('snippet', '')
        
        # Hard filters
        if is_hard_senior(title):
            continue
        
        if not is_us_location(title, snippet):
            continue
        
        # Compute fit
        fit_score, fit_reasons, keywords_matched = compute_fit_score(title, snippet)
        
        # Keep only high-fit jobs
        if fit_score < 30:
            continue
        
        job_id = extract_job_id(url)
        
        job = {
            'title': title,
            'company': extract_company_name(url, title),
            'url': url,
            'job_id': job_id,
            'snippet': snippet,
            'location': metadata['location'],
            'role_category': metadata['role'],
            'ats': metadata['ats'],
            'role_pack': metadata['pack'],
            'source_query': metadata['query'][:60],
            'fit_score': fit_score,
            'fit_reasons': fit_reasons,
            'keywords_matched': keywords_matched,
            'date_found': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'status': 'Not Applied'
        }
        jobs.append(job)
    
    return jobs


def save_to_csv(jobs, filename):
    """Save with fit score first for easy sorting"""
    if not jobs:
        return
    
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['fit_score', 'title', 'company', 'location', 'role_category', 'role_pack',
                     'ats', 'keywords_matched', 'fit_reasons', 'url', 'date_found', 'status', 'snippet']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for job in jobs:
            row = {k: v for k, v in job.items() if k not in ['job_id', 'source_query']}
            writer.writerow(row)


def main():
    """Main execution"""
    print("=" * 60)
    print("AI/ML JOB SCRAPER - COMPLETE VERSION")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Searches: {len(SEARCHES)}")
    print("Features: Role packs, 10+ ATS, Fit scoring, Pagination")
    print("=" * 60)
    
    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        print("ERROR: Missing API keys")
        return
    
    seen_jobs = load_seen_jobs()
    all_new_jobs = []
    
    for idx, search_config in enumerate(SEARCHES, 1):
        pack = search_config.get('pack', 'General')
        print(f"\n[{idx}/{len(SEARCHES)}] [{pack}] {search_config['role']} - {search_config['ats']}")
        
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
                avg_score = sum(j['fit_score'] for j in new_jobs) / len(new_jobs)
                print(f"   Found {len(new_jobs)} jobs (avg fit: {avg_score:.0f})")
                all_new_jobs.extend(new_jobs)
                seen_jobs.update([job['job_id'] for job in new_jobs])
            else:
                print(f"   No new jobs")
        
        time.sleep(DELAY_BETWEEN_SEARCHES)
    
    # Sort by fit score
    all_new_jobs.sort(key=lambda x: x['fit_score'], reverse=True)
    
    if all_new_jobs:
        save_to_csv(all_new_jobs, OUTPUT_FILE)
        save_seen_jobs(seen_jobs)
        
        print("\n" + "=" * 60)
        print(f"SUCCESS! Found {len(all_new_jobs)} jobs")
        print(f"Score range: {all_new_jobs[0]['fit_score']} to {all_new_jobs[-1]['fit_score']}")
        print(f"Saved to: {OUTPUT_FILE}")
        print("\nTop 3 matches:")
        for job in all_new_jobs[:3]:
            print(f"  [{job['fit_score']}] {job['company']}: {job['title'][:50]}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("No new jobs this run")
        print("=" * 60)


if __name__ == "__main__":
    main()
