# ETL Startup Process Documentation

## Overview

The JLG Provider Recommender app automatically triggers a complete ETL (Extract, Transform, Load) pipeline on startup. This ensures the app always has fresh, processed data available from the S3 bucket.

## ETL Pipeline Architecture

### 1. **Extract** - Data Extraction from S3

**Module**: `src.data.ingestion.DataIngestionManager._get_s3_data()`

- Downloads latest files from S3 bucket
- Supports both CSV (.csv) and Excel (.xlsx, .xls) formats
- Retrieves metadata (filename, last modified timestamp)
- Handles two data types:
  - Referrals data (inbound/outbound)
  - Preferred providers contact list

**S3 Folder Structure**:
```
s3://bucket/
├── referrals/
│   └── latest_referrals.csv (or .xlsx)
└── preferred_providers/
    └── latest_providers.csv (or .xlsx)
```

### 2. **Transform** - Data Processing and Cleaning

**Module**: `src.data.preparation.process_referral_data()`

Applies the following transformations:

- **Column normalization**: Strips whitespace, standardizes names
- **Data type conversion**: Ensures correct dtypes (dates, integers, strings)
- **Deduplication**: Uses canonical identity (normalized_name, normalized_address)
- **Data validation**: Checks for required columns, missing values
- **Geocoding preparation**: Prepares address data for geocoding
- **Provider aggregation**: Creates unique provider records with referral counts

**Processing Steps**:
1. Load raw data from S3 bytes (auto-detect CSV/Excel format)
2. Normalize column names and remove whitespace
3. Split into inbound/outbound referrals
4. Apply filters and transformations per data type
5. Combine and deduplicate records
6. Generate provider aggregation from outbound referrals
7. Validate output quality

### 3. **Load** - Cache Storage in Streamlit

**Module**: `src.data.ingestion.DataIngestionManager._load_and_process_data_cached()`

- Uses Streamlit's `@st.cache_data` decorator
- Cache key: `(source, last_modified_timestamp, data_bytes, filename)`
- Cache invalidation triggers:
  - S3 file update (detected via last_modified timestamp)
  - TTL expiration (default: 1 hour)
  - Manual cache clear
- Stores processed DataFrames in memory for fast access

**Cached Data Sources**:
- `ALL_REFERRALS`: Combined inbound + outbound referrals
- `PREFERRED_PROVIDERS`: Firm's preferred provider contacts
- `PROVIDER_DATA`: Unique providers with referral counts

## ETL Triggers

### Trigger 1: App Startup (Background Thread)

**Function**: `app.auto_update_data_from_s3()`

**When**: Every time the app starts (once per session)

**How**:
```python
# In app._build_and_run_app()
thread = threading.Thread(target=auto_update_data_from_s3, daemon=True)
thread.start()
```

**What it does**:
1. Checks if S3 is configured via `src.utils.config.is_api_enabled("s3")`
2. Calls `DataIngestionManager.preload_data()`
3. Preloads critical data sources:
   - ALL_REFERRALS
   - PREFERRED_PROVIDERS
   - PROVIDER_DATA
4. Warms the cache for immediate app responsiveness
5. Writes status to `data/processed/s3_auto_update_status.txt`

**Benefits**:
- Runs asynchronously (doesn't block UI rendering)
- Ensures data is ready when users navigate to pages
- Provides user feedback via status file

### Trigger 2: Daily Refresh (4 AM Check)

**Function**: `DataIngestionManager.check_and_refresh_daily_cache()`

**When**: Every app load (Streamlit reruns frequently)

**How**:
```python
# In app._build_and_run_app()
data_manager = get_data_manager()
refreshed = data_manager.check_and_refresh_daily_cache()
```

**What it does**:
1. Checks current time against last refresh timestamp
2. If it's after 4 AM and cache hasn't been refreshed today:
   - Clears all cached data
   - Re-runs full ETL pipeline via `preload_data()`
   - Updates last refresh timestamp in session state
3. Returns `True` if refresh occurred, `False` otherwise

**Benefits**:
- Ensures daily data freshness
- Runs during low-traffic hours (4 AM)
- Automatically recovers from stale cache

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          App Startup (app.py)                        │
│                                                                      │
│  1. _build_and_run_app() called                                    │
│  2. check_and_refresh_daily_cache() (sync, main thread)            │
│  3. auto_update_data_from_s3() (async, background thread)          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│              DataIngestionManager.preload_data()                    │
│                    (src.data.ingestion)                             │
│                                                                      │
│  Loads critical sources:                                            │
│  - ALL_REFERRALS                                                    │
│  - PREFERRED_PROVIDERS                                              │
│  - PROVIDER_DATA                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│         DataIngestionManager.load_data(source)                      │
│                                                                      │
│  For each data source:                                              │
│  1. _load_and_process_data(source)                                 │
│  2. _get_s3_data(folder_type)  ← EXTRACT                           │
│  3. _load_and_process_data_cached(...)  ← TRANSFORM + LOAD         │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                ┌───────────────────┴───────────────────┐
                ▼                                       ▼
┌──────────────────────────────┐    ┌─────────────────────────────────┐
│  EXTRACT (S3 Download)       │    │  TRANSFORM (Data Processing)    │
│                              │    │                                 │
│  S3DataClient methods:       │    │  process_referral_data():       │
│  - list_files_batch()        │    │  - Load CSV/Excel from bytes    │
│  - download_file()           │    │  - Normalize columns            │
│                              │    │  - Apply filters                │
│  Returns:                    │    │  - Deduplicate                  │
│  - data_bytes (CSV/Excel)    │    │  - Validate                     │
│  - filename                  │    │  - Aggregate providers          │
│  - last_modified             │    │                                 │
└──────────────────────────────┘    └─────────────────────────────────┘
                                                    │
                                                    ▼
                                    ┌─────────────────────────────────┐
                                    │  LOAD (Cache Storage)           │
                                    │                                 │
                                    │  @st.cache_data decorator:      │
                                    │  - Cache key: (source,          │
                                    │    last_modified, data_bytes)   │
                                    │  - TTL: 1 hour                  │
                                    │  - Stored in Streamlit memory   │
                                    │                                 │
                                    │  Result: Processed DataFrame    │
                                    └─────────────────────────────────┘
                                                    │
                                                    ▼
                                    ┌─────────────────────────────────┐
                                    │      App Usage (Pages)          │
                                    │                                 │
                                    │  Pages can access cached data:  │
                                    │  - 1_🔎_Search.py               │
                                    │  - 20_📊_Data_Dashboard.py      │
                                    │  - 30_🔄_Update_Data.py         │
                                    └─────────────────────────────────┘
```

## Code Reference

### Main ETL Orchestration (app.py)

```python
def auto_update_data_from_s3():
    """Trigger the complete ETL pipeline on app launch."""
    # Check S3 configuration
    if not is_api_enabled("s3"):
        return
    
    # Get data manager and trigger ETL
    data_manager = get_data_manager()
    data_manager.preload_data()  # Extract → Transform → Load

def _build_and_run_app():
    """Run ETL triggers on app startup."""
    # Daily refresh check (synchronous)
    data_manager = get_data_manager()
    data_manager.check_and_refresh_daily_cache()
    
    # Background ETL (asynchronous)
    thread = threading.Thread(target=auto_update_data_from_s3, daemon=True)
    thread.start()
```

### Data Ingestion Manager (src/data/ingestion.py)

```python
class DataIngestionManager:
    def preload_data(self) -> None:
        """Preload critical data sources into cache."""
        critical_sources = [
            DataSource.ALL_REFERRALS,
            DataSource.PREFERRED_PROVIDERS,
            DataSource.PROVIDER_DATA,
        ]
        for source in critical_sources:
            self.load_data(source, show_status=False)
    
    def load_data(self, source: DataSource) -> pd.DataFrame:
        """Load and process a specific data source."""
        return self._load_and_process_data(source)
    
    def _load_and_process_data(self, source: DataSource) -> pd.DataFrame:
        """Download from S3 and process."""
        # EXTRACT
        data_bytes, filename, last_modified = self._get_s3_data(folder_type)
        
        # TRANSFORM + LOAD (cached)
        return self._load_and_process_data_cached(
            source, last_modified, data_bytes, filename
        )
    
    @st.cache_data(ttl=3600)
    def _load_and_process_data_cached(
        _self, source, last_modified, data_bytes, filename
    ) -> pd.DataFrame:
        """Process data with caching."""
        # TRANSFORM
        if source == DataSource.PREFERRED_PROVIDERS:
            df = _self._process_preferred_providers_data(data_bytes, filename)
        else:
            df = _self._process_referral_data(source, data_bytes, filename)
        
        # LOAD (automatically cached by decorator)
        return df
```

### Data Preparation (src/data/preparation.py)

```python
def process_referral_data(
    raw_input: Union[bytes, BytesIO, ...],
    *,
    filename: Optional[str] = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, PreparationSummary]:
    """Transform raw data into processed DataFrames."""
    # Load from bytes (auto-detect CSV/Excel)
    if isinstance(raw_input, bytes):
        buffer = BytesIO(raw_input)
        df_all = pd.read_excel(buffer) or pd.read_csv(buffer)
    
    # Normalize
    df_all = _normalize_input_dataframe(df_all)
    
    # Process each configuration
    for key, config in _REFERRAL_CONFIGS.items():
        processed, missing = _process_referral_data(
            df_all, config["columns"], config.get("filters")
        )
        results[key] = processed
    
    # Combine and return
    inbound = _combine_inbound(...)
    outbound = _prepare_outbound(...)
    combined = pd.concat([inbound, outbound])
    
    return inbound, outbound, combined, summary
```

## Configuration

### S3 Configuration (Required)

The app requires S3 credentials in `.streamlit/secrets.toml`:

```toml
[aws]
access_key_id = "YOUR_ACCESS_KEY"
secret_access_key = "YOUR_SECRET_KEY"
region = "us-east-1"
bucket_name = "your-bucket-name"
```

### Cache Configuration

Cache TTL is configurable in `DataIngestionManager.__init__()`:

```python
def __init__(self):
    self.cache_ttl = 3600  # 1 hour (default)
```

### Daily Refresh Time

Refresh time is configurable in `check_and_refresh_daily_cache()`:

```python
refresh_time = time(4, 0, 0)  # 4:00 AM (default)
```

## Testing

The ETL process can be tested using the test fixtures:

```bash
# Run ingestion tests
pytest tests/test_data_preparation.py -v

# Run with S3 disabled (local mode)
pytest tests/ -v
```

Tests use the `disable_s3_only_mode` fixture to allow local file access.

## Monitoring

### Status Messages

The app writes ETL status to `data/processed/s3_auto_update_status.txt`:

- `✅ ETL complete: Data extracted from S3, transformed, and loaded to cache`
- `❌ ETL process failed: {error_message}`
- `ℹ️ S3 not configured — ETL process skipped`

### Logging

ETL operations are logged via Python's logging module:

```python
logger.info("Starting ETL process: Extract from S3 → Transform → Load to cache...")
logger.info("Processed 1234 records for all_referrals")
logger.warning("No data available for provider_data")
logger.error("Failed to download referrals from S3: connection timeout")
```

## Troubleshooting

### Issue: ETL Not Running

**Symptoms**: App starts but no data available

**Solutions**:
1. Check S3 configuration in `.streamlit/secrets.toml`
2. Verify S3 bucket permissions (read access required)
3. Check logs for error messages
4. Manually trigger ETL from Update Data page

### Issue: Stale Data

**Symptoms**: App shows old data

**Solutions**:
1. Wait for daily refresh (after 4 AM)
2. Manually clear cache from Update Data page
3. Check S3 bucket for latest files
4. Verify cache TTL hasn't expired prematurely

### Issue: Slow Startup

**Symptoms**: App takes long time to load

**Solutions**:
1. ETL runs in background thread (shouldn't block UI)
2. Check network connection to S3
3. Reduce cache TTL if memory constrained
4. Consider reducing preload sources

## Summary

The JLG Provider Recommender implements a robust ETL pipeline that:

1. ✅ **Automatically triggers** on app startup (background thread)
2. ✅ **Extracts** latest data from S3 (CSV/Excel support)
3. ✅ **Transforms** data with comprehensive cleaning and validation
4. ✅ **Loads** processed DataFrames into Streamlit cache
5. ✅ **Refreshes** daily (4 AM) to ensure data freshness
6. ✅ **Monitors** via logging and status files
7. ✅ **Tests** with comprehensive test suite

All ETL logic is centralized in `src.data.ingestion` and `src.data.preparation` modules, making it easy to maintain and extend.
