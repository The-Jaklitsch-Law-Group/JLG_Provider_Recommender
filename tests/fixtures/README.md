# Test Fixtures

This directory contains small sample data files used for unit testing.

These fixtures are tiny, representative samples (not real data) used to test the data pipeline without relying on large local parquet files or S3 access.

## Files

- `sample_referrals.parquet` - Minimal sample referral data for testing ingestion
- `sample_providers.parquet` - Minimal sample provider data for testing

## Usage

Tests should use these fixtures via the `conftest.py` fixtures or by directly loading them when needed.

Example:
```python
import pandas as pd
from pathlib import Path

fixtures_dir = Path(__file__).parent / "fixtures"
df = pd.read_parquet(fixtures_dir / "sample_referrals.parquet")
```

## Note on S3-Only Mode

With S3-only mode enabled, the app no longer relies on local parquet files in `data/processed/`.
These test fixtures are only for unit testing purposes and are kept minimal to avoid bloating the repository.
