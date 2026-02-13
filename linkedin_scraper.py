import requests
from bs4 import BeautifulSoup
import time
import random
import re
import json
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timedelta

class LinkedInJobScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def search_jobs(self, keywords, location='United States', time_filter='r86400', max_results=25, fetch_details=True):
        """
        Search LinkedIn jobs using public job search
        
        Args:
            keywords: Job search keywords
            location: Location string
            time_filter: r86400 (24h), r172800 (48h), r604800 (week)
            max_results: Max jobs to return
            fetch_details: If True, fetch full job page for each result (slower but more data)
            
        Returns:
            List of job dictionaries with title, company, location, apply_link, description, etc.
        """
        
        base_url = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
        
        params = {
            'keywords': keywords,
            'location': location,
            'f_TPR': time_filter,
            'start': 0
        }
        
        jobs = []
        
        try:
            url = f"{base_url}?{urlencode(params)}"
            print(f"Fetching: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all job cards
            job_cards = soup.find_all('li')
            
            print(f"Found {len(job_cards)} job listings")
            
            for idx, card in enumerate(job_cards[:max_results]):
                job_data = self._extract_job_data(card)
                if job_data:
                    # Fetch full details if requested
                    if fetch_details and job_data.get('job_id'):
                        print(f"Fetching details for job {idx+1}/{min(len(job_cards), max_results)}: {job_data['title']}")
                        full_details = self._fetch_job_details(job_data['job_id'])
                        if full_details:
                            job_data.update(full_details)
                        time.sleep(random.uniform(1.5, 2.5))
                    
                    jobs.append(job_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Error: {e}")
            
        return jobs
    
    def _extract_job_data(self, card):
        """Extract basic job details from job card"""
        try:
            job = {}
            
            # Job link and ID
            link_elem = card.find('a', class_='base-card__full-link')
            if link_elem and link_elem.get('href'):
                job['link'] = link_elem['href']
                
                # Extract numeric job ID from URL
                # URLs look like: /jobs/view/1234567890 or /jobs/view/job-title-at-company-1234567890
                if '/view/' in job['link']:
                    view_part = job['link'].split('/view/')[-1].split('?')[0]
                    
                    # Extract numeric ID (last number in the string)
                    import re
                    numeric_ids = re.findall(r'\d+', view_part)
                    if numeric_ids:
                        # Take the last (longest) numeric sequence
                        job_id = numeric_ids[-1]
                        job['job_id'] = job_id
                        job['linkedin_url'] = f"https://www.linkedin.com/jobs/view/{job_id}"
                    else:
                        return None
                else:
                    return None
            else:
                return None
            
            # Job title
            title_elem = card.find('h3', class_='base-search-card__title')
            job['title'] = title_elem.text.strip() if title_elem else 'N/A'
            
            # Company name
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            if not company_elem:
                company_elem = card.find('a', class_='hidden-nested-link')
            job['company'] = company_elem.text.strip() if company_elem else 'N/A'
            
            # Location
            location_elem = card.find('span', class_='job-search-card__location')
            job['location'] = location_elem.text.strip() if location_elem else 'N/A'
            
            # Posted date
            date_elem = card.find('time', class_='job-search-card__listdate')
            if not date_elem:
                date_elem = card.find('time', {'datetime': True})
            
            if date_elem:
                job['posted_date'] = date_elem.get('datetime', date_elem.text.strip())
            else:
                job['posted_date'] = 'Recently'
            
            # Salary (rarely available in search results)
            salary_elem = card.find('span', class_='job-search-card__salary-info')
            job['salary'] = salary_elem.text.strip() if salary_elem else None
            
            # Only return if we have essential data
            if job.get('title') != 'N/A' and job.get('link'):
                return job
                
        except Exception as e:
            return None
            
        return None
    
    def _fetch_job_details(self, job_id):
        """
        Fetch full job page and extract detailed information including:
        - External apply link (company website)
        - Full job description
        - Employment type, seniority level
        - Exact posting date
        """
        try:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            
            print(f"  Fetching job details from: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            details = {}
            
            # Extract job description
            desc_elem = soup.find('div', class_='show-more-less-html__markup')
            if desc_elem:
                details['description'] = desc_elem.get_text(strip=True, separator='\n')
                print(f"  ✓ Found description ({len(details['description'])} chars)")
            
            # Extract apply link - look for external apply URL
            apply_link = None
            
            # Method 1: Look for apply button with external URL
            apply_button = soup.find('a', {'data-tracking-control-name': 'public_jobs_apply-link-offsite'})
            if apply_button and apply_button.get('href'):
                apply_link = apply_button['href']
                print(f"  ✓ Found external apply link: {apply_link[:60]}...")
            
            # Method 2: Look in the page source for applyUrl
            if not apply_link:
                # Try to find in script tags
                script_tags = soup.find_all('script', type='application/ld+json')
                for script in script_tags:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict) and 'directApply' in data:
                            if not data.get('directApply', True):
                                # Has external apply
                                apply_link = data.get('url', data.get('applicationUrl'))
                                if apply_link:
                                    print(f"  ✓ Found apply link in JSON-LD: {apply_link[:60]}...")
                    except:
                        pass
            
            # Method 3: Parse rehydration data
            if not apply_link:
                rehydrate_script = soup.find('script', id='rehydrate-data')
                if rehydrate_script and rehydrate_script.string:
                    try:
                        # Try to find applyUrl patterns in the data
                        matches = re.findall(r'"applyUrl":"([^"]+)"', rehydrate_script.string)
                        if matches:
                            apply_link = matches[0].replace('\\/', '/')
                            print(f"  ✓ Found apply link in rehydration data: {apply_link[:60]}...")
                    except:
                        pass
            
            if not apply_link:
                print(f"  ℹ No external apply link found, using LinkedIn Easy Apply")
            
            details['external_apply_url'] = apply_link
            details['apply_type'] = 'external' if apply_link else 'linkedin_easy_apply'
            
            # Extract job criteria (employment type, seniority, etc.)
            criteria_items = soup.find_all('li', class_='description__job-criteria-item')
            for item in criteria_items:
                label_elem = item.find('h3', class_='description__job-criteria-subheader')
                value_elem = item.find('span', class_='description__job-criteria-text')
                
                if label_elem and value_elem:
                    label = label_elem.text.strip().lower()
                    value = value_elem.text.strip()
                    
                    if 'seniority' in label:
                        details['seniority_level'] = value
                        print(f"  ✓ Seniority: {value}")
                    elif 'employment type' in label:
                        details['employment_type'] = value
                        print(f"  ✓ Employment type: {value}")
                    elif 'job function' in label:
                        details['job_function'] = value
                    elif 'industries' in label:
                        details['industries'] = value
            
            # Extract exact posted date
            posted_elem = soup.find('span', class_='posted-time-ago__text')
            if posted_elem:
                posted_text = posted_elem.text.strip()
                details['posted_ago'] = posted_text
                details['posted_date_formatted'] = self._parse_posted_date(posted_text)
                print(f"  ✓ Posted: {posted_text}")
            
            return details
            
        except requests.exceptions.HTTPError as e:
            print(f"  ✗ HTTP Error: {e.response.status_code} - {e}")
            return None
        except Exception as e:
            print(f"  ✗ Error fetching job details: {e}")
            return None
    
    def _parse_posted_date(self, posted_text):
        """Convert 'Posted 2 days ago' to actual date"""
        try:
            now = datetime.now()
            posted_lower = posted_text.lower()
            
            if 'just now' in posted_lower or 'moments ago' in posted_lower:
                return now.strftime('%Y-%m-%d')
            
            # Extract number
            numbers = re.findall(r'\d+', posted_text)
            if not numbers:
                return posted_text
            
            num = int(numbers[0])
            
            if 'hour' in posted_lower:
                date = now - timedelta(hours=num)
            elif 'day' in posted_lower:
                date = now - timedelta(days=num)
            elif 'week' in posted_lower:
                date = now - timedelta(weeks=num)
            elif 'month' in posted_lower:
                date = now - timedelta(days=num*30)
            else:
                return posted_text
            
            return date.strftime('%Y-%m-%d')
        except:
            return posted_text


if __name__ == "__main__":
    scraper = LinkedInJobScraper()
    
    print("Testing Enhanced LinkedIn Job Scraper")
    print("=" * 60)
    
    # Test with fetch_details=True to get full job information
    jobs = scraper.search_jobs(
        keywords="Machine Learning Engineer",
        location="San Francisco",
        time_filter="r86400",
        max_results=5,  # Reduced for testing since we're fetching full pages
        fetch_details=True  # Enable full detail fetching
    )
    
    print(f"\nFound {len(jobs)} jobs with full details\n")
    
    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Posted: {job.get('posted_ago', job.get('posted_date', 'N/A'))}")
        print(f"   Posted Date: {job.get('posted_date_formatted', 'N/A')}")
        
        if job.get('external_apply_url'):
            print(f"   External Apply: {job['external_apply_url']}")
        else:
            print(f"   Apply: {job.get('linkedin_url', 'N/A')} (LinkedIn Easy Apply)")
        
        if job.get('employment_type'):
            print(f"   Type: {job['employment_type']}")
        if job.get('seniority_level'):
            print(f"   Level: {job['seniority_level']}")
        
        if job.get('description'):
            desc_preview = job['description'][:200] + '...'
            print(f"   Description: {desc_preview}")
        
        print()

