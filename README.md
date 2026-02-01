# Morgan - AI/ML Job Scraper

Automated scraper that finds AI and Machine Learning engineering jobs posted in the last 24 hours using **Google Search** + **Selenium**.

## Evolution Summary

This project evolved through multiple iterations to solve API limitations and optimize job discovery:

1. **Google Custom Search API** → Shutdown for new users (Jan 2025)
2. **Brave Search API** → Rate limiting + small index
3. **Selenium + Google Search** → **CURRENT SOLUTION** 

## What It Does

Scrapes Google search results for entry-to-mid level AI/ML jobs across:
- **8 role categories**: LLM/GenAI, AI Engineer, ML Engineer, Research Scientist, NLP, Computer Vision, MLOps, Deep Learning
- **5 ATS platforms**: Ashby, Greenhouse, Lever, Workday, SmartRecruiters
- **Time filter**: Last 24 hours only
- **Location**: United States only
- **Deduplication**: Global across all searches

## Current Working Solution

**File:** `ai_ml_scraper_us_only.py`

**Key features:**
- Uses Brave browser via Selenium
- Searches Google with `after:YYYY-MM-DD` filter
- **20-second delays** between searches (randomized 18-22s)
- Incognito mode + WebDriver hiding
- Global deduplication across categories
- Filters senior roles (staff, principal, director, etc.)

## Quick Start

### 1. Install Dependencies

```bash
pip install selenium python-dotenv
brew install chromedriver
```

Allow chromedriver in System Settings → Privacy & Security (first run only)

### 2. Install Brave Browser

Download from: https://brave.com/

### 3. Configure

Create `.env` file:
```env
OUTPUT_DIR=ai_ml_jobs_output
HOURS_LOOKBACK=24
DELAY_BETWEEN_SEARCHES=20
MAX_RESULTS_PER_QUERY=20
```

### 4. Run

```bash
python ai_ml_scraper_us_only.py
```

**Runtime:** ~10-12 minutes (30 searches × 20 sec delays)

## Output Structure

Separate CSV files by role category:

```
ai_ml_jobs_output/
├── llm_genai_engineer_2026-01-31.csv
├── ai_engineer_2026-01-31.csv
├── ml_engineer_2026-01-31.csv
├── research_scientist_2026-01-31.csv
├── nlp_engineer_2026-01-31.csv
├── computer_vision_2026-01-31.csv
├── mlops_infrastructure_2026-01-31.csv
└── deep_learning_2026-01-31.csv
```

**CSV columns:**
- title: Job title
- company: Extracted from URL
- url: Direct application link
- ats: Platform (Ashby, Greenhouse, etc.)
- date_found: Timestamp when scraped

## Search Coverage

### Role Categories (8)

1. **LLM/Generative AI Engineer** - LLM Engineer, GenAI Engineer, Foundation Model Engineer
2. **AI Engineer** - AI Engineer, Artificial Intelligence Engineer, Applied AI
3. **Machine Learning Engineer** - ML Engineer, Applied ML Engineer
4. **Research Scientist** - ML Scientist, Applied Scientist, AI Research Scientist
5. **NLP Engineer** - NLP Engineer, Natural Language Processing
6. **Computer Vision** - CV Engineer, Multimodal Engineer
7. **MLOps/Infrastructure** - MLOps, ML Platform, ML Infrastructure
8. **Deep Learning** - Deep Learning Engineer, Neural Networks

### ATS Platforms (5)

- **Ashby** - `jobs.ashbyhq.com` (YC companies, GenAI startups)
- **Greenhouse** - `boards.greenhouse.io` (Startups, unicorns)
- **Lever** - `jobs.lever.co` (Mid-size tech)
- **Workday** - `myworkdayjobs.com` (Big tech, finance)
- **SmartRecruiters** - `jobs.smartrecruiters.com` (Enterprises)

### Location Filter

All queries include: `("United States" OR "USA" OR "US")`

Filters out: Canada, UK, India, remote international roles

## Key Technical Improvements

### 1. Correct ATS Subdomains

**Critical discovery:** Most jobs are indexed under specific subdomains, not root domains.

**Fixed:**
```python
# Before (missed 40-60% of jobs)
site:ashbyhq.com
site:greenhouse.io
site:lever.co

# After (correct)
site:jobs.ashbyhq.com
site:boards.greenhouse.io
site:jobs.lever.co
```

### 2. Global Deduplication

**Problem:** Same job appearing in multiple category CSVs

**Solution:**
```python
seen_urls_global = set()  # Shared across all searches
```

### 3. Improved URL Normalization

**Removes:**
- `#:~:text=` anchors (Google text fragments)
- `?gh_src=` (Greenhouse tracking)
- `?utm_*` (marketing parameters)
- `?source=` (referral tracking)

**Result:** Better deduplication, cleaner URLs

### 4. Better Senior Role Filtering

**Excluded:**
- senior, sr., staff, principal
- director, head of, chief
- engineering manager, VP
- Level III, IV, V

**Kept:**
- associate, junior, entry level
- Level I, II
- "Lead" (can be IC role)

### 5. Anti-CAPTCHA Measures

**20-second randomized delays** (critical):
```python
delay = random.randint(18, 22)  # Human-like irregularity
```

**Incognito mode:**
```python
options.add_argument('--incognito')
```

**Hide WebDriver property:**
```python
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
})
```

## Evolution & Experiments

### Experiment 1: Google Custom Search API (FAILED)

**Result:** HTTP 403 "This project does not have access"

**Root cause:** Google shutdown API for new users (Jan 8-15, 2025)

**Evidence:** Reddit thread confirmed multiple users affected

**Attempts:**
- Enabled API in Google Cloud Console ✗
- Created multiple API keys ✗
- Enabled billing ✗
- Disabled/re-enabled API ✗

**Conclusion:** API permanently closed to new customers

### Experiment 2: Brave Search API (PARTIAL SUCCESS)

**API key:** 

**Issues discovered:**
- Rate limiting (HTTP 429) after 3-4 queries
- Freshness parameter broken (`freshness=pd` returned 0 results)
- Independent index smaller than Google (missed many jobs)

**Improvements made:**
- Fixed pagination (offset is result index, not page number)
- Relaxed US location filtering (3-tier system)
- Separator-tolerant keyword matching
- Enhanced scoring with negative hints
- Concurrent verification with ThreadPoolExecutor

**Conclusion:** Too limited for daily scraping needs

### Experiment 3: Selenium + Google Search (SUCCESS)

**Current solution:** Uses Brave browser to search Google directly

**Why it works:**
- Full access to Google's index
- No API rate limits
- Real browser = better anti-detection
- Can solve CAPTCHA manually if needed

**Timeline:**
- Initial version: 5-second delays → CAPTCHA frequent
- Updated version: 20-second delays → CAPTCHA rare 

## CAPTCHA Avoidance Strategy

### What Triggers CAPTCHA (Research Findings)

1. **Automation signals:** `navigator.webdriver = true`, headless mode
2. **Behavioral patterns:** < 3 sec between requests, no cookies
3. **IP reputation:** Flagged IP, too many requests per hour

### Our Mitigation (Layered Defense)

**Layer 1: Browser Configuration**
- Incognito mode (fresh session)
- Non-headless (visible browser)
- WebDriver property hidden
- Automation flags disabled

**Layer 2: Timing**
- 20-second delays (randomized 18-22s)
- 6-second wait after each search
- ~10 minutes total runtime

**Layer 3: Request Volume**
- 30 searches total
- 3 searches/minute average
- Well under Google's 100 searches/hour limit

**Success rate:** < 5% CAPTCHA encounters with this config

## Typical Workflow

**Morning routine:**
```bash
# 8:00 AM - Start scraper
python ai_ml_scraper_us_only.py

# 8:10 AM - Scraper finishes
# Review 8 CSV files in ai_ml_jobs_output/

# 8:15 AM - Apply to top matches
```

**Results:**
- 20-50 jobs found (varies by day)
- All posted in last 24 hours
- All US-based
- All entry-to-mid level
- Zero duplicates

## Troubleshooting

### CAPTCHA Appears

**Cause:** IP flagged or delays too short

**Immediate fix:** Solve manually in browser (10 seconds)

**Long-term fix:**
1. Increase `DELAY_BETWEEN_SEARCHES` to 25-30
2. Run only once per day
3. Restart router (new IP)

### No Results Found

**Cause:** `after:YYYY-MM-DD` filter too strict

**Fix:** Increase lookback period
```env
HOURS_LOOKBACK=48  # or 72
```

### "0 result containers" in Output

**Cause:** Google changed CSS selectors

**Fix:** Script has fallback from `div.tF2Cxc` to `div.g`

## Alternative Scrapers Included

### GMP/QA Jobs Scraper

**File:** `job_scraper_gmp_final_48h.py`

Searches for pharma/biotech QA roles:
- GMP QA Associate
- GMP Specialist  
- Document Control Specialist

Same architecture, different vertical.

## Performance Metrics

**Per Run:**
- Searches: 30
- Runtime: 10-12 minutes
- Jobs found: 20-50
- CAPTCHA rate: < 5%
- Duplicates removed: 5-10

## Requirements

**System:**
- Python 3.8+
- Brave browser
- ChromeDriver

**Python packages:**
```bash
pip install selenium python-dotenv
```

---

**Last updated:** January 31, 2026
**Version:** 3.4 (Selenium + 20-sec delays + incognito)
**Status:** Production-ready