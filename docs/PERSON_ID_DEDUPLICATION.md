# Person ID Deduplication Implementation

## Overview

This document describes the implementation of Person ID-based deduplication in the ETL pipeline, as requested in issue "Verify, Validate, and De-Duplicate Source Data".

## Objective

Update the ETL pipeline to deduplicate source data using "Person ID" as the unique identifier for each provider, similar to `pd.DataFrame.drop_duplicates(subset='Person ID')`.

## Implementation

### Modified Files

1. **src/data/preparation.py**
2. **src/data/ingestion.py**
3. **tests/test_person_id_deduplication.py** (new)

### Key Changes

#### 1. Referral Data Processing (`preparation.py`)

**Column Mapping Updates:**
Added Person ID to all referral configuration column mappings:
- `Referred From's Details: Person ID` → `Person ID` (inbound primary)
- `Secondary Referred From's Details: Person ID` → `Person ID` (inbound secondary)
- `Dr/Facility Referred To's Details: Person ID` → `Person ID` (outbound)

**Deduplication Logic in `_clean_referral_frame()`:**
```python
# Deduplicate by Person ID if available and has actual values
if "Person ID" in df.columns and df["Person ID"].notna().any():
    df = df.drop_duplicates(subset="Person ID", keep="first")
    logger.info("Deduplicated by Person ID: %d unique providers", len(df))

# Drop Person ID column if it's all NA (column was added but source didn't have it)
if "Person ID" in df.columns and df["Person ID"].isna().all():
    df = df.drop(columns=["Person ID"])
```

#### 2. Preferred Providers Processing

**In `process_and_save_preferred_providers()` and `process_preferred_providers()`:**
```python
# Check for the raw column name before renaming
person_id_col = "Contact's Details: Person ID"
if person_id_col in df.columns:
    df = df.drop_duplicates(subset=person_id_col, keep="first", ignore_index=True)
    logger.info("Deduplicated preferred providers by Person ID: %d unique providers", len(df))
else:
    df = df.drop_duplicates(ignore_index=True)
    logger.info("Deduplicated preferred providers (no Person ID column): %d unique providers", len(df))
```

**Column Mapping:**
Added `"Contact's Details: Person ID": "Person ID"` to the column mapping to preserve Person ID in the output.

#### 3. Ingestion Layer (`ingestion.py`)

Updated `_process_preferred_providers_data()` to use the same Person ID deduplication logic as the preparation layer:
```python
person_id_col = "Contact's Details: Person ID"
if person_id_col in df.columns:
    df = df.drop_duplicates(subset=person_id_col, keep="first", ignore_index=True)
    logger.info("Deduplicated preferred providers by Person ID: %d unique providers", len(df))
else:
    df = df.drop_duplicates(ignore_index=True)
    logger.info("Deduplicated preferred providers (no Person ID column): %d unique providers", len(df))
```

### Behavior

#### When Person ID Exists

1. **Source Data Contains Person ID:**
   - Deduplication uses `drop_duplicates(subset="Person ID", keep="first")`
   - Only the first occurrence of each Person ID is kept
   - Subsequent rows with the same Person ID are removed
   - Person ID column is preserved in the output

2. **Example:**
   ```python
   # Input data with duplicates
   [
       {"Person ID": "P001", "Name": "Dr. Smith", "Phone": "123-456-7890"},
       {"Person ID": "P001", "Name": "Dr. Smith", "Phone": "987-654-3210"},  # Duplicate - removed
       {"Person ID": "P002", "Name": "Dr. Jones", "Phone": "555-555-5555"},
   ]
   
   # Output after deduplication
   [
       {"Person ID": "P001", "Name": "Dr. Smith", "Phone": "123-456-7890"},
       {"Person ID": "P002", "Name": "Dr. Jones", "Phone": "555-555-5555"},
   ]
   ```

#### When Person ID Does Not Exist

1. **Fallback to Generic Deduplication:**
   - Uses standard `drop_duplicates()` without subset
   - Removes exact duplicate rows
   - Person ID column is not added to the output

2. **Example:**
   ```python
   # Input data without Person ID
   [
       {"Name": "Dr. Smith", "Phone": "123-456-7890", "Address": "1 Main St"},
       {"Name": "Dr. Smith", "Phone": "123-456-7890", "Address": "1 Main St"},  # Exact duplicate - removed
       {"Name": "Dr. Jones", "Phone": "555-555-5555", "Address": "2 Oak Ave"},
   ]
   
   # Output after deduplication
   [
       {"Name": "Dr. Smith", "Phone": "123-456-7890", "Address": "1 Main St"},
       {"Name": "Dr. Jones", "Phone": "555-555-5555", "Address": "2 Oak Ave"},
   ]
   ```

### Data Flow

```
S3 Bucket → Download → Deduplication (Person ID if available) → Clean & Process → Parquet Cache
                            ↓
                    Log deduplication count
                            ↓
                    Preserve Person ID column
```

## Testing

### New Test File: `tests/test_person_id_deduplication.py`

Comprehensive test suite covering:

1. **Referral Data Deduplication:**
   - `test_referral_deduplication_by_person_id`: Verifies Person ID-based deduplication for both inbound and outbound referrals
   - `test_referral_deduplication_fallback_without_person_id`: Verifies fallback behavior when Person ID is not present

2. **Preferred Providers Deduplication:**
   - `test_preferred_providers_deduplication_by_person_id`: Verifies Person ID-based deduplication
   - `test_preferred_providers_deduplication_fallback_without_person_id`: Verifies fallback behavior

### Test Results

```
tests/test_person_id_deduplication.py::test_referral_deduplication_by_person_id PASSED
tests/test_person_id_deduplication.py::test_preferred_providers_deduplication_by_person_id PASSED
tests/test_person_id_deduplication.py::test_referral_deduplication_fallback_without_person_id PASSED
tests/test_person_id_deduplication.py::test_preferred_providers_deduplication_fallback_without_person_id PASSED
```

**All existing tests continue to pass (115 tests).**

## Expected Column Names

### For Referral Data (S3 CSV/Excel):
- Primary Inbound: `Referred From's Details: Person ID`
- Secondary Inbound: `Secondary Referred From's Details: Person ID`
- Outbound: `Dr/Facility Referred To's Details: Person ID`

### For Preferred Providers (S3 CSV/Excel):
- `Contact's Details: Person ID`

### In Processed Output (Parquet):
- All sources: `Person ID`

## Logging

The implementation includes informative logging to track deduplication:

```
INFO: Deduplicated by Person ID: 150 unique providers
INFO: Deduplicated preferred providers by Person ID: 75 unique providers
INFO: Deduplicated preferred providers (no Person ID column): 80 unique providers
```

## Backward Compatibility

The implementation is fully backward compatible:
- If Person ID column exists in source data → uses Person ID for deduplication
- If Person ID column does not exist → falls back to generic deduplication
- No breaking changes to existing functionality
- All existing tests pass without modification

## Performance Considerations

- Person ID-based deduplication is highly efficient: O(n) complexity
- Uses pandas' optimized `drop_duplicates()` method
- Deduplication happens early in the pipeline to reduce downstream processing
- Minimal memory overhead

## Future Enhancements

Possible future improvements:
1. Add data quality checks for Person ID uniqueness across different data sources
2. Implement merge/reconciliation logic for providers with multiple Person IDs
3. Add Person ID validation to ensure format consistency
4. Track deduplication metrics over time

## Related Documentation

- [Data Input Formats](./DATA_INPUT_FORMATS.md) - Supported file formats and processing
- [ETL Startup Process](./ETL_STARTUP_PROCESS.md) - Overall data pipeline flow
- [Copilot Instructions](../.github/copilot-instructions.md) - Development guidelines
