#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import google.generativeai as genai

if os.path.exists('.env_prod'):
    load_dotenv('.env_prod')
    print("✓ Loaded .env_prod")
else:
    load_dotenv('.env')

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found!")
    exit(1)

print(f"✓ API Key: {GOOGLE_API_KEY[:10]}...{GOOGLE_API_KEY[-10:]}")

try:
    genai.configure(api_key=GOOGLE_API_KEY)

    print("\nTesting gemini-2.5-flash (latest stable)...")
    model = genai.GenerativeModel('gemini-2.5-flash')

    response = model.generate_content("Say 'Hello from Gemini 2.5!' in one sentence.")
    print(f"✓ Response: {response.text}")

    print("\n" + "=" * 60)
    print("SUCCESS! Google AI Studio is working.")
    print("=" * 60)
    print("\nModel: gemini-2.5-flash")
    print("Free tier: 1,500 requests/day")
    print("\nRun: python app.py")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)