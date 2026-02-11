#!/usr/bin/env python3
"""
Morgan Job Search - Backend API
Uses Groq (free) to optimize job descriptions
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
# Try .env_prod first (production), fallback to .env (local dev)
if os.path.exists('.env_prod'):
    load_dotenv('.env_prod')
else:
    load_dotenv('.env')

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize Groq client (free API)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/api/optimize', methods=['POST'])
def optimize_job_description():
    """
    Analyze job description and extract:
    1. Key technical skills
    2. Suggested job titles to search
    3. Important keywords
    """

    if not client:
        return jsonify({
            'error': 'Groq API key not configured. Set GROQ_API_KEY environment variable.'
        }), 500

    data = request.json
    job_description = data.get('jobDescription', '')

    if not job_description:
        return jsonify({'error': 'No job description provided'}), 400

    # Truncate if too long (Groq free tier limit)
    if len(job_description) > 8000:
        job_description = job_description[:8000]

    try:
        # Call Groq LLM
        prompt = f"""Analyze this job description and extract key information for job searching.

Job Description:
{job_description}

Please provide:
1. The 5-8 most important technical skills/keywords (e.g., "LLM", "PyTorch", "NLP", "Computer Vision")
2. 3-5 similar job titles someone should search for (e.g., "Machine Learning Engineer", "AI Engineer")

Format your response as JSON:
{{
  "keywords": ["keyword1", "keyword2", ...],
  "suggestedTitles": ["title1", "title2", ...]
}}

Only return valid JSON, no markdown formatting."""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Fast, free model
            messages=[
                {
                    "role": "system",
                    "content": "You are a job search expert who extracts keywords from job descriptions. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=500
        )

        response_text = completion.choices[0].message.content

        # Parse JSON response
        import json

        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)

        result = json.loads(response_text)

        # Validate response
        if 'keywords' not in result or 'suggestedTitles' not in result:
            raise ValueError("Invalid response format from LLM")

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': f'Error processing request: {str(e)}',
            # Fallback keywords
            'keywords': ['Machine Learning', 'Python', 'AI', 'Deep Learning'],
            'suggestedTitles': ['Machine Learning Engineer', 'AI Engineer', 'ML Engineer']
        }), 200  # Return 200 with fallback


if __name__ == '__main__':
    if not GROQ_API_KEY:
        print("WARNING: GROQ_API_KEY not set. Get free key from https://console.groq.com")
        print("Set it with: export GROQ_API_KEY='your_key_here'")

    app.run(debug=True, host='0.0.0.0', port=5000)