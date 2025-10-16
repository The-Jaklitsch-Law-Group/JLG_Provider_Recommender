# Data Ingestion Warnings Guide

This document explains the warning messages you may see during data ingestion and what they mean.

## Overview

The JLG Provider Recommender includes data quality validation to help detect issues with uploaded data files. Warnings are designed to alert you to potential problems while still allowing data processing to continue.

## Warning Types

### 1. Person ID Column Warnings (RESOLVED)

**Previous Behavior:**
```
primary_inbound missing columns: Referred From's Details: Person ID
secondary_inbound missing columns: Secondary Referred From's Details: Person ID
outbound missing columns: Dr/Facility Referred To's Details: Person ID
```

**Current Behavior:**
Person ID columns are now treated as **optional**. When Person ID is present in your data, it's used for more accurate deduplication. When it's absent, the system falls back to standard deduplication methods.

**What You Need to Know:**
- Person ID warnings no longer appear at the WARNING level
- Missing Person ID columns are logged at DEBUG level for troubleshooting
- Data processes correctly whether or not Person ID is present
- No action required from users

**Technical Details:**
- Person ID is used when available for deduplication: `df.drop_duplicates(subset="Person ID")`
- When Person ID is all NA, it's automatically dropped from the processed data
- Fallback deduplication uses other columns like normalized name and address

---

### 2. Preferred Providers File Size Warning

**Warning Message:**
```
WARNING: Preferred providers file contains 401 unique providers. 
This is unusually high. Please verify that the correct file was uploaded to the 
preferred_providers folder in S3. The preferred providers list should contain 
only the firm's preferred provider contacts, not all providers.
```

**What This Means:**
The system detected more than 100 unique providers in the preferred providers file. This is unusual because the preferred providers list should contain only a curated subset of providers that the firm prefers to work with.

**Why This Matters:**
If the wrong file was uploaded (e.g., the full provider database instead of just preferred providers), it will affect:
- Provider recommendations (preferred status is used in scoring)
- Dashboard metrics (preferred vs. non-preferred provider analysis)
- Search results (preferred providers may be highlighted or filtered)

**How to Fix:**
1. **Verify the file in S3:** Check the `preferred_providers` folder and confirm the file is the correct one
2. **Check file contents:** The file should have significantly fewer providers than your main referrals data
3. **Expected size:** Typically 10-100 preferred providers depending on your firm's relationships
4. **Re-upload if needed:** If wrong file was uploaded, upload the correct preferred providers list

**What Happens if You Ignore This:**
- Data will still process and the app will function
- All providers in the file will be marked as "preferred"
- Recommendations and analytics may not reflect true preferred status
- Warning appears only once per app session to avoid log spam

---

### 3. Preferred Provider Percentage Warning

**Warning Message:**
```
WARNING: 93.5% of providers are marked as preferred. 
This is unusually high and may indicate that the preferred providers file 
contains all providers instead of just the preferred ones. 
Please verify the preferred providers data source.
```

**What This Means:**
After merging the preferred providers list with the main provider database, more than 80% of providers are marked as preferred. This suggests the preferred providers file may contain too many providers.

**Why This Matters:**
- If most providers are "preferred", the preferred status becomes meaningless
- Recommendation scoring gives bonus points to preferred providers
- Dashboard analytics comparing preferred vs. non-preferred becomes less useful
- This usually indicates a data issue, not a business policy

**How to Fix:**
1. **Review your preferred providers file:** Should contain only providers the firm actively prefers
2. **Check for duplicate uploads:** Ensure you didn't upload the full provider list to the preferred_providers folder
3. **Verify merge logic:** The system matches on "Full Name" - ensure name formatting is consistent
4. **Expected percentage:** Typically 10-30% of providers should be preferred

**What Happens if You Ignore This:**
- App continues to function normally
- Recommendations may not accurately reflect true preferences
- "Preferred" filter becomes less useful since most providers qualify
- Warning appears only once per app session

---

## Warning Suppression Logic

To prevent log spam and improve user experience:

1. **Person ID warnings are suppressed** - These columns are optional and don't indicate problems
2. **Preferred provider warnings use once-per-session flags** - Each warning appears only once per app session
3. **Debug logging available** - Set log level to DEBUG to see detailed information about optional columns

### Enabling Debug Logging

To see detailed information about data processing including optional columns:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or in Streamlit's logging configuration:

```toml
# .streamlit/config.toml
[logger]
level = "debug"
```

---

## Data Quality Best Practices

### For Referrals Data

**Required Columns:**
- Project ID
- Date of Intake
- Full Name (Referred From / Referred To)
- Work Address
- Latitude
- Longitude

**Optional Columns:**
- Person ID (enhances deduplication)
- Work Phone
- Last Verified Date
- Specialty

**File Format:**
- CSV or Excel (.xlsx, .xls)
- Upload to `referrals` folder in S3
- Named with timestamp for versioning

### For Preferred Providers Data

**Required Columns:**
- Contact Full Name
- Contact's Work Address
- Contact's Details: Latitude
- Contact's Details: Longitude

**Optional Columns:**
- Contact's Details: Person ID (enhances deduplication)
- Contact's Work Phone
- Contact's Details: Specialty
- Contact's Details: Last Verified Date

**File Format:**
- CSV or Excel (.xlsx, .xls)
- Upload to `preferred_providers` folder in S3
- Should contain 10-100 providers (curated list)

---

## Troubleshooting Common Issues

### Issue: Person ID warnings appear frequently

**Status:** RESOLVED in current version
**Solution:** Upgrade to latest version where Person ID is treated as optional

### Issue: Preferred provider warnings on every startup

**Cause:** Preferred providers file contains too many providers
**Solution:** 
1. Verify correct file is in S3 `preferred_providers` folder
2. Ensure file contains only curated preferred providers (not full database)
3. Re-upload correct file if needed

### Issue: All providers marked as preferred

**Cause:** Wrong file uploaded or merge issue
**Solution:**
1. Check if preferred providers file accidentally contains all providers
2. Verify "Full Name" column format matches between files
3. Consider manual review of providers marked as preferred
4. Re-upload correct preferred providers file

### Issue: Data doesn't process at all

**Cause:** Missing required columns
**Solution:**
1. Check logs for actual column names that are missing
2. Verify required columns are present (see Data Quality Best Practices above)
3. Ensure column names exactly match expected format (case-sensitive, includes spaces)
4. Check for typos in column names

---

## Technical Reference

### Code Locations

**Person ID handling:**
- `src/data/preparation.py` - `_OPTIONAL_COLUMNS` set, `_filter_missing_columns_for_warning()` function
- Lines 198-204: Person ID deduplication logic
- Lines 625-648: Warning filtering logic

**Preferred providers warnings:**
- `src/data/ingestion.py` - Lines 366-385: File size validation
- `src/app_logic.py` - Lines 140-155: Percentage validation

**Warning suppression flags:**
- `src/data/ingestion.py` - `_preferred_providers_warning_logged` (line 54)
- `src/app_logic.py` - `_preferred_pct_warning_logged` (line 30)

### Test Coverage

**Person ID tests:**
- `tests/test_person_id_deduplication.py` - Deduplication behavior
- `tests/test_person_id_warning_suppression.py` - Warning suppression behavior

**Preferred provider tests:**
- `tests/test_preferred_provider_attribution.py` - Merge logic and validation warnings

---

## Need Help?

If you continue to see warnings after following this guide:

1. Enable DEBUG logging to see detailed information
2. Check the S3 bucket contents to verify correct files are uploaded
3. Review the test files in `tests/fixtures/` for examples of correct data format
4. Contact the development team with specific error messages and log output
