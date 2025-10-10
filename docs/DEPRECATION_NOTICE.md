# Deprecation Notice: Local Parquet Files - COMPLETE

**Effective Date:** Version 2.0+  
**Status:** ✅ **FULLY IMPLEMENTED** - S3 is now the only supported data source  
**Impact:** S3 configuration is required for all environments

## Summary

Local parquet files in `data/processed/` have been **removed from version control** and **all fallback mechanisms have been removed**. The app now **strictly requires** AWS S3 configuration to load data.

## What Was Deprecated and Removed

- ❌ Local parquet files checked into git (`data/processed/*.parquet`)
- ❌ File-based data loading priority (parquet → raw Excel)
- ❌ Assumption that data files exist in the repository
- ❌ `allow_local_fallback` configuration flag (removed)
- ❌ `use_s3_only` configuration flag (no longer needed - S3 is always required)
- ❌ All fallback logic in data ingestion code

## What Replaced It

- ✅ **S3 as the only supported data source**
- ✅ Automatic data download from S3 on app launch
- ✅ Local parquet files as cache files only (gitignored)
- ✅ Clear error messages when S3 is not configured

## Migration Timeline

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1: S3 Implementation** | ✅ Complete | S3 client and auto-update implemented |
| **Phase 2: S3-Only Enforcement** | ✅ Complete | Local parquet files removed, S3 required by default |
| **Phase 3: Fallback Removal** | ✅ **Complete (This Release)** | All fallback flags and logic removed |

## Current Configuration

### S3 Required (Only Option)

```toml
[s3]
aws_access_key_id = "your-access-key-id"
aws_secret_access_key = "your-secret-access-key"
bucket_name = "your-bucket-name"
region_name = "us-east-1"
referrals_folder = "referrals"
preferred_providers_folder = "preferred_providers"
```

The app will:
1. Check for S3 configuration on startup
2. Auto-download latest data from S3
3. Cache to `data/processed/` (gitignored)
4. Show clear error if S3 not configured

## Action Required

### For Production/Staging
✅ **No action required** - S3 should already be configured

### For Local Development

**Configure S3 (Required)**
- Create `.streamlit/secrets.toml` with S3 credentials
- See `docs/S3_MIGRATION_GUIDE.md` for setup instructions
- S3 is the only supported data source

## Breaking Changes

### What No Longer Works

❌ **Cloning repo and running without S3**
```bash
git clone ...
streamlit run app.py  # Will fail if S3 not configured
```

❌ **Relying on local parquet files in git**
```python
# These files no longer exist in the repository
data/processed/cleaned_all_referrals.parquet  # REMOVED
```

❌ **Direct file path to parquet files in code**
```python
# Will fail - files don't exist
pd.read_parquet("data/processed/cleaned_all_referrals.parquet")
```

### What Still Works

✅ **DataIngestionManager API (recommended)**
```python
from src.data.ingestion import DataIngestionManager, DataSource

manager = DataIngestionManager()
df = manager.load_data(DataSource.ALL_REFERRALS)  # Loads from cache (auto-populated from S3)
```

✅ **Manual file upload**
- Navigate to Update Data page
- Upload CSV/Excel via UI
- Data is processed and cached locally

✅ **S3 auto-download**
- App automatically downloads on launch
- No manual intervention required

## Testing Implications

### For Unit Tests

Use the `disable_s3_only_mode` fixture:

```python
def test_my_feature(disable_s3_only_mode):
    # S3 requirement disabled for this test
    # Can use local fixtures or temp files
    pass
```

### For Integration Tests

Either:
- Mock S3 using `moto` library
- Use `disable_s3_only_mode` fixture
- Use small fixtures from `tests/fixtures/`

See `tests/conftest.py` for fixture implementation.

## Support

For questions or assistance:

1. **S3 Setup Issues:** See `docs/S3_MIGRATION_GUIDE.md`
2. **Configuration Help:** See `docs/API_SECRETS_GUIDE.md`
3. **General Questions:** Contact Data Operations team

## Related Documentation

- [S3 Migration Guide](./S3_MIGRATION_GUIDE.md) - Complete setup instructions
- [Data Input Formats](./DATA_INPUT_FORMATS.md) - Supported file formats
- [README](../README.md) - Updated with S3 requirements

---

**Last Updated:** Version 2.1+  
**Applies To:** All versions 2.1+ of JLG Provider Recommender  
**Status:** S3 is now the only supported data source - no fallbacks available
