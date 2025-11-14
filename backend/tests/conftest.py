"""
Pytest configuration for MCP server tests.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Ensure test database is seeded
def pytest_sessionstart(session):
    """
    Called after the Session object has been created and before performing collection.
    """
    try:
        from backend.seed import seed_database

        print("\nChecking if database is seeded...")
        seed_database()
    except Exception as e:
        print(f"\nWarning: Could not seed database: {e}")
        print("Some tests may be skipped if test data is not available.")
