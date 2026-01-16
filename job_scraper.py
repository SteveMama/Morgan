#!/usr/bin/env python3
"""
AI/ML Job Scraper - Tailored for Entry to Mid-Level Roles
Focused on: AI Engineer, ML Engineer, LLM Engineer, MLOps, Computer Vision
NO Senior/Staff/Principal roles
"""

import requests
import csv
import time
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from .env
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'ai_ml_jobs.csv')
SEEN_JOBS_FILE = os.getenv('SEEN_JOBS_FILE', 'seen_jobs.json')
DELAY_BETWEEN_SEARCHES = int(os.getenv('DELAY_BETWEEN_SEARCHES', 1))

# REFINED SEARCH QUERIES - Entry to Mid-Level Only
SEARCHES = [
    # ========================================
    # NYC - CORE ML/AI ROLES
    # ========================================

    {
        "query": '("AI Engineer" OR "Artificial Intelligence Engineer") ("New York" OR "NYC") site:ashbyhq.com -senior -staff -principal -lead',
        "location": "NYC",
        "role": "AI Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("Machine Learning Engineer" OR "ML Engineer") ("New York" OR "NYC") site:ashbyhq.com -senior -staff -principal',
        "location": "NYC",
        "role": "ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("AI Engineer") ("New York" OR "NYC") site:greenhouse.io -senior -staff -principal',
        "location": "NYC",
        "role": "AI Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("Machine Learning Engineer") ("New York" OR "NYC") site:greenhouse.io -senior -staff',
        "location": "NYC",
        "role": "ML Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("Applied AI Engineer" OR "Applied ML Engineer") ("New York" OR "NYC") site:lever.co',
        "location": "NYC",
        "role": "Applied AI/ML",
        "ats": "Lever"
    },

    # LLM/NLP/CV Roles
    {
        "query": '("LLM Engineer" OR "NLP Engineer") ("New York" OR "NYC") site:ashbyhq.com -senior -staff',
        "location": "NYC",
        "role": "LLM/NLP Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("Computer Vision Engineer" OR "CV Engineer") ("New York" OR "NYC") site:greenhouse.io -senior',
        "location": "NYC",
        "role": "CV Engineer",
        "ats": "Greenhouse"
    },

    # MLOps
    {
        "query": '("MLOps Engineer" OR "ML Infrastructure Engineer") ("New York" OR "NYC") site:lever.co -senior',
        "location": "NYC",
        "role": "MLOps Engineer",
        "ats": "Lever"
    },

    # Enterprise ATS
    {
        "query": '("AI Engineer" OR "ML Engineer") ("New York" OR "NYC") site:myworkdayjobs.com -senior -staff',
        "location": "NYC",
        "role": "AI/ML Engineer",
        "ats": "Workday"
    },
    {
        "query": '("Machine Learning Engineer") ("New York") site:smartrecruiters.com -senior',
        "location": "NYC",
        "role": "ML Engineer",
        "ats": "SmartRecruiters"
    },

    # ========================================
    # SF/BAY AREA - CORE ROLES
    # ========================================

    {
        "query": '("AI Engineer" OR "Applied AI Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com -senior -staff',
        "location": "SF/Bay Area",
        "role": "AI Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("Machine Learning Engineer" OR "ML Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com -senior',
        "location": "SF/Bay Area",
        "role": "ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("AI Engineer") ("San Francisco" OR "Palo Alto" OR "Mountain View") site:greenhouse.io -senior -staff',
        "location": "SF/Bay Area",
        "role": "AI Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("Machine Learning Engineer") ("San Francisco" OR "Sunnyvale") site:greenhouse.io -senior',
        "location": "SF/Bay Area",
        "role": "ML Engineer",
        "ats": "Greenhouse"
    },

    # LLM/Generative AI (Hot market in SF)
    {
        "query": '("LLM Engineer" OR "Generative AI Engineer" OR "Foundation Model Engineer") ("San Francisco" OR "Bay Area") site:ashbyhq.com -senior',
        "location": "SF/Bay Area",
        "role": "LLM Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("LLM Engineer") ("San Francisco" OR "Palo Alto") site:greenhouse.io -senior',
        "location": "SF/Bay Area",
        "role": "LLM Engineer",
        "ats": "Greenhouse"
    },

    # Computer Vision
    {
        "query": '("Computer Vision Engineer" OR "Deep Learning Engineer") ("San Francisco") site:greenhouse.io -senior',
        "location": "SF/Bay Area",
        "role": "CV/DL Engineer",
        "ats": "Greenhouse"
    },

    # MLOps
    {
        "query": '("MLOps Engineer" OR "ML Platform Engineer") ("San Francisco" OR "Mountain View") site:lever.co -senior',
        "location": "SF/Bay Area",
        "role": "MLOps Engineer",
        "ats": "Lever"
    },

    # Other ATS
    {
        "query": '("AI Engineer" OR "ML Engineer") ("San Francisco") site:lever.co -senior -staff',
        "location": "SF/Bay Area",
        "role": "AI/ML Engineer",
        "ats": "Lever"
    },
    {
        "query": '("Machine Learning Engineer") ("San Francisco") site:smartrecruiters.com -senior',
        "location": "SF/Bay Area",
        "role": "ML Engineer",
        "ats": "SmartRecruiters"
    },

    # ========================================
    # SEATTLE
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("Seattle") site:ashbyhq.com -senior -staff',
        "location": "Seattle",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("ML Engineer" OR "AI Engineer") ("Seattle") site:greenhouse.io -senior',
        "location": "Seattle",
        "role": "AI/ML Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("Applied Scientist") ("Seattle") site:myworkdayjobs.com -"senior applied scientist"',
        "location": "Seattle",
        "role": "Applied Scientist",
        "ats": "Workday"
    },
    {
        "query": '("LLM Engineer" OR "NLP Engineer") ("Seattle") site:greenhouse.io -senior',
        "location": "Seattle",
        "role": "LLM/NLP Engineer",
        "ats": "Greenhouse"
    },

    # ========================================
    # BOSTON (Close to you!)
    # ========================================

    {
        "query": '("AI Engineer" OR "Applied AI Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com -senior -staff',
        "location": "Boston",
        "role": "AI Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("Machine Learning Engineer" OR "ML Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com -senior',
        "location": "Boston",
        "role": "ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("Machine Learning Engineer") ("Boston" OR "Cambridge") site:greenhouse.io -senior',
        "location": "Boston",
        "role": "ML Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("Computer Vision Engineer" OR "Robotics Engineer") ("Boston" OR "Cambridge") site:ashbyhq.com -senior',
        "location": "Boston",
        "role": "CV/Robotics",
        "ats": "Ashby"
    },
    {
        "query": '("LLM Engineer" OR "NLP Engineer") ("Boston" OR "Cambridge") site:greenhouse.io -senior',
        "location": "Boston",
        "role": "LLM/NLP",
        "ats": "Greenhouse"
    },
    {
        "query": '("MLOps Engineer") ("Boston" OR "Cambridge") site:lever.co -senior',
        "location": "Boston",
        "role": "MLOps Engineer",
        "ats": "Lever"
    },

    # ========================================
    # REMOTE - HIGH PRIORITY
    # ========================================

    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("remote" OR "hybrid") site:ashbyhq.com -senior -staff',
        "location": "Remote",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("AI Engineer") ("United States" OR "remote") site:greenhouse.io -senior -staff',
        "location": "Remote",
        "role": "AI Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("Machine Learning Engineer") ("remote US" OR "remote USA") site:ashbyhq.com -senior',
        "location": "Remote",
        "role": "ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("LLM Engineer" OR "Applied AI Engineer") ("remote United States") site:ashbyhq.com -senior',
        "location": "Remote",
        "role": "LLM/Applied AI",
        "ats": "Ashby"
    },
    {
        "query": '("MLOps Engineer" OR "ML Infrastructure") ("remote US") site:lever.co -senior',
        "location": "Remote",
        "role": "MLOps",
        "ats": "Lever"
    },
    {
        "query": '("Computer Vision Engineer" OR "NLP Engineer") ("remote" OR "hybrid") site:greenhouse.io -senior',
        "location": "Remote",
        "role": "CV/NLP Engineer",
        "ats": "Greenhouse"
    },
    {
        "query": '("AI Engineer" OR "ML Engineer") ("work from home" OR "distributed") site:greenhouse.io -senior',
        "location": "Remote",
        "role": "AI/ML Engineer",
        "ats": "Greenhouse"
    },

    # ========================================
    # DIRECT COMPANY SEARCHES - TOP AI COMPANIES
    # ========================================

    {
        "query": 'site:openai.com/careers "engineer" -senior -staff -principal',
        "location": "Various",
        "role": "Engineer",
        "ats": "OpenAI Careers"
    },
    {
        "query": 'site:anthropic.com/careers "engineer" -senior -staff',
        "location": "Various",
        "role": "Engineer",
        "ats": "Anthropic Careers"
    },
    {
        "query": 'site:scale.ai/careers ("machine learning" OR "AI") -senior -staff',
        "location": "Various",
        "role": "ML/AI",
        "ats": "Scale AI Careers"
    },
    {
        "query": 'site:cohere.com/careers "engineer" -senior -staff',
        "location": "Various",
        "role": "Engineer",
        "ats": "Cohere Careers"
    },
    {
        "query": 'site:huggingface.co/careers ("machine learning" OR "engineer") -senior',
        "location": "Various",
        "role": "ML Engineer",
        "ats": "HuggingFace Careers"
    },
    {
        "query": 'site:adept.ai/careers -senior -staff',
        "location": "Various",
        "role": "Engineer",
        "ats": "Adept Careers"
    },

    # Big Tech (entry-level focused)
    {
        "query": 'site:nvidia.com/careers ("AI" OR "machine learning") -senior -staff -principal',
        "location": "Various",
        "role": "AI/ML",
        "ats": "NVIDIA Careers"
    },
    {
        "query": 'site:meta.com/careers ("AI engineer" OR "ML engineer") -"senior" -"staff"',
        "location": "Various",
        "role": "AI/ML Engineer",
        "ats": "Meta Careers"
    },
    {
        "query": 'site:google.com/careers "machine learning engineer" -senior -staff',
        "location": "Various",
        "role": "ML Engineer",
        "ats": "Google Careers"
    },
    {
        "query": 'site:amazon.jobs ("machine learning engineer" OR "applied scientist") -"senior" -"principal"',
        "location": "Various",
        "role": "MLE/Applied Scientist",
        "ats": "Amazon Jobs"
    },

    # ========================================
    # ADDITIONAL MARKETS (Lower Priority)
    # ========================================

    # Texas
    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("Austin" OR "Dallas") site:ashbyhq.com -senior',
        "location": "Texas",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("ML Engineer") ("Austin") site:greenhouse.io -senior',
        "location": "Texas",
        "role": "ML Engineer",
        "ats": "Greenhouse"
    },

    # Los Angeles
    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("Los Angeles" OR "Santa Monica") site:ashbyhq.com -senior',
        "location": "Los Angeles",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
    {
        "query": '("Computer Vision Engineer") ("Los Angeles" OR "San Diego") site:greenhouse.io -senior',
        "location": "Los Angeles",
        "role": "CV Engineer",
        "ats": "Greenhouse"
    },

    # Washington DC
    {
        "query": '("AI Engineer" OR "Machine Learning Engineer") ("Washington DC" OR "Arlington") site:ashbyhq.com -senior',
        "location": "DC/DMV",
        "role": "AI/ML Engineer",
        "ats": "Ashby"
    },
]


# ========================================
# FUNCTIONS
# ========================================

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


def search_google(query, api_key, search_engine_id, date_restrict='d1'):
    """Execute Google Custom Search API query"""
    base_url = "https://www.googleapis.com/customsearch/v1"

    params = {
        'key': api_key,
        'cx': search_engine_id,
        'q': query,
        'dateRestrict': date_restrict,
        'num': 10
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {str(e)[:100]}")
        return None


def extract_company_name(url, title):
    """Extract company name from URL or title"""
    if 'ashbyhq.com' in url:
        parts = url.split('/')
        for i, part in enumerate(parts):
            if part == 'jobs.ashbyhq.com' and i + 1 < len(parts):
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

    # Extract from specific company sites
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
        'adept.ai': 'Adept'
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
        job = {
            'title': item.get('title', 'No Title'),
            'company': extract_company_name(item.get('link', ''), item.get('title', '')),
            'url': item.get('link', ''),
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
        print("⚠️  No new jobs to save")
        return

    file_exists = os.path.exists(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['title', 'company', 'location', 'role_category', 'ats', 'url', 'date_found', 'status', 'snippet']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for job in jobs:
            writer.writerow(job)

    print(f"✅ Saved {len(jobs)} jobs to {filename}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("🚀 AI/ML JOB SCRAPER - ENTRY TO MID-LEVEL FOCUSED")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total Searches: {len(SEARCHES)}")
    print("🎯 Target: Entry to Mid-Level AI/ML Roles")
    print("=" * 60)

    # Verify API keys are loaded
    if not GOOGLE_API_KEY or not SEARCH_ENGINE_ID:
        print("❌ ERROR: Missing API keys!")
        print("Please ensure .env file exists with GOOGLE_API_KEY and SEARCH_ENGINE_ID")
        return

    seen_jobs = load_seen_jobs()
    all_new_jobs = []

    total_searches = len(SEARCHES)

    for idx, search_config in enumerate(SEARCHES, 1):
        print(
            f"\n[{idx}/{total_searches}] Searching: {search_config['role']} in {search_config['location']} ({search_config['ats']})")

        results = search_google(
            query=search_config['query'],
            api_key=GOOGLE_API_KEY,
            search_engine_id=SEARCH_ENGINE_ID
        )

        if results:
            jobs = parse_job_results(results, search_config)

            new_jobs = [job for job in jobs if job['url'] not in seen_jobs]

            if new_jobs:
                print(f"   ✨ Found {len(new_jobs)} new jobs")
                all_new_jobs.extend(new_jobs)
                seen_jobs.update([job['url'] for job in new_jobs])
            else:
                print(f"   ℹ️  No new jobs (found {len(jobs)} already seen)")
        else:
            print(f"   ❌ Search failed")

        if idx < total_searches:
            time.sleep(DELAY_BETWEEN_SEARCHES)

    if all_new_jobs:
        save_to_csv(all_new_jobs, OUTPUT_FILE)
        save_seen_jobs(seen_jobs)

        print("\n" + "=" * 60)
        print(f"🎉 DONE! Found {len(all_new_jobs)} NEW jobs")
        print(f"📊 Total unique jobs tracked: {len(seen_jobs)}")
        print(f"📁 Results saved to: {OUTPUT_FILE}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("ℹ️  No new jobs found in this run")
        print(f"📊 Total unique jobs tracked: {len(seen_jobs)}")
        print("=" * 60)


if __name__ == "__main__":
    main()