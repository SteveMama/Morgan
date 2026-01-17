#!/usr/bin/env python3
"""
Debug version - See what Selenium is actually seeing
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def setup_driver():
    """Setup Chrome with visible window"""
    chrome_options = Options()
    # DON'T run headless so we can see what's happening
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def test_search():
    """Test a single search and see what we get"""
    driver = setup_driver()

    query = '("AI Engineer") ("New York") site:ashbyhq.com'
    search_url = f"https://www.google.com/search?q={query}&tbs=qdr:d"

    print(f"Opening: {search_url}\n")
    driver.get(search_url)

    print("Waiting 5 seconds for page to load...")
    time.sleep(5)

    # Save screenshot
    driver.save_screenshot("google_search_debug.png")
    print("Screenshot saved to: google_search_debug.png")

    # Try different selectors
    print("\n--- Testing different CSS selectors ---")

    selectors = [
        ("div.g a", "Standard search result links"),
        ("a[href]", "All links"),
        ("#search a", "Links in search div"),
        ("div[data-sokoban-container] a", "New Google structure"),
        ("div.yuRUbf a", "Search result title links"),
    ]

    for selector, description in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"\n{description} ({selector}):")
            print(f"  Found {len(elements)} elements")

            if len(elements) > 0:
                for i, elem in enumerate(elements[:5]):  # Show first 5
                    try:
                        href = elem.get_attribute('href')
                        if href and 'google.com' not in href:
                            print(f"  [{i + 1}] {href[:80]}")
                    except:
                        pass
        except Exception as e:
            print(f"  Error: {e}")

    # Get page source
    print("\n--- Page HTML (first 1000 chars) ---")
    print(driver.page_source[:1000])

    print("\n--- Page Title ---")
    print(driver.title)

    input("\nPress Enter to close browser...")
    driver.quit()


if __name__ == "__main__":
    test_search()