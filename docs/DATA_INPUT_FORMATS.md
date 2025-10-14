# Data Input Format Support

**⚠️ IMPORTANT: S3 is now the canonical data source. Only CSV files are supported. All data is cached in-memory for 24 hours.**

## Overview

The JLG Provider Recommender supports **CSV file format exclusively** for data input from AWS S3.

## Data Flow

```
S3 Bucket (CSV) → Auto-Download → Transform → In-Memory Cache (24hr) → App
     OR
Manual Upload (CSV) → Transform → In-Memory Cache (24hr) → App
```

**Note:** CSV files in `data/processed/` are temporary cache files created from transformed S3 data, not source files.

## Supported Input Sources

### 1. S3 Bucket (CSV files only)
- **Format**: CSV (Comma-Separated Values) 
- **Use Case**: Automatic data pulls from AWS S3
- **File Pattern**: `*.csv`
- **Processing**: Automatic CSV parsing
- **Cache**: Transformed data cached in-memory for 24 hours

### 2. Local File Upload (CSV only)
- **Format**: CSV (`.csv`)
- **Use Case**: Manual file uploads via Streamlit UI
- **Processing**: Direct CSV parsing
- **Cache**: Transformed data cached in-memory for 24 hours

### 3. File Paths (CSV only)
- **Format**: CSV only
- **Use Case**: Processing from local filesystem paths
- **Processing**: CSV parsing with validation

## Processing Logic

The data preparation pipeline (`src/data/preparation.py`) uses CSV-only format:

### Buffer/Bytes Input (S3 or Uploads)
```python
process_and_save_cleaned_referrals(
    raw_bytes,          # bytes or BytesIO object (CSV data)
    output_dir,         # Path to save processed CSV files
    filename="data.csv" # Filename hint for logging
)
```

**Format Detection:**
1. Parse as CSV
2. If parsing fails, raise error with detailed message

### File Path Input
```python
process_and_save_cleaned_referrals(
    Path("data.csv"),   # Path to CSV file
    output_dir          # Path to save processed files
)
```

**Format Detection:**
1. Check file extension is `.csv`
2. Parse as CSV
3. If not `.csv`, raise ValueError

### DataFrame Input
```python
process_and_save_cleaned_referrals(
    df,                 # Pre-loaded DataFrame
    output_dir,         # Path to save processed files
    filename="source.csv"  # Optional filename for logging
)
```

**Direct Processing:**
- No format detection needed
- DataFrame is processed directly
- Column names are normalized (whitespace stripped)

## Examples

### S3 CSV Download
```python
from src.utils.s3_client_optimized import S3DataClient
from src.data.preparation import process_and_save_cleaned_referrals

client = S3DataClient()
file_bytes, filename = client.download_latest_file('referrals')
# filename = "Referrals_App_Full_Contacts_2025-10-08.csv"

summary = process_and_save_cleaned_referrals(
    file_bytes,
    Path("data/processed"),
    filename=filename  # CSV auto-detected from extension
)
```

### Local CSV Upload
```python
# Streamlit file uploader
uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
if uploaded_file:
    summary = process_and_save_cleaned_referrals(
        uploaded_file.getvalue(),  # bytes
        Path("data/processed"),
        filename=uploaded_file.name  # "data.csv"
    )
```

### Local CSV File
```python
summary = process_and_save_cleaned_referrals(
    Path("data/raw/referrals.csv"),
    Path("data/processed")
)
```

## Output Format

All processing functions save transformed data as CSV files:

- `inbound_referrals.csv`: Inbound referral data
- `outbound_referrals.csv`: Outbound referral data  
- `all_referrals.csv`: Combined inbound + outbound
- `preferred_providers.csv`: Preferred provider contacts

These CSV files are:
- Cached in `data/processed/` directory
- Loaded into Streamlit cache with 24-hour TTL
- Automatically refreshed from S3 on app launch
- Gitignored (not committed to repository)

## Best Practices

### For S3 Exports
- ✅ Use CSV format (smaller file size, faster processing)
- ✅ Include `.csv` extension in S3 object key
- ✅ Ensure column names match expected structure

### For Local Uploads
- ✅ Use CSV format exclusively
- ✅ Use consistent column naming
- ✅ Include all required fields (Name, Address, Lat/Long)

### For Batch Processing
- ✅ Use CSV for all data generation
- ✅ Include filename parameter when processing bytes
- ✅ Check `summary.warnings` for data quality issues

## Cache Behavior

- **Cache Duration**: 24 hours (86400 seconds)
- **Cache Revalidation**: On app reload or after 24 hours
- **Cache Storage**: In-memory (Streamlit cache_data)
- **Cache Files**: CSV files in `data/processed/` (temporary, gitignored)

## Error Handling

The processing pipeline includes comprehensive error handling:

1. **Format Detection Failures**: CSV parsing errors raise ValueError with detailed message
2. **Missing Columns**: Warnings logged, processing continues with available data
3. **Invalid Data**: Rows with missing critical fields filtered out, reported in summary
4. **Unsupported Formats**: Clear error messages when non-CSV files are provided

### Error Example
```python
try:
    summary = process_and_save_cleaned_referrals(
        file_bytes,
        Path("data/processed"),
        filename="data.xlsx"  # Will raise ValueError
    )
except ValueError as e:
    print(f"Error: {e}")
    # Output: "Only CSV files are supported. Got: .xlsx"
```

## Expected Data Structure

CSV files should contain the following column structure:

### Referrals Data
- `Project ID`
- `Date of Intake` (Excel serial number or ISO date string)
- `Referral Source`
- `Referred From Full Name`
- `Referred From's Work Phone`
- `Referred From's Work Address`
- `Referred From's Details: Latitude`
- `Referred From's Details: Longitude`

### Preferred Providers Data
- `Contact's Details: Latitude`
- `Contact's Details: Longitude`
- Additional provider information fields

## Date Handling

The system automatically handles different date formats:

1. **Excel Serial Dates**: Numeric values (e.g., `44927`) converted using Excel origin `1899-12-30`
2. **ISO Timestamps**: Standard datetime strings (e.g., `2023-01-15T10:30:00`)
3. **CSV Numeric Strings**: String representations of Excel serials (e.g., `"44927"`)

All dates are normalized to `datetime64[ns]` format during processing.

## Validation Results

### Test: S3 CSV → Parquet
```
Input:  CSV bytes (398 bytes), filename="...csv"
Output: 3 parquet files, 2 records processed
Status: ✓ SUCCESS
```

### Test: Local Excel → Parquet
```
Input:  Excel bytes (5246 bytes), filename="...xlsx"
Output: 3 parquet files, 2 records processed
Status: ✓ SUCCESS
```

## Troubleshooting

### Issue: "Excel file format cannot be determined"
**Cause**: pandas trying to read CSV as Excel without correct engine
**Solution**: Implemented in code via CSV fallback logic

### Issue: Missing columns warning
**Cause**: Input file structure doesn't match expected schema
**Solution**: Check column names in source file, ensure exact match

### Issue: Empty output files
**Cause**: All records filtered out due to missing required fields
**Solution**: Check `summary.issue_records` for details on filtered rows

## File Locations

- **Processing Logic**: `src/data/preparation.py`
- **S3 Client**: `src/utils/s3_client.py`
- **UI Integration**: `pages/30_🔄_Update_Data.py`
- **Tests**: `tests/test_data_preparation.py`, `tests/test_s3_client.py`

## Related Documentation

- [API Secrets Guide](./API_SECRETS_GUIDE.md) - S3 credentials setup
- [Test Expansion Summary](../tests/TEST_EXPANSION_SUMMARY.md) - Test coverage details
- [Copilot Instructions](../.github/copilot-instructions.md) - Development guidelines
