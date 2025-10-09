"""Pytest configuration helpers.

Ensure the project root is on sys.path so tests can import the `src` package
when pytest is invoked from the repository root or an isolated test runner.
"""
import sys
from pathlib import Path
import pytest


def pytest_configure():
    # Insert the repository root (parent of the tests directory) at the front
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))


@pytest.fixture
def disable_s3_only_mode(monkeypatch):
    """
    Fixture to disable S3-only mode for tests that use local files.
    
    This allows tests to run without S3 configuration by enabling the local fallback.
    Use this fixture in tests that need to load data from local test fixtures.
    """
    # Mock the config to allow local fallback
    def mock_get_api_config(api_name):
        if api_name == 's3':
            return {
                'aws_access_key_id': '',
                'aws_secret_access_key': '',
                'bucket_name': '',
                'region_name': 'us-east-1',
                'referrals_folder': 'referrals',
                'preferred_providers_folder': 'preferred_providers',
                'use_latest_file': True,
                'use_s3_only': False,  # Disable S3-only mode for tests
                'allow_local_fallback': True,
            }
        return {}
    
    monkeypatch.setattr('src.utils.config.get_api_config', mock_get_api_config)


@pytest.fixture
def sample_fixtures_dir():
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"

