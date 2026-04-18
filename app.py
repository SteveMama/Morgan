#!/usr/bin/env python3
"""
Minimal backend for the listings-style life sciences PM role page.
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS


app = Flask(__name__, static_folder=".")
CORS(app)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
