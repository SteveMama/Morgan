# Morgan

Automated scraper that finds AI and Machine Learning engineering jobs posted in the last 24 hours.

## What It Does

Searches major ATS platforms (Ashby, Greenhouse, Lever, Workday) for entry-to-mid level AI/ML engineering positions. Filters out senior roles, scores jobs based on your resume keywords, and outputs a ranked CSV of the best matches.

## Quick Start

```bash
pip install -r requirements.txt
python job_scraper_brave.py
```

## Configuration

Edit `.env`:

```
BRAVE_API_KEY=your_key_here
FRESHNESS=pd
```

Freshness options:
- pd = past day (24 hours)
- pw = past week
- pm = past month

## Output

Two CSV files:
- `ai_ml_jobs.csv` - All jobs found
- `ai_ml_jobs_top10_today.csv` - Top 10 best matches

## Features

- Searches 11 major tech hubs and remote positions
- Filters jobs posted in last 24 hours
- Removes senior/staff/principal roles
- Scores jobs based on LLM, computer vision, and MLOps keywords
- Deduplicates results
- Fast: runs in under 30 seconds

## Search Coverage

Locations: NYC, SF/Bay Area, Boston, Seattle, Austin, Remote US

ATS Platforms: Ashby, Greenhouse, Lever, Workday

Role Types: AI Engineer, ML Engineer, LLM Engineer, Applied Scientist

## Requirements

- Python 3.8+
- Brave Search API key (free tier: 100 searches/day)
- Libraries: requests, beautifulsoup4, python-dotenv

## Typical Usage

Run once per day to catch new postings. Check the top 10 CSV for quick review before applying.