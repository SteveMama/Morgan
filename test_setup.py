#!/usr/bin/env python3
"""
Quick test to verify your setup is working
"""

import sys

def test_imports():
    """Test if all required packages are installed"""
    print("Testing Python packages...")
    
    try:
        import requests
        print("✅ requests installed")
    except ImportError:
        print("❌ requests NOT installed - run: pip install requests")
        return False
    
    try:
        import json
        print("✅ json installed (built-in)")
    except ImportError:
        print("❌ json NOT installed")
        return False
    
    try:
        import csv
        print("✅ csv installed (built-in)")
    except ImportError:
        print("❌ csv NOT installed")
        return False
    
    return True

def test_api_credentials():
    """Check if API credentials are set"""
    print("\nTesting API credentials...")
    
    from job_scraper import GOOGLE_API_KEY, SEARCH_ENGINE_ID
    
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        print(f"✅ Google API Key found: {GOOGLE_API_KEY[:10]}...")
    else:
        print("❌ Google API Key missing or invalid")
        return False
    
    if SEARCH_ENGINE_ID and len(SEARCH_ENGINE_ID) > 5:
        print(f"✅ Search Engine ID found: {SEARCH_ENGINE_ID}")
    else:
        print("❌ Search Engine ID missing or invalid")
        return False
    
    return True

def main():
    print("=" * 60)
    print("🧪 JOB SCRAPER SETUP TEST")
    print("=" * 60 + "\n")
    
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ Setup incomplete. Please install missing packages.")
        sys.exit(1)
    
    api_ok = test_api_credentials()
    
    if not api_ok:
        print("\n❌ API credentials not configured properly")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nYou're ready to run:")
    print("  python job_scraper.py")
    print("\n")

if __name__ == "__main__":
    main()
