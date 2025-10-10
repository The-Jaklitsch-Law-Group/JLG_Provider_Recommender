# S3 Data Source Migration Guide

## Overview

As of this release, the JLG Provider Recommender app uses **AWS S3 exclusively** as the canonical data source. Local parquet files that were previously checked into the repository have been deprecated and removed.

## What Changed

### Before (Deprecated)
- Local parquet files in `data/processed/` were checked into git
- App prioritized local files over S3
- Repository size bloated with data files (~100KB+)
- Confusion about which data source was authoritative

### After (Current)
- **S3 is the only authoritative data source**
- Local parquet files in `data/processed/` are cache files auto-generated from S3
- Parquet files are gitignored and not checked into repository
- App automatically downloads latest data from S3 on launch
- Clear error messages if S3 is not configured

## Configuration

### Required S3 Setup

Create or update `.streamlit/secrets.toml`:

```toml
[s3]
aws_access_key_id = "your-access-key-id"
aws_secret_access_key = "your-secret-access-key"
bucket_name = "your-bucket-name"
region_name = "us-east-1"

# Folder/prefix configuration
referrals_folder = "referrals"
preferred_providers_folder = "preferred_providers"
```

### S3 Bucket Structure

Your S3 bucket should contain:

```
your-bucket/
├── referrals/
│   ├── Referrals_App_Full_Contacts_2024-01-15.csv
│   ├── Referrals_App_Full_Contacts_2024-02-10.csv
│   └── Referrals_App_Full_Contacts_2024-03-01.csv  (latest)
└── preferred_providers/
    ├── Preferred_Providers_2024-01-15.csv
    └── Preferred_Providers_2024-03-01.csv  (latest)
```

The app will automatically use the **most recent file** based on timestamp in the filename or S3 LastModified date.

## Migration Steps

### For Production/Staging Environments

1. **Ensure S3 credentials are configured** in your hosting platform's secrets/environment
2. **Upload latest data files to S3** if not already present
3. **Deploy the updated app** - it will auto-download on launch
4. **Verify data loaded correctly** in the Data Dashboard page

### For Local Development

1. Create `.streamlit/secrets.toml` with your S3 credentials (see template above)
2. Run the app: `streamlit run app.py`
3. Data will auto-download from S3 on first launch

## Deployment Checklist

- [ ] S3 bucket created and accessible
- [ ] Latest referral data uploaded to S3
- [ ] S3 credentials configured in secrets/environment
- [ ] App deployed and auto-update verified
- [ ] Smoke test: Search page returns results
- [ ] Data Dashboard shows expected record counts

## Troubleshooting

### Error: "S3 is not configured"

**Cause:** S3 credentials are missing or invalid.

**Fix:**
1. Check `.streamlit/secrets.toml` has all required S3 fields
2. Verify credentials are correct (test with AWS CLI: `aws s3 ls s3://your-bucket/`)
3. Ensure IAM user has `s3:GetObject` and `s3:ListBucket` permissions

### Error: "No data file found for [source]"

**Cause:** S3 auto-update failed or bucket is empty.

**Fix:**
1. Navigate to **🔄 Update Data** page
2. Click "Refresh Both Files" to manually trigger download from S3
3. Check S3 bucket contains files in the correct folders
4. Verify folder names match config: `referrals_folder` and `preferred_providers_folder`

### App runs but no providers returned

**Cause:** Data was downloaded but processing failed.

**Fix:**
1. Check logs for processing errors
2. Verify CSV/Excel format matches expected schema
3. Try re-uploading a known-good file to S3

## File Naming Conventions

For S3 files to be auto-detected correctly:

- **Referrals:** `Referrals_App_Full_Contacts*.csv` or `*.xlsx`
- **Providers:** `Preferred_Providers*.csv` or `*.xlsx` or `Referral_App_Preferred_Providers*.csv`
- Include date in filename for version tracking: `YYYY-MM-DD` format recommended

Example:
- `Referrals_App_Full_Contacts_2024-03-15.csv`
- `Preferred_Providers_2024-03-15.csv`

## Benefits of S3-Only Mode

1. **Single Source of Truth:** S3 is the authoritative data source
2. **Smaller Repository:** No large data files checked into git
3. **Better Security:** Sensitive data not in version control
4. **Simplified Deployment:** All environments use same S3 source
5. **Automatic Updates:** App auto-downloads latest data on launch
6. **Version History:** S3 object versioning tracks data changes

## Testing Without S3

For unit tests, use the `disable_s3_only_mode` pytest fixture:

```python
def test_my_feature(disable_s3_only_mode):
    # Test runs without S3 requirement
    # Can use local fixtures or temp files
    pass
```

See `tests/conftest.py` and `tests/fixtures/` for examples.

## Support

For questions or issues:
- Check S3 bucket permissions and credentials
- Review app logs for specific error messages
- Contact Data Operations team for S3 access issues
- See `docs/API_SECRETS_GUIDE.md` for detailed configuration help
