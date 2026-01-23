#!/usr/bin/env python3
"""
API Key Diagnostic Script
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
search_id = os.getenv('SEARCH_ENGINE_ID')

print("=" * 60)
print("API KEY DIAGNOSTIC TEST")
print("=" * 60)
print(f"\nAPI Key: {api_key[:20]}..." if api_key else "NOT FOUND")
print(f"Search Engine ID: {search_id}" if search_id else "NOT FOUND")
print("\nTesting API call...")

url = "https://www.googleapis.com/customsearch/v1"
params = {
    'key': api_key,
    'cx': search_id,
    'q': 'test',
    'num': 1
}

try:
    response = requests.get(url, params=params, timeout=10)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        print("\nSUCCESS! API is working correctly.")
        data = response.json()
        print(f"Total results: {data.get('searchInformation', {}).get('totalResults', 'N/A')}")
    
    elif response.status_code == 403:
        print("\nERROR: 403 Forbidden")
        print("\nFull error response:")
        print(response.text)
        print("\nPossible causes:")
        print("1. Custom Search API is not enabled")
        print("2. API key has restrictions")
        print("3. API key is invalid")
        print("4. Billing not enabled (sometimes required)")
    
    elif response.status_code == 429:
        print("\nERROR: 429 Rate Limit")
        print("You've exhausted your daily quota (100 searches/day)")
        print("Wait until tomorrow at 3 AM EST")
    
    else:
        print(f"\nUnexpected status: {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"\nException occurred: {e}")

print("\n" + "=" * 60)
