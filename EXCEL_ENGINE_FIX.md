# Excel Engine Parameter Fix - Summary

## Problem

The app was encountering errors when loading data from S3:

```
Failed to process all_referrals: Excel file format cannot be determined, you must specify an engine manually.
Failed to preload all_referrals: empty dataset
Failed to process provider: Excel file format cannot be determined, you must specify an engine manually.
Failed to preload provider: empty dataset
Failed to process outbound: Excel file format cannot be determined, you must specify an engine manually.
Failed to process inbound: Excel file format cannot be determined, you must specify an engine manually.
```

## Root Cause

When pandas' `pd.read_excel()` function is called on a `BytesIO` buffer without specifying an `engine` parameter, pandas needs to auto-detect whether the file is:
- `.xlsx` (modern Excel format) - requires the `openpyxl` engine
- `.xls` (older Excel format) - requires the `xlrd` engine

This auto-detection can fail when:
1. The buffer doesn't have clear Excel file signatures
2. The file is actually CSV data but doesn't have a `.csv` extension
3. Pandas cannot determine the format from the buffer alone

## Solution

We've updated all Excel file reading operations in the codebase to:

1. **Determine the appropriate engine based on filename extension:**
   - `.xlsx` files → use `engine='openpyxl'`
   - `.xls` files → use `engine='xlrd'`
   - `.csv` files → use `pd.read_csv()`

2. **Use byte signature detection when filename is ambiguous:**
   - Use the existing `_looks_like_excel_bytes()` helper function
   - Detect XLSX signature: `b'PK\x03\x04'` (ZIP archive)
   - Detect XLS signature: `b'\xD0\xCF\x11\xE0'` (BIFF format)

3. **Implement robust fallback chains:**
   - CSV files: Try CSV first, then Excel with appropriate engine
   - Excel files: Try with engine, fallback to openpyxl, then xlrd
   - Include CSV fallback for misnamed files

## Files Modified

### 1. `src/data/preparation.py`

Updated three functions that process Excel/CSV data:

#### `process_and_save_cleaned_referrals()`
- Added engine detection logic for BytesIO buffers
- Specified engine parameter when calling `pd.read_excel()`
- Enhanced fallback chain: Excel (with sheet) → CSV → Excel (no sheet) with engine

#### `process_referral_data()`
- Added same engine detection for BytesIO buffers
- Improved error handling with engine specification
- Added fallback to both openpyxl and xlrd engines

#### `_load_excel()`
- Added engine detection for both Path/str and buffer inputs
- Specified engine for all `pd.read_excel()` calls
- Improved CSV/Excel fallback logic

### 2. `src/data/ingestion.py`

Updated one function:

#### `_process_preferred_providers_data()`
- Imported `_looks_like_excel_bytes` helper
- Added engine detection based on filename and byte signature
- Specified engine for all `pd.read_excel()` calls
- Enhanced fallback chain for preferred providers data

## Testing

The changes preserve all existing functionality while adding explicit engine specification:

1. **CSV files** from S3 are parsed with `pd.read_csv()`
2. **XLSX files** from S3 are parsed with `engine='openpyxl'`
3. **XLS files** from S3 are parsed with `engine='xlrd'`
4. **Files without extensions** use byte signature detection
5. **All cases** have CSV fallback for misnamed files

## Expected Behavior After Fix

When the app starts:
1. S3 client downloads latest files (CSV or Excel)
2. Ingestion manager detects file format from filename
3. Appropriate pandas reader is called with correct engine
4. Data is processed and cached successfully
5. No "Excel file format cannot be determined" errors

## Verification

To verify the fix:
1. Restart the Streamlit app: `streamlit run app.py`
2. Check the terminal output for successful preload messages:
   ```
   Preloaded all_referrals: XXXX records
   Preloaded preferred_providers: XXXX records
   Preloaded provider: XXXX records
   ```
3. Navigate to the Search page - data should load without errors
4. Check `data/processed/s3_auto_update_status.txt` for success message

## Technical Details

### Engine Selection Logic

```python
# Determine engine from filename
engine = None
if filename and filename.lower().endswith('.xlsx'):
    engine = 'openpyxl'
elif filename and filename.lower().endswith('.xls'):
    engine = 'xlrd'

# Fallback to byte signature detection
if not engine and not is_csv_file:
    if _looks_like_excel_bytes(buffer):
        engine = 'openpyxl'  # Default to modern Excel

# Use engine when reading
if engine:
    df = pd.read_excel(buffer, engine=engine)
else:
    # Try both engines as fallback
    try:
        df = pd.read_excel(buffer, engine='openpyxl')
    except:
        df = pd.read_excel(buffer, engine='xlrd')
```

### Byte Signature Detection

The `_looks_like_excel_bytes()` helper checks for:
- XLSX files (ZIP format): starts with `b'PK\x03\x04'`
- XLS files (BIFF format): starts with `b'\xD0\xCF\x11\xE0'`

## Dependencies

The fix relies on existing pandas Excel engines:
- `openpyxl` - for .xlsx files (modern Excel)
- `xlrd` - for .xls files (older Excel)

These should already be installed as per `requirements.txt`.

## Backward Compatibility

The fix is fully backward compatible:
- Local parquet files still work as cache
- All existing data formats are supported
- Fallback chains ensure robustness
- No breaking changes to APIs or interfaces
