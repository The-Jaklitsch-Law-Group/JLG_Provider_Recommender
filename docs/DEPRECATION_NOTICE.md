# Deprecation Notice: Local Parquet Files

**Effective Date:** [Current Release]  
**Status:** ✅ Completed  
**Impact:** Breaking change for environments not using S3

## Summary

Local parquet files in `data/processed/` have been **removed from version control** and are now **deprecated**. The app now requires AWS S3 configuration to load data.

## What Was Deprecated

- ❌ Local parquet files checked into git (`data/processed/*.parquet`)
- ❌ File-based data loading priority (parquet → raw Excel)
- ❌ Assumption that data files exist in the repository

## What Replaced It

- ✅ **S3 as the single source of truth**
- ✅ Automatic data download from S3 on app launch
- ✅ Local parquet files as cache files only (gitignored)
- ✅ Clear error messages when S3 is not configured
- ✅ `use_s3_only` and `allow_local_fallback` configuration flags

## Migration Timeline

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1: S3 Implementation** | ✅ Complete (Prior Release) | S3 client and auto-update implemented |
| **Phase 2: S3-Only Enforcement** | ✅ Complete (This Release) | Local parquet files removed, S3 required by default |
| **Phase 3: Fallback Removal** | 🔜 Planned (Next Release) | `allow_local_fallback` flag will be removed entirely |

## Current Configuration

### Default Behavior (S3-Only Mode)

```toml
[s3]
use_s3_only = true  # Enforces S3 requirement
allow_local_fallback = false  # No fallback to local files
```

The app will:
1. Check for S3 configuration on startup
2. Auto-download latest data from S3
3. Cache to `data/processed/` (gitignored)
4. Show clear error if S3 not configured

### Temporary Fallback (Deprecated - Will Be Removed)

For local development without S3:

```toml
[s3]
use_s3_only = false
allow_local_fallback = true
```

**⚠️ WARNING:** This fallback will be removed in the next release. Plan to configure S3 for local development.

## Action Required

### For Production/Staging
✅ **No action required** - S3 should already be configured

### For Local Development
Choose one:

**Option A: Configure S3 (Recommended)**
- Create `.streamlit/secrets.toml` with S3 credentials
- See `docs/S3_MIGRATION_GUIDE.md` for setup instructions

**Option B: Use Temporary Fallback (Not Recommended)**
- Set `allow_local_fallback = true` in secrets
- Manually upload data via the Update Data page
- Plan to migrate to S3 before next release

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
    # S3-only mode disabled for this test
    # Can use local fixtures or temp files
    pass
```

### For Integration Tests

Either:
- Mock S3 using `moto` library
- Use `disable_s3_only_mode` fixture
- Use small fixtures from `tests/fixtures/`

See `tests/conftest.py` for fixture implementation.

## Rollback Instructions

If you encounter issues and need to rollback:

1. **Immediate:** Set in `.streamlit/secrets.toml`:
   ```toml
   [s3]
   allow_local_fallback = true
   ```

2. **Create local cache:** Navigate to Update Data page and upload files manually

3. **Investigate:** Check S3 configuration and permissions

4. **Fix and Re-enable:** Once S3 is working, set back to:
   ```toml
   [s3]
   allow_local_fallback = false
   ```

## Future Removal Schedule

The `allow_local_fallback` flag will be **completely removed** in the **next major release**.

After removal:
- S3 will be strictly required
- No fallback option available
- All environments must have S3 configured

**Timeline:** 1-2 release cycles (plan accordingly)

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

**Last Updated:** [Current Date]  
**Applies To:** Version 2.0+ of JLG Provider Recommender
