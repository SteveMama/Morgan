#!/usr/bin/env python3
"""
GMP Job Scraper - DIAGNOSTIC VERSION
Takes screenshots and tries all possible selectors to debug extraction
"""

import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Configuration
SCREENSHOT_DIR = 'debug_screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def setup_brave_driver():
    """Setup Brave browser"""
    brave_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"

    options = Options()
    options.binary_location = brave_path
    options.add_argument('--start-maximized')

    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        print(f"Error: {e}")
        print("Run: brew install chromedriver")
        exit(1)


def test_google_selectors(driver, query):
    """Test different selectors to find Google results"""

    print(f"\n{'=' * 70}")
    print(f"TESTING QUERY: {query}")
    print(f"{'=' * 70}")

    # Navigate and search
    driver.get("https://www.google.com")
    time.sleep(2)

    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(query)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)  # Wait for results

    # Take screenshot
    timestamp = datetime.now().strftime('%H%M%S')
    screenshot_file = f"{SCREENSHOT_DIR}/google_results_{timestamp}.png"
    driver.save_screenshot(screenshot_file)
    print(f"\nScreenshot saved: {screenshot_file}")

    # Test different selectors
    selectors = [
        ('div.g', 'Standard Google result container'),
        ('div[data-sokoban-container]', 'Sokoban container'),
        ('div.Gx5Zad', 'Alternative container'),
        ('div#search div', 'All divs in search area'),
        ('div#rso div', 'RSO container divs'),
        ('div#search a', 'All links in search'),
        ('[data-ved]', 'Data-ved attribute'),
        ('div.yuRUbf', 'yuRUbf container'),
    ]

    print("\nTesting selectors:")
    print("-" * 70)

    for selector, description in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            count = len(elements)
            print(f"{selector:30s} → {count:3d} elements  ({description})")

            if count > 0 and count < 100:  # Show sample
                first_elem = elements[0]
                sample_text = first_elem.text[:80].replace('\n', ' ') if first_elem.text else "[no text]"
                print(f"  Sample: {sample_text}")

                # Try to find h3 and link in first element
                try:
                    h3 = first_elem.find_element(By.CSS_SELECTOR, 'h3')
                    print(f"  ✓ Has h3: {h3.text[:50]}")
                except:
                    print(f"  ✗ No h3 found")

                try:
                    a = first_elem.find_element(By.CSS_SELECTOR, 'a')
                    url = a.get_attribute('href')
                    print(f"  ✓ Has link: {url[:60]}")
                except:
                    print(f"  ✗ No link found")

                print()

        except Exception as e:
            print(f"{selector:30s} → ERROR: {str(e)[:40]}")

    # Check page source for common text
    print("\nPage source check:")
    print("-" * 70)
    page_source = driver.page_source

    checks = [
        ('div class="g"', 'Standard result class'),
        ('myworkdayjobs.com', 'Workday URLs present'),
        ('icims.com', 'iCIMS URLs present'),
        ('No results found', 'No results message'),
        ('did not match', 'No match message'),
    ]

    for text, description in checks:
        if text in page_source:
            print(f"✓ Found: {description}")
        else:
            print(f"✗ Missing: {description}")

    print("\n" + "=" * 70)
    print("Review the screenshot and selector results above")
    print("Update the script with the working selector")
    print("=" * 70)


def main():
    """Run diagnostics"""
    print("=" * 70)
    print("GOOGLE SEARCH EXTRACTION DIAGNOSTIC")
    print("=" * 70)

    driver = setup_brave_driver()
    print("Browser ready!")

    # Test queries
    test_queries = [
        'GMP QA Associate site:myworkdayjobs.com',
        'machine learning engineer site:jobs.ashbyhq.com',
    ]

    try:
        for query in test_queries:
            test_google_selectors(driver, query)
            time.sleep(3)

        input("\nPress Enter to close browser and exit...")

    finally:
        driver.quit()
        print("Done!")


if __name__ == "__main__":
    main()