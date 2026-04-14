"""
WSGI entry point for PythonAnywhere.

PythonAnywhere looks for a variable named `application` in this file.

Setup steps (done once in the PythonAnywhere Web tab):
  Source code:      /home/<username>/health-agent
  Working dir:      /home/<username>/health-agent
  WSGI config file: (PythonAnywhere auto-generates this — replace its contents
                    with the single import line at the bottom of this file)
  Virtualenv:       /home/<username>/.virtualenvs/health-agent
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env variables
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Create the Flask app
from dashboard.app import create_app
application = create_app()
