from linkedin_scraper import LinkedInJobScraper

def test_scraper():
    print("=" * 60)
    print("TESTING LINKEDIN JOB SCRAPER")
    print("=" * 60)
    
    scraper = LinkedInJobScraper()
    
    # Test 1: AI/ML jobs
    print("\nTest 1: Machine Learning Engineer jobs")
    print("-" * 60)
    
    jobs = scraper.search_jobs(
        keywords="Machine Learning Engineer",
        location="San Francisco",
        time_filter="r86400",
        max_results=5
    )
    
    if jobs:
        print(f"SUCCESS: Found {len(jobs)} jobs\n")
        for idx, job in enumerate(jobs, 1):
            print(f"{idx}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Apply: {job['apply_link']}")
            if job.get('salary'):
                print(f"   Salary: {job['salary']}")
            print()
    else:
        print("FAILED: No jobs found")
        
    # Test 2: GMP jobs
    print("\nTest 2: QA Document Control jobs")
    print("-" * 60)
    
    jobs2 = scraper.search_jobs(
        keywords="QA Document Control Specialist",
        location="New Jersey",
        time_filter="r86400",
        max_results=5
    )
    
    if jobs2:
        print(f"SUCCESS: Found {len(jobs2)} jobs\n")
        for idx, job in enumerate(jobs2, 1):
            print(f"{idx}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Apply: {job['apply_link']}")
            print()
    else:
        print("FAILED: No jobs found")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_scraper()
