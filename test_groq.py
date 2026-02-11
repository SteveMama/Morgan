#!/usr/bin/env python3
"""
Test Groq API key and app functionality
"""

import os
from dotenv import load_dotenv
from groq import Groq

# Load .env_prod
if os.path.exists('.env_prod'):
    load_dotenv('.env_prod')
    print("✓ Loaded .env_prod")
else:
    load_dotenv('.env')
    print("✓ Loaded .env")

# Get API key
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY not found!")
    print("Check .env_prod file exists and contains the key")
    exit(1)

print(f"✓ API Key found: {GROQ_API_KEY[:10]}...{GROQ_API_KEY[-10:]}")

# Test Groq API
try:
    client = Groq(api_key=GROQ_API_KEY)

    print("\nTesting Groq API...")

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": "Say 'Hello from Groq!' in one short sentence."
            }
        ],
        temperature=0.5,
        max_tokens=50
    )

    response = completion.choices[0].message.content
    print(f"✓ Groq API Response: {response}")

    print("\n" + "=" * 50)
    print("SUCCESS! Groq API is working correctly.")
    print("=" * 50)
    print("\nYou can now run: python app.py")

except Exception as e:
    print(f"\n❌ Error testing Groq API: {e}")
    print("\nPossible issues:")
    print("1. Invalid API key")
    print("2. Network connectivity")
    print("3. Groq service down")
    exit(1)