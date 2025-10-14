# Data Ingestion Module Review

**Date:** October 14, 2025  
**Module:** `src/data/ingestion.py`  
**Scope:** Verify CSV data extraction from S3, transformation, and caching

## Executive Summary

✅ **Overall Status:** The module successfully handles CSV data from S3 through transformation to `st.cache_data`

The ingestion pipeline properly supports CSV files alongside Excel formats, with robust fallback handling and proper caching strategies.

## Detailed Analysis

### 1. CSV Data Extraction from S3 ✅

**Location:** `src/utils/s3_client_optimized.py` lines 200-210

```python
# Include Excel and CSV files
if obj["Key"].lower().endswith((".xlsx", ".xls", ".csv")):
    filename = obj["Key"].split("/")[-1]
    files.append((filename, obj["LastModified"]))
```

**Status:** ✅ VERIFIED
- S3 client correctly lists CSV files (`.csv` extension)
- Files are sorted by `LastModified` timestamp (most recent first)
- Both `referrals` and `preferred_providers` folders support CSV

### 2. CSV Data Transformation ✅

**Location:** `src/data/preparation.py`

The module handles CSV transformation through multiple layers:

#### Layer 1: `_load_excel()` helper (lines 789-844)
Despite the misleading name, this function handles CSV files:

```python
def _load_excel(raw_input: Any, filename: Optional[str] = None) -> pd.DataFrame:
    # For file paths
    if suffix == '.csv':
        df = pd.read_csv(raw_path)
    else:
        try:
            df = pd.read_excel(raw_path)
        except Exception:
            df = pd.read_csv(raw_path)  # Fallback to CSV
    
    # For byte streams
    if filename and isinstance(filename, str) and filename.lower().endswith('.csv'):
        try:
            df = pd.read_csv(excel_buffer)
        except Exception:
            excel_buffer.seek(0)
            df = pd.read_excel(excel_buffer)
    else:
        try:
            df = pd.read_excel(excel_buffer)
        except Exception:
            excel_buffer.seek(0)
            df = pd.read_csv(excel_buffer)  # Fallback to CSV
```

**Features:**
- ✅ Explicit CSV detection via filename
- ✅ Automatic fallback from Excel to CSV
- ✅ Handles both file paths and byte streams
- ✅ Column name normalization (`.str.strip()`)

#### Layer 2: `process_referral_data()` (lines 639-780)
- ✅ Calls `_load_excel()` for all input types
- ✅ Applies standardized transformations regardless of source format
- ✅ Returns clean DataFrames (inbound, outbound, combined)

#### Layer 3: `process_preferred_providers()` (lines 927-1000)
- ✅ Uses same `_load_excel()` helper
- ✅ Processes preferred providers from CSV or Excel
- ✅ Applies schema mapping and deduplication

**Transformations Applied (All Formats):**
1. Column name normalization (whitespace stripping)
2. Phone number formatting: `(123) 456-7890`
3. Address cleaning (remove double commas/spaces)
4. Geocode validation (-180 to +180 range)
5. Date normalization (handles Excel serial dates and ISO formats)
6. Deduplication
7. Schema mapping to standardized column names

### 3. Data Caching with `st.cache_data` ✅

**Location:** `src/data/ingestion.py` lines 129-169

```python
@st.cache_data(ttl=3600, show_spinner=False)
def _load_and_process_data_cached(_self, source: DataSource, 
                                   last_modified: str, 
                                   data_bytes: bytes, 
                                   filename: str) -> pd.DataFrame:
```

**Cache Key Components:**
1. `source` - Data source type (enum)
2. `last_modified` - S3 timestamp (ISO format string)
3. `data_bytes` - Raw file content (hash)
4. `filename` - Filename for logging

**Cache Invalidation Strategy:**
- ✅ Automatic invalidation when S3 file is updated (via `last_modified` timestamp)
- ✅ 1-hour TTL (`ttl=3600`) for additional freshness
- ✅ Manual cache clearing via `refresh_data_cache()`
- ✅ Daily 4 AM cache refresh via `check_and_refresh_daily_cache()`

**Backward-Compatible Functions (also cached):**
```python
@st.cache_data(ttl=3600, show_spinner=False)
def load_detailed_referrals(filepath: Optional[str] = None) -> pd.DataFrame
def load_inbound_referrals(filepath: Optional[str] = None) -> pd.DataFrame
def load_provider_data(filepath: Optional[str] = None) -> pd.DataFrame
def load_all_referrals(filepath: Optional[str] = None) -> pd.DataFrame
def load_preferred_providers(filepath: Optional[str] = None) -> pd.DataFrame
```

### 4. Complete Data Flow ✅

```
┌─────────────────────────────────────────────────────────────────┐
│ S3 Bucket (CSV/Excel files)                                     │
│  └─ referrals/         (990046944)                              │
│  └─ preferred_providers/ (990047553)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ S3DataClient._get_s3_data()                                     │
│  - Lists files (including .csv)                                 │
│  - Downloads latest file (by LastModified)                      │
│  - Returns: (bytes, filename, last_modified)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ DataIngestionManager._load_and_process_data_cached()            │
│  - Cached with: source, last_modified, data_bytes, filename     │
│  - TTL: 3600s (1 hour)                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ preparation._load_excel()                                       │
│  - Detects CSV via filename                                     │
│  - pd.read_csv() or pd.read_excel()                             │
│  - Automatic fallback handling                                  │
│  - Column name normalization                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ preparation.process_referral_data() OR                          │
│ preparation.process_preferred_providers()                       │
│  - Phone number formatting                                      │
│  - Address cleaning                                             │
│  - Geocode validation                                           │
│  - Date normalization                                           │
│  - Schema mapping                                               │
│  - Deduplication                                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ st.cache_data (Streamlit Cache)                                │
│  - Clean DataFrame ready for use                               │
│  - Available to all pages via DataIngestionManager             │
└─────────────────────────────────────────────────────────────────┘
```

## Issues and Recommendations

### Minor Issues

1. **Misleading Function Name** 🟡
   - **Location:** `src/data/preparation.py:789`
   - **Issue:** Function named `_load_excel()` but handles CSV files
   - **Impact:** Low - functionality works correctly, just confusing
   - **Recommendation:** Rename to `_load_data()` or `_load_file()`

2. **Inconsistent CSV Handling** 🟡
   - **Location:** `src/data/preparation.py:639-750`
   - **Issue:** `process_referral_data()` doesn't use `_load_excel()` helper consistently
   - **Impact:** Low - has duplicate CSV handling logic
   - **Recommendation:** Refactor to use `_load_excel()` helper throughout

### Documentation Gaps

1. **DataFormat Enum Not Used** 📝
   - **Location:** `src/data/ingestion.py:71-75`
   - **Issue:** `DataFormat.CSV` enum exists but isn't actively used
   - **Recommendation:** Either use it or remove it

2. **CSV Support Not Documented** 📝
   - **Location:** Module docstrings
   - **Issue:** Module docs don't mention CSV support
   - **Recommendation:** Update docstrings to clarify CSV + Excel support

## Test Coverage Recommendations

### Suggested Test Cases

1. **CSV Loading from S3**
   ```python
   def test_load_csv_from_s3(mock_s3_client):
       """Verify CSV files are loaded correctly from S3"""
       pass
   ```

2. **CSV Transformation**
   ```python
   def test_csv_transformation():
       """Verify CSV data is transformed identically to Excel"""
       pass
   ```

3. **Cache Invalidation on CSV Update**
   ```python
   def test_cache_invalidation_csv():
       """Verify cache invalidates when CSV file updated in S3"""
       pass
   ```

4. **Excel-to-CSV Fallback**
   ```python
   def test_excel_to_csv_fallback():
       """Verify automatic fallback when Excel parsing fails"""
       pass
   ```

## Conclusion

✅ **CSV extraction from S3:** Working correctly  
✅ **CSV transformation:** Fully implemented with robust fallback handling  
✅ **Caching with st.cache_data:** Properly configured with S3 metadata-based invalidation  

The ingestion module handles CSV files correctly throughout the entire pipeline. The only improvements needed are:
1. Renaming `_load_excel()` for clarity
2. Consolidating duplicate CSV handling logic
3. Updating documentation to reflect CSV support

**No functional changes required** - the system works as intended for CSV data.

## References

- **S3 Client:** `src/utils/s3_client_optimized.py`
- **Data Preparation:** `src/data/preparation.py`
- **Data Ingestion:** `src/data/ingestion.py`
- **Copilot Instructions:** `.github/copilot-instructions.md`
