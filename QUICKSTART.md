# QUICK START — Run This Now

**Get your first batch of jobs in under 2 minutes.**

---

## Step 1: Download These Files

You already have:
- ✅ `config.py` (your API keys are configured)
- ✅ `job_scraper.py` (the main script)
- ✅ `requirements.txt` (dependencies)

---

## Step 2: Install Dependencies (30 seconds)

Open terminal/command prompt and run:

```bash
pip install requests
```

That's it. Just one package.

---

## Step 3: Run the Scraper (1 minute)

```bash
python job_scraper.py
```

**What you'll see:**

```
======================================================================
🚀 AI/ML JOB SCRAPER - STARTING
======================================================================
📅 Date: 2026-01-16 09:30:00
🔍 Running 35 searches...
📊 Found 0 existing jobs in database

[1/35] Searching: Ashby - NYC
  ✅ NEW: Anthropic - AI Engineer
  ✅ NEW: Scale AI - Machine Learning Engineer
  
[2/35] Searching: Greenhouse - NYC
  ✅ NEW: Cohere - Applied ML Engineer
  
...

======================================================================
📈 SEARCH COMPLETE
   Total results: 127
   New jobs found: 43
   Duplicates skipped: 0
======================================================================

✅ Saved 43 new jobs to jobs.csv

✨ SUCCESS! Open 'jobs.csv' to see your jobs.
```

---

## Step 4: Open Your Results

**Mac:**
```bash
open jobs.csv
```

**Windows:**
```bash
start jobs.csv
```

**Linux:**
```bash
xdg-open jobs.csv
```

---

## What You'll See in jobs.csv

| job_title | company | location | ats_platform | apply_link | date_found | status |
|-----------|---------|----------|--------------|------------|------------|--------|
| AI Engineer | Anthropic | SF | Greenhouse | https://boards.greenhouse.io/... | 2026-01-16 09:30 | Not Applied |
| ML Engineer | Scale AI | SF | Ashby | https://jobs.ashbyhq.com/... | 2026-01-16 09:31 | Not Applied |

**Click the apply_link → apply immediately.**

---

## Next Steps

### Run it daily:

**Manual (recommended for first week):**
```bash
# Run every morning at 6 AM
python job_scraper.py
```

**Automated (after first week):**
- See `AUTOMATION.md` for GitHub Actions setup (free, cloud-based)
- Or set up a cron job (Mac/Linux) or Task Scheduler (Windows)

---

## Pro Tips for First Run

1. **Check API usage**: You have 100 searches/day on the free tier
   - This script uses ~35 searches per run
   - You can run it 2-3 times per day safely

2. **Best times to run**:
   - 6 AM EST — catches jobs posted overnight
   - 6 PM EST — catches jobs posted during the day

3. **Apply FAST**:
   - Jobs with <20 applicants get reviewed
   - Jobs with 100+ applicants go to the black hole
   - Speed matters more than perfection

4. **Update the status column**:
   - Change "Not Applied" to "Applied" after you apply
   - Helps you track what you've done

5. **Filter by company/location**:
   - Open CSV in Excel/Google Sheets
   - Use filters to focus on specific companies or locations

---

## Troubleshooting

### "No module named 'requests'"
```bash
pip install requests
```

### "API quota exceeded"
- You've run the script too many times today
- Wait until tomorrow (quota resets at midnight PST)
- Or create a new Google Cloud project with fresh API key

### "No jobs found"
- Google may not have indexed new jobs yet
- Try running later in the day (after 9 AM or after 5 PM)
- Jobs posted overnight are usually indexed by 9 AM

### CSV won't open
- Make sure you have Excel, Google Sheets, or a CSV viewer installed
- Try: `cat jobs.csv` to view in terminal

---

## What Happens on Subsequent Runs

The script is **smart about duplicates**:

**First run** (today):
- Finds 43 jobs
- Saves them all to `jobs.csv`

**Second run** (tomorrow):
- Finds 50 jobs
- 7 are new, 43 are duplicates
- Only adds the 7 new jobs
- Your CSV now has 50 jobs total

**Third run** (day after):
- Finds 55 jobs
- 5 are new
- Your CSV now has 55 jobs total

**You never see the same job twice.**

---

## Ready?

```bash
python job_scraper.py
```

**Then open `jobs.csv` and start applying. 🚀**

---

## Questions?

- Read `README.md` for detailed docs
- Read `AUTOMATION.md` for scheduling setup
- Check `config.py` to customize your searches

**Good luck with your job search!**
