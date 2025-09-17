"""Pytest configuration helpers.

Ensure the project root is on sys.path so tests can import the `src` package
when pytest is invoked from the repository root or an isolated test runner.
"""
import sys
from pathlib import Path


def pytest_configure():
    # Insert the repository root (parent of the tests directory) at the front
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
