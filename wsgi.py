"""
wsgi.py - WSGI entry point for LexGuard backend deployment on Render.

Adds the project root to sys.path so that the backend package can be
imported correctly by gunicorn regardless of the working directory.
"""

import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
