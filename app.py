#!/usr/bin/env python3
"""
Morgan Job Search - Backend API
Uses Google AI Studio (Gemini) to optimize job descriptions
FREE: 1M tokens/minute, very generous limits
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
if os.path.exists('.env_prod'):
    load_dotenv('.env_prod')
else:
    load_dotenv('.env')

app = Flask(__name__, static_folder='.')
CORS(app)

# Initialize Google AI Studio (Gemini)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')  # Latest stable model
else:
    model = None


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/api/optimize', methods=['POST'])
def optimize_job_description():
    """
    Analyze job description using Google Gemini and extract:
    1. Key technical skills
    2. Suggested job titles to search
    3. Important keywords
    """

    if not model:
        return jsonify({
            'error': 'Google API key not configured. Set GOOGLE_API_KEY environment variable.'
        }), 500

    data = request.json
    job_description = data.get('jobDescription', '')

    if not job_description:
        return jsonify({'error': 'No job description provided'}), 400

    # Truncate if too long
    if len(job_description) > 10000:
        job_description = job_description[:10000]

    try:
        # Call Gemini
        prompt = f"""Analyze this job description and extract key information for job searching.

Job Description:
{job_description}

Please provide:
1. The 5-8 most important technical skills/keywords (e.g., "LLM", "PyTorch", "NLP", "Computer Vision")
2. 3-5 similar job titles someone should search for (e.g., "Machine Learning Engineer", "AI Engineer")

Format your response as valid JSON only:
{{
  "keywords": ["keyword1", "keyword2", ...],
  "suggestedTitles": ["title1", "title2", ...]
}}

Return ONLY valid JSON, no markdown, no explanation."""

        response = model.generate_content(prompt)
        response_text = response.text

        # Parse JSON response
        import json

        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()

        result = json.loads(response_text)

        # Validate response
        if 'keywords' not in result or 'suggestedTitles' not in result:
            raise ValueError("Invalid response format from AI")

        # Ensure arrays
        if not isinstance(result['keywords'], list):
            result['keywords'] = []
        if not isinstance(result['suggestedTitles'], list):
            result['suggestedTitles'] = []

        return jsonify(result)

    except Exception as e:
        print(f"Error: {e}")
        # Return fallback response
        return jsonify({
            'keywords': ['Machine Learning', 'Python', 'AI', 'Deep Learning', 'Data Science'],
            'suggestedTitles': ['Machine Learning Engineer', 'AI Engineer', 'ML Engineer', 'Data Scientist']
        }), 200


if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5000)