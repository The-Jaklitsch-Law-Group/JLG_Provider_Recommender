# Preferred Providers Attribution - Expected Behavior

## Overview

The JLG Provider Recommender marks certain providers as "preferred" based on a curated list of preferred provider contacts maintained by the firm. This document explains how the preferred provider attribution works and how to verify it's functioning correctly.

## How It Works

### Data Sources

1. **General Provider List**: Generated from outbound referrals data (all providers the firm has referred clients to)
2. **Preferred Providers List**: A separate, curated contact list stored in the S3 `preferred_providers` folder

### Attribution Logic

The system merges the general provider list with the preferred providers list using the following logic:

1. Load the preferred providers file from S3
2. Perform an **outer join** on the `Full Name` field
   - Providers in both lists → marked as preferred ✓
   - Providers only in preferred list → included and marked as preferred ✓
   - Providers only in general list → marked as not preferred ✗
3. The `Preferred Provider` column is set to `True` or `False` accordingly

### Scoring Impact

When a provider is marked as preferred and the `preferred_weight` parameter is > 0:
- The provider's recommendation score is increased
- This gives preferred providers an edge in the ranking algorithm
- The weight is normalized and added to the overall score

## Expected Behavior

### Normal Case
- **Preferred providers file should contain**: Only the firm's preferred provider contacts (typically 10-50 providers)
- **Result**: Only those specific providers are marked as preferred
- **Example**: If the file contains Dr. Smith and Dr. Jones, only they are marked as preferred

### Bug Scenario (Issue Fixed)
- **Problem**: If the preferred providers file contains ALL providers instead of just preferred ones
- **Result**: All providers would be incorrectly marked as preferred
- **Validation**: The system now detects this and logs a warning

## Validation and Monitoring

The system includes built-in validation to detect incorrect data:

### File-Level Validation (in `src/data/ingestion.py`)

When loading the preferred providers file:
```python
if unique_providers > 100:
    logger.warning(
        f"WARNING: Preferred providers file contains {unique_providers} unique providers. "
        "This is unusually high. Please verify that the correct file was uploaded..."
    )
```

### Attribution-Level Validation (in `src/app_logic.py`)

After merging the lists:
```python
if preferred_pct > 80:
    logger.warning(
        f"WARNING: {preferred_pct:.1f}% of providers are marked as preferred. "
        "This is unusually high and may indicate that the preferred providers file "
        "contains all providers instead of just the preferred ones..."
    )
```

## Troubleshooting

### All Providers Marked as Preferred

**Symptoms:**
- Results page shows all providers with "⭐ Yes" in the Preferred Provider column
- Logs show >80% of providers marked as preferred

**Root Cause:**
- The preferred providers file in S3 contains all providers instead of just preferred ones

**Solution:**
1. Check the file in the S3 `preferred_providers` folder
2. Verify it contains only the firm's preferred provider contacts
3. If incorrect, upload the correct preferred providers file
4. Refresh the app data cache (Update Data page)

### No Providers Marked as Preferred

**Symptoms:**
- All providers show "No" in the Preferred Provider column
- Logs show 0 providers marked as preferred

**Possible Causes:**
1. **Missing file**: No file in the S3 `preferred_providers` folder
2. **Name mismatch**: Provider names in the preferred file don't match those in the referrals data
3. **Wrong column**: The file doesn't have a "Contact Full Name" column

**Solution:**
1. Check logs for errors loading preferred providers
2. Verify the file exists in the correct S3 folder
3. Check that provider names match exactly (case-sensitive)
4. Ensure the file has the expected column structure

### Verifying Correct Attribution

To verify preferred providers are correctly attributed:

1. **Check the logs**:
   ```
   INFO: Loaded X unique preferred providers from preferred providers file
   INFO: Marked Y out of Z providers as preferred (P%)
   ```

2. **Expected values**:
   - X (unique preferred providers) should be 10-100 (typically)
   - P (percentage) should be 10-30% (typically)
   - If P > 80%, you'll see a warning

3. **Inspect results**:
   - Go to the Results page after a search
   - Check the "Preferred Provider" column
   - Only specific providers should show "⭐ Yes"

## File Format Requirements

The preferred providers file should:
- Be uploaded to the S3 `preferred_providers` folder
- Be in CSV or Excel format
- Include at minimum these columns:
  - `Contact Full Name` (required) - must match provider names in referrals data
  - `Contact's Details: Latitude` (required)
  - `Contact's Details: Longitude` (required)
  - `Contact's Details: Specialty` (optional)

## Testing

The preferred provider attribution is tested in `tests/test_preferred_provider_attribution.py`:

- ✓ Correct marking when only some providers are preferred
- ✓ Handling of empty preferred providers list
- ✓ Validation warnings for suspicious data
- ✓ Inclusion of preferred-only providers (not in referrals)
- ✓ Specialty override from preferred list
- ✓ Detection of the "all providers marked as preferred" bug

Run tests with:
```bash
pytest tests/test_preferred_provider_attribution.py -v
```

## Related Files

- **Logic**: `src/app_logic.py` (lines 109-158)
- **Data loading**: `src/data/ingestion.py` (`_process_preferred_providers_data`)
- **Scoring**: `src/utils/scoring.py` (`recommend_provider`)
- **Tests**: `tests/test_preferred_provider_attribution.py`
- **Display**: `pages/2_📄_Results.py` (formats as "⭐ Yes" / "No")
