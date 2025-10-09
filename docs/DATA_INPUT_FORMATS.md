# Data Input Format Support

**⚠️ IMPORTANT: S3 is now the canonical data source. Local parquet files have been deprecated and removed from the repository.**

## Overview

The JLG Provider Recommender supports **both CSV and Excel file formats** for data input, with intelligent automatic detection and fallback mechanisms to ensure seamless processing from AWS S3 or manual uploads.

## Data Flow

```
S3 Bucket (CSV/Excel) → Auto-Download → Clean & Process → Local Parquet Cache → App
     OR
Manual Upload (CSV/Excel) → Clean & Process → Local Parquet Cache → App
```

**Note:** Local parquet files in `data/processed/` are cache files auto-generated from S3, not source files.

## Supported Input Sources

### 1. S3 Bucket (CSV files)
- **Format**: CSV (Comma-Separated Values)
- **Use Case**: Automatic data pulls from AWS S3
- **File Pattern**: `*.csv`
- **Processing**: Automatic detection via filename extension

### 2. Local File Upload (Excel or CSV)
- **Formats**:
  - Excel: `.xlsx`, `.xls`
  - CSV: `.csv`
- **Use Case**: Manual file uploads via Streamlit UI
- **Processing**: Format auto-detection based on file extension and content

### 3. File Paths (Excel or CSV)
- **Formats**: Both Excel and CSV
- **Use Case**: Processing from local filesystem paths
- **Processing**: Extension-based detection with fallback

## Processing Logic

The data preparation pipeline (`src/data/preparation.py`) uses intelligent multi-layer format detection:

### Buffer/Bytes Input (S3 or Uploads)
```python
process_and_save_cleaned_referrals(
    raw_bytes,          # bytes or BytesIO object
    output_dir,         # Path to save processed files
    filename="data.csv" # Filename hint for format detection
)
```

**Detection Flow**:
1. **Filename Check**: If filename ends with `.csv` → Try CSV first
2. **Excel Attempt**: Try `pd.read_excel()` with sheet name
3. **CSV Fallback**: If Excel fails → Try `pd.read_csv()`
4. **Final Attempt**: Try Excel without sheet name (single-sheet files)

### Path Input (Local Files)
```python
process_and_save_cleaned_referrals(
    "data/raw/referrals.csv",  # or .xlsx
    "data/processed"
)
```

**Detection Flow**:
1. **Extension Check**: `.csv` → Read as CSV directly
2. **Other Extensions**: Try Excel with sheet name → CSV fallback → Excel without sheet

### DataFrame Input (Pre-loaded Data)
```python
df = pd.read_csv("data.csv")
process_and_save_cleaned_referrals(
    df,                # Already loaded DataFrame
    "data/processed"
)
```

**Processing**: Immediate processing, no format detection needed

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

### Local Excel Upload
```python
# Streamlit file uploader
uploaded_file = st.file_uploader("Upload Excel file", type=['xlsx', 'xls'])
if uploaded_file:
    summary = process_and_save_cleaned_referrals(
        uploaded_file.getvalue(),  # bytes
        Path("data/processed"),
        filename=uploaded_file.name  # "data.xlsx"
    )
```

### Local CSV File
```python
summary = process_and_save_cleaned_referrals(
    Path("data/raw/referrals.csv"),
    Path("data/processed")
)
```

## Expected Data Structure

Both CSV and Excel files should contain the same column structure:

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

## Error Handling

The processing pipeline includes comprehensive error handling:

1. **Format Detection Failures**: Multiple fallback attempts before raising error
2. **Missing Columns**: Warnings logged, processing continues with available data
3. **Invalid Data**: Rows with missing critical fields filtered out, reported in summary

## Best Practices

### For S3 Exports
- ✅ Use CSV format (smaller file size, faster processing)
- ✅ Include `.csv` extension in S3 object key
- ✅ Ensure column names match expected structure

### For Local Uploads
- ✅ Either CSV or Excel format works equally well
- ✅ Use consistent column naming
- ✅ Include all required fields (Name, Address, Lat/Long)

### For Batch Processing
- ✅ Prefer CSV for programmatic generation
- ✅ Include filename parameter when processing bytes
- ✅ Check `summary.warnings` for data quality issues

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
