# Last Verified Date Feature

## Overview

The "Last Verified Date" feature tracks when provider information was last verified, helping users identify whether provider data is current or may need updating.

## Data Sources

The feature automatically maps and normalizes Last Verified Date from the following source fields:

### Inbound Referrals
- `Referred From's Details: Last Verified Date` → `Last Verified Date`
- `Secondary Referred From's Details: Last Verified Date` → `Last Verified Date`

### Outbound Referrals
- `Dr/Facility Referred To's Details: Last Verified Date` → `Last Verified Date`

### Preferred Providers
- `Contact's Details: Last Verified Date` → `Last Verified Date`

## Freshness Indicators

Data is automatically categorized based on age:

| Status | Icon | Age Range | Meaning |
|--------|------|-----------|---------|
| **Fresh** | ✅ | 0-90 days | Recently verified, current data |
| **Stale** | ⚠️ | 90-180 days | May need verification |
| **Very Stale** | ❌ | >180 days | Likely outdated, should be updated |
| **Unknown** | ❓ | No date | Verification date not available |

## Where to Find It

### Provider Search Results
- Displays in the top recommendation card as "Last Verified"
- Shown in the results table with freshness indicator
- Format: `✅ 2024-01-15` (with emoji indicator)

### Data Quality Dashboard
1. Navigate to the Data Dashboard page
2. View "Data Quality Metrics" section for completeness
3. Check "Data Freshness Analysis" section for breakdown:
   - Count of Fresh providers
   - Count of Stale providers
   - Count of Very Stale providers
   - Count of Unverified providers

## Data Processing

### Aggregation Logic
When multiple referrals exist for the same provider, the system:
- Takes the **most recent** (maximum) Last Verified Date
- Ensures only the latest verification status is shown

### Date Handling
- Dates are normalized to `YYYY-MM-DD` format
- Excel serial dates are automatically converted
- Invalid dates are filtered out (dates before 1990)
- Missing dates are handled gracefully with "Unknown" status

## Configuration

### Custom Thresholds
While default thresholds are 90 and 180 days, the freshness indicator functions accept custom thresholds:

```python
from src.utils.freshness import get_freshness_indicator

# Use custom thresholds (e.g., 60 and 120 days)
indicator, status = get_freshness_indicator(
    date_value,
    stale_threshold_days=60,
    very_stale_threshold_days=120
)
```

## Usage Tips

1. **For Data Entry**: Ensure source Excel/CSV files include the Last Verified Date fields with current dates
2. **For Data Review**: Use the Data Dashboard to identify providers needing verification updates
3. **For Recommendations**: Consider Last Verified Date when selecting providers - fresher data is more reliable

## Technical Details

### Files Modified
- `src/data/preparation.py` - Column mapping and date normalization
- `src/data/ingestion.py` - Data standardization and aggregation
- `src/utils/freshness.py` - Freshness calculation utilities (new file)
- `pages/2_📄_Results.py` - Display in search results
- `pages/20_📊_Data_Dashboard.py` - Data quality metrics

### API Reference
See `src/utils/freshness.py` for detailed function documentation:
- `calculate_data_age_days()` - Calculate age in days
- `get_freshness_indicator()` - Get status and emoji indicator
- `format_last_verified_display()` - Format for UI display

## Testing

Comprehensive test coverage in `tests/test_last_verified_date.py` includes:
- Date mapping and normalization
- Freshness indicator logic
- Age calculation
- Display formatting
- Custom threshold handling
