import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urlencode, quote_plus

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
        
    def search_jobs(self, keywords, location='United States', time_filter='r86400', max_results=25):
        """
        Search LinkedIn jobs using public job search
        
        Args:
            keywords: Job search keywords
            location: Location string
            time_filter: r86400 (24h), r172800 (48h), r604800 (week)
            max_results: Max jobs to return
            
        Returns:
            List of job dictionaries with title, company, location, apply_link
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
            
            # Find all job cards - LinkedIn uses <li> elements with class containing job-search-card
            job_cards = soup.find_all('li')
            
            print(f"Found {len(job_cards)} job listings")
            
            for card in job_cards[:max_results]:
                job_data = self._extract_job_data(card)
                if job_data:
                    jobs.append(job_data)
                    
            time.sleep(random.uniform(1, 2))
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Error: {e}")
            
        return jobs
    
    def _extract_job_data(self, card):
        """Extract job details from job card"""
        try:
            job = {}
            
            # Job link and ID
            link_elem = card.find('a', class_='base-card__full-link')
            if link_elem and link_elem.get('href'):
                job['link'] = link_elem['href']
                
                # Extract job ID from URL
                if '/view/' in job['link']:
                    job_id = job['link'].split('/view/')[-1].split('?')[0]
                    job['job_id'] = job_id
                    job['apply_link'] = f"https://www.linkedin.com/jobs/view/{job_id}"
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
            
            # Salary (rarely available)
            salary_elem = card.find('span', class_='job-search-card__salary-info')
            job['salary'] = salary_elem.text.strip() if salary_elem else None
            
            # Only return if we have essential data
            if job.get('title') != 'N/A' and job.get('link'):
                return job
                
        except Exception as e:
            return None
            
        return None


if __name__ == "__main__":
    scraper = LinkedInJobScraper()
    
    print("Testing LinkedIn Job Scraper")
    print("=" * 60)
    
    jobs = scraper.search_jobs(
        keywords="Machine Learning Engineer",
        location="San Francisco",
        time_filter="r86400",
        max_results=10
    )
    
    print(f"\nFound {len(jobs)} jobs\n")
    
    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Apply: {job['apply_link']}")
        print(f"   Posted: {job['posted_date']}")
        print()
