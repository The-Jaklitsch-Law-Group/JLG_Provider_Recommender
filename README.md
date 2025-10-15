# JLG Provider Recommender

A Streamlit application that intelligently recommends legal service providers based on geographic proximity, workload distribution, and referral relationships. Built for The Jaklitsch Law Group to optimize client-provider matching and maintain balanced referral networks.

## Overview

The JLG Provider Recommender is a cloud-native Streamlit application that analyzes historical referral data to suggest optimal provider matches for legal clients. The system employs a multi-factor scoring algorithm combining:

- **Geographic proximity** - Vectorized haversine distance calculations accounting for Earth's curvature
- **Workload distribution** - Analyzes outbound referral patterns to prevent provider overload
- **Referral reciprocity** - Prioritizes mutual referral partnerships (inbound referral tracking)
- **Strategic preferences** - Configurable weighting for designated preferred providers

### Technical Architecture

**Data Flow**: AWS S3 (single source of truth) → Auto-download → Data cleaning pipeline (preparation.py) → Shared I/O utilities (io_utils.py) → Local Parquet cache → Application loading (ingestion.py)

**Key Technologies**:
- **Frontend**: Streamlit (multi-page app with session state management)
- **Data Processing**: Pandas (DataFrame operations), NumPy (vectorized calculations)
- **Cloud Storage**: AWS S3 with boto3 client (connection pooling, adaptive retries)
- **Geocoding**: Nominatim/OpenStreetMap API (rate-limited at 1 req/sec)
- **Caching**: Streamlit `@st.cache_data` decorators (1-hour TTL for data, geocoding)
- **Testing**: Pytest (137+ tests with mocking for external services)

**Performance Characteristics**:
- S3 download (first run): 2-5 seconds for ~5MB CSV
- Data loading (from S3-generated cache): <100ms for 10k rows
- Search execution (cached): <1 second for typical datasets
- Geocoding (cached): <10ms, (uncached): 1-3 seconds with rate limiting

The application prioritizes data integrity, performance optimization, and maintainability through centralized data ingestion, comprehensive validation, and extensive test coverage.

## Features

### Cloud-Native Data Management
- **AWS S3 Integration** - S3 is the single source of truth; local files are cache only
- **Automatic Data Sync** - Downloads latest files from S3 on app launch
- **Intelligent File Selection** - Automatically chooses most recent file by timestamp or S3 LastModified
- **Connection Pooling** - Optimized boto3 client with max 10 concurrent connections
- **Adaptive Retries** - Up to 3 retry attempts with exponential backoff for transient failures

### High-Performance Data Processing
- **Parquet Caching** - Local cache files in columnar format (~10x faster than CSV/Excel for repeated loads)
- **Vectorized Operations** - NumPy-based distance calculations (100x faster than Python loops)
- **Streamlit Caching** - 1-hour TTL for data loading and geocoding results
- **Lazy Loading** - Data loaded on-demand, not at app startup
- **Session State Management** - Preserves user preferences and search results across page navigation

### Robust Geocoding Pipeline
- **Primary Provider**: Nominatim (OpenStreetMap) - free, no API key required
- **Rate Limiting**: Strict 1 req/sec enforcement via `geopy.RateLimiter`
- **Smart Caching**: 1-hour cache for geocoding results to minimize API calls
- **Error Handling**: Graceful degradation with user-friendly error messages
- **Validation**: Coordinate range checking (-90 to 90 lat, -180 to 180 lon)

### Flexible Scoring System
- **Multi-Factor Algorithm** - Combines distance, outbound referrals, inbound referrals, preferred status
- **Configurable Weights** - Interactive sliders for scenario-specific tuning
- **Automatic Normalization** - Weights auto-normalized to sum to 1.0 (users don't need to do math)
- **Deterministic Results** - Same inputs always produce same outputs
- **Tie-Breaking** - Clear precedence rules (distance → referrals → name)

### Interactive Multi-Page UI
- **Search Page** - Address geocoding, preference configuration, filter controls
- **Results Page** - Ranked provider list with export options (CSV/Excel)
- **Data Dashboard** - Analytics, trends, data quality metrics, missing geocode detection
- **Update Data** - Manual S3 refresh trigger and file upload interface
- **Documentation** - Comprehensive algorithm explanation and usage guide

### Data Quality & Validation
- **Person ID Deduplication** - Primary deduplication using unique Person ID when available (see [Person ID Deduplication](docs/PERSON_ID_DEDUPLICATION.md))
- **Fallback Deduplication** - Generic row-level deduplication when Person ID is not present
- **Provider Identity** - Canonical identity uses `(normalized_name, normalized_address)` tuple
- **Address Normalization** - Standardized abbreviations, stripped suite numbers
- **Phone Formatting** - Consistent (XXX) XXX-XXXX format
- **Coordinate Validation** - Range checks and invalid data filtering
- **Missing Data Detection** - Identifies and reports providers without geocodes

### Comprehensive Testing
- **137+ Automated Tests** - Full pytest suite with >80% code coverage
- **Unit Tests** - Scoring, validation, distance calculation, data cleaning, I/O utilities
- **Integration Tests** - S3 client, geocoding fallback, data preparation pipeline
- **Mocked External Services** - S3 and geocoding APIs mocked for reliable CI/CD
- **Performance Tests** - Validates vectorization and caching optimizations

## Quick Start

> **🔴 BREAKING CHANGE:** As of version 2.1+, S3 configuration is **strictly required**. All local parquet file fallbacks have been removed.  
> See [S3 Migration Guide](docs/S3_MIGRATION_GUIDE.md) for detailed setup instructions and migration path from local files.  
> For understanding the data pipeline architecture, see [Data Pipeline Architecture](docs/DATA_PIPELINE_ARCHITECTURE.md).

### System Requirements

**Minimum Requirements**:
- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- 2GB RAM (4GB recommended for large datasets)
- Internet connection (required for S3 and geocoding APIs)
- AWS S3 access with valid credentials

**Recommended Environment**:
- Virtual environment (venv, conda, or similar)
- AWS IAM user with S3 read permissions
- Git for version control
- Modern web browser (Chrome, Firefox, Edge)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/The-Jaklitsch-Law-Group/JLG_Provider_Recommender.git
cd JLG_Provider_Recommender
```

2. **Create and activate virtual environment** (recommended):
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n provider-recommender python=3.10
conda activate provider-recommender
```

3. **Install runtime dependencies**:
```bash
pip install -r requirements.txt
```

**Core dependencies installed**:
- `streamlit>=1.28.0` - Web application framework
- `pandas>=2.0.0` - DataFrame operations and data manipulation
- `numpy>=1.24.0` - Vectorized numerical calculations
- `boto3>=1.28.0` - AWS S3 client library
- `geopy>=2.3.0` - Geocoding with Nominatim support
- `pyarrow>=12.0.0` - Parquet file format support
- `openpyxl>=3.1.0` - Excel file reading (for raw data imports)

4. **Install development dependencies** (for testing and linting):
```bash
pip install -r requirements-dev.txt
```

**Dev dependencies installed**:
- `pytest>=7.4.0` - Test framework
- `pytest-cov>=4.1.0` - Code coverage reporting
- `black>=23.7.0` - Code formatter
- `isort>=5.12.0` - Import sorting
- `flake8>=6.1.0` - Linting
- `pre-commit>=3.3.0` - Git hooks for code quality

5. **Configure AWS S3 credentials** (required):

Create `.streamlit/secrets.toml` in the project root:
```toml
[s3]
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
bucket_name = "jlg-provider-recommender-bucket"
region_name = "us-east-1"
referrals_folder = "990046944"
preferred_providers_folder = "990047553"
```

**⚠️ Security Note**: Never commit `.streamlit/secrets.toml` to version control. It's already in `.gitignore`.

6. **Verify installation**:
```bash
# Run tests to verify everything works
pytest tests/ -q

# Check that Streamlit can import the app
python -c "import streamlit; import app; print('✓ Installation successful')"
```

### Running the Application

**Launch the Streamlit app**:
```bash
streamlit run app.py
```

**Expected behavior**:
1. App starts on `http://localhost:8501`
2. Automatically checks S3 configuration on launch
3. Downloads latest data files from S3 (if configured)
4. Processes and caches data as Parquet files in `data/processed/`
5. Opens in default web browser

**Command-line options**:
```bash
# Custom port
streamlit run app.py --server.port 8502

# Headless mode (no browser auto-open)
streamlit run app.py --server.headless true

# Development mode with auto-reload
streamlit run app.py --server.runOnSave true

# Production mode with CORS enabled
streamlit run app.py --server.enableCORS true --server.enableXsrfProtection true
```

**Application pages**:
- **🏠 Home** (`app.py`) - Landing page with navigation and project overview
- **🔎 Search** (`pages/1_🔎_Search.py`) - Provider search interface with geocoding and scoring
- **📄 Results** (`pages/2_📄_Results.py`) - Ranked provider recommendations with export
- **🛠️ How It Works** (`pages/10_🛠️_How_It_Works.py`) - Algorithm documentation and technical details
- **📊 Data Dashboard** (`pages/20_📊_Data_Dashboard.py`) - Analytics, trends, data quality metrics
- **🔄 Update Data** (`pages/30_🔄_Update_Data.py`) - Manual S3 refresh and file upload

**First-time setup workflow**:
1. Ensure S3 credentials are configured in `.streamlit/secrets.toml`
2. Upload referral data to S3 bucket (CSV or Excel format)
3. Run `streamlit run app.py`
4. App auto-downloads and processes data (may take 5-10 seconds)
5. Navigate to **🔎 Search** page to start using the app

### Running Tests

The project includes a comprehensive test suite with 137+ tests covering all core functionality.

**Run all tests**:
```bash
pytest tests/ -v
```

**Run specific test categories**:
```bash
# Scoring algorithm tests
pytest tests/test_scoring.py -v

# S3 integration tests
pytest tests/test_s3_client.py -v

# Data cleaning tests
pytest tests/test_cleaning.py -v

# I/O utilities tests
pytest tests/test_io_utils.py -v

# Distance calculation tests
pytest tests/test_distance_calculation.py -v
```

**Run with coverage report**:
```bash
# Terminal coverage summary
pytest tests/ --cov=src --cov-report=term

# HTML coverage report (opens in browser)
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # On macOS/Linux
start htmlcov/index.html  # On Windows
```

**Quick test run** (summary only, useful for CI/CD):
```bash
pytest tests/ -q
```

**Test performance benchmarks**:
```bash
# Run tests with duration reporting
pytest tests/ --durations=10

# Run only fast tests (skip slow integration tests)
pytest tests/ -m "not slow"
```

**Continuous testing during development**:
```bash
# Auto-rerun tests on file changes (requires pytest-watch)
pip install pytest-watch
ptw tests/ src/
```

**Expected test output**:
```
tests/test_scoring.py ........................... [ 30%]
tests/test_validation.py ...................... [ 50%]
tests/test_distance_calculation.py .......... [ 65%]
tests/test_cleaning.py .................... [ 80%]
tests/test_s3_client.py ............... [ 95%]
tests/test_data_preparation.py ..... [100%]

============ 79 passed in 2.34s ============
```

## Project Structure

```
JLG_Provider_Recommender/
├── app.py                          # Main Streamlit entry point
├── pages/                          # Multi-page Streamlit UI
│   ├── 1_🔎_Search.py             # Provider search interface (landing page)
│   ├── 2_📄_Results.py            # Ranked recommendations display
│   ├── 10_🛠️_How_It_Works.py    # Algorithm documentation
│   ├── 20_📊_Data_Dashboard.py   # Data quality and analytics
│   └── 30_🔄_Update_Data.py       # Data refresh interface
├── src/                            # Core application logic
│   ├── app_logic.py               # Distance calculations and filtering
│   ├── data/
│   │   ├── ingestion.py           # Centralized data loading (Parquet/Excel)
│   │   └── preparation.py         # Raw data cleaning and processing
│   └── utils/
│       ├── addressing.py          # Address normalization
│       ├── cleaning.py            # Data cleaning utilities
│       ├── geocoding.py           # Nominatim/Google Maps geocoding
│       ├── providers.py           # Provider aggregation and deduplication
│       ├── scoring.py             # Recommendation scoring algorithm
│       └── validation.py          # Input validation
├── data/
│   ├── raw/                       # (gitignored) Downloaded from S3
│   │   └── Referrals_App_Full_Contacts.csv     # Latest file from S3
│   └── processed/                 # (gitignored) Local cache files only
│       ├── cleaned_all_referrals.parquet        # Cache (auto-generated from S3 data)
│       ├── cleaned_inbound_referrals.parquet    # Cache (auto-generated from S3 data)
│       ├── cleaned_outbound_referrals.parquet   # Cache (auto-generated from S3 data)
│       └── cleaned_preferred_providers.parquet  # Cache (auto-generated from S3 data)
├── prepare_contacts/              # Jupyter notebooks for data exploration
│   ├── contact_cleaning.ipynb     # Referral data cleaning workflow (legacy)
│   └── Cleaning_Preferred_Providers.ipynb
├── tests/                         # Comprehensive pytest suite (79+ tests)
│   ├── fixtures/                  # Small sample data for testing (static test data)
│   │   ├── sample_referrals.parquet
│   │   └── sample_providers.parquet
│   ├── test_scoring.py           # Scoring algorithm tests
│   ├── test_validation.py        # Input validation tests
│   ├── test_distance_calculation.py  # Haversine distance tests
│   ├── test_cleaning.py          # Data cleaning tests
│   └── ...
└── assets/                        # Logo and branding resources
```

## How It Works

### 1. Data Pipeline Architecture

**End-to-End Flow**: AWS S3 (source of truth) → Auto-download → Data cleaning → Local Parquet cache → Application runtime → Scoring

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS S3 Bucket                            │
│  ┌──────────────────────┐    ┌──────────────────────────────┐  │
│  │  Referrals Folder    │    │  Preferred Providers Folder  │  │
│  │  (990046944)         │    │  (990047553)                 │  │
│  │  - Latest CSV files  │    │  - Latest CSV files          │  │
│  └──────────────────────┘    └──────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────────────┘
                      │ boto3 client (connection pooling)
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Local Cache (data/raw/)                        │
│  - Referrals_App_Full_Contacts.csv (downloaded from S3)         │
│  - Referral_App_Preferred_Providers.csv (downloaded from S3)    │
└─────────────────────┬────────────────────────────────────────────┘
                      │ Data cleaning pipeline (src/data/preparation.py)
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│              Processed Cache (data/processed/)                   │
│  - cleaned_inbound_referrals.parquet (gitignored)               │
│  - cleaned_outbound_referrals.parquet (gitignored)              │
│  - cleaned_all_referrals.parquet (gitignored)                   │
│  - cleaned_preferred_providers.parquet (gitignored)             │
└─────────────────────┬────────────────────────────────────────────┘
                      │ DataIngestionManager (src/data/ingestion.py)
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Application Runtime                           │
│  - Search Page: Geocoding + Scoring + Filtering                 │
│  - Data Dashboard: Analytics + Visualization                    │
│  - Update Data: Manual S3 refresh trigger                       │
└─────────────────────────────────────────────────────────────────┘
```

**Detailed Steps**:

1. **S3 Data Storage** (`OptimizedS3DataClient`):
   - Referral data stored in AWS S3 bucket with folder-based organization
   - Connection pooling with max 10 concurrent connections
   - Adaptive retry strategy (3 attempts with exponential backoff)
   - Automatic selection of most recent file by timestamp or LastModified

2. **Auto-Download on Launch** (`src/utils/s3_client_optimized.py`):
   - App checks S3 configuration in `.streamlit/secrets.toml`
   - Downloads latest files from configured S3 folders
   - Saves to `data/raw/` as local cache
   - Skips download if local file is recent (optional optimization)

3. **Data Cleaning Pipeline** (`src/data/preparation.py`):
   - **Split referral direction**: Separates inbound/outbound referrals based on contact type
   - **Address normalization**: Standardizes abbreviations (St→Street, Ave→Avenue)
   - **Phone formatting**: Converts to (XXX) XXX-XXXX format
   - **Coordinate parsing**: Extracts lat/lon from string formats or existing columns
   - **Deduplication**: Uses `(normalized_name, normalized_address)` as unique key
   - **Geocoding**: Fills missing coordinates via Nominatim API (rate-limited)
   - **Validation**: Range checks for coordinates, phone numbers, zip codes

4. **Parquet Cache Generation** (`src/data/preparation.py`):
   - Converts cleaned DataFrames to columnar Parquet format for caching
   - Achieves ~10x faster repeated loading compared to re-parsing CSV/Excel
   - Saves to `data/processed/` as local cache (gitignored, auto-generated from S3)
   - Preserves data types and reduces file size

5. **Application Loading** (`src/data/ingestion.py`):
   - `DataIngestionManager` provides centralized data access
   - Loads from local Parquet cache (auto-generated from S3 data)
   - Applies source-specific post-processing (e.g., provider aggregation)
   - Uses Streamlit `@st.cache_data` with 1-hour TTL

**Data Source Enumeration** (`DataSource` enum in `ingestion.py`):
```python
class DataSource(Enum):
    INBOUND_REFERRALS = "inbound"        # Referrals TO the firm
    OUTBOUND_REFERRALS = "outbound"      # Referrals FROM firm to providers
    ALL_REFERRALS = "all_referrals"      # Combined dataset
    PROVIDER_DATA = "provider"           # Aggregated unique providers
    PREFERRED_PROVIDERS = "preferred"    # Preferred provider contacts
```

**Usage Pattern**:
```python
from src.data.ingestion import DataIngestionManager, DataSource

manager = DataIngestionManager()
outbound_df = manager.load_data(DataSource.OUTBOUND_REFERRALS)
# Returns clean DataFrame with automatic caching
```

### 2. Geocoding Strategy

**Multi-Tier Geocoding with Intelligent Caching**:

**Primary Provider - Nominatim (OpenStreetMap)**:
- Free, community-supported geocoding service
- No API key required (uses User-Agent header)
- Rate limit: 1 request/second (strictly enforced client-side)
- Timeout: 10 seconds per request
- Retry strategy: Up to 3 attempts with exponential backoff

**Implementation** (`src/utils/geocoding.py`):
```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Initialize with rate limiting
geolocator = Nominatim(user_agent="provider_recommender")
geocode_fn = RateLimiter(
    geolocator.geocode,
    min_delay_seconds=1.0,  # Enforce 1 req/sec
    max_retries=3
)

# Cached geocoding function
@st.cache_data(ttl=3600)  # 1-hour cache
def geocode_address_with_cache(address: str) -> Optional[Tuple[float, float]]:
    location = geocode_fn(address, timeout=10)
    return (location.latitude, location.longitude) if location else None
```

**Caching Strategy**:
- **Level 1 - Streamlit Cache**: 1-hour TTL using `@st.cache_data` decorator
- **Cache Key**: Full address string (case-sensitive)
- **Cache Hit**: <10ms response time
- **Cache Miss**: 1-3 seconds (API call with rate limiting)
- **Cache Invalidation**: After 1 hour or app restart

**Error Handling**:
```python
try:
    coords = geocode_address_with_cache(address)
except GeocoderTimedOut:
    # Retry with exponential backoff (handled by RateLimiter)
except GeocoderServiceError:
    # Service unavailable, return None and log warning
except Exception as e:
    # Unexpected error, display user-friendly message
```

**Validation** (`src/utils/validation.py`):
```python
def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate coordinate ranges."""
    return -90 <= lat <= 90 and -180 <= lon <= 180
```

**Performance Characteristics**:
- First geocode request: 1-3 seconds (API latency + rate limiting)
- Cached geocode lookup: <10ms (memory access)
- Batch geocoding (100 addresses): ~200 seconds with rate limiting
- Typical search page load: <1 second (assumes geocode cached)

### 3. Scoring Algorithm

**Multi-Factor Recommendation System with Normalized Weighting**:

The scoring algorithm combines four normalized factors to produce a final recommendation score. Higher scores indicate better matches.

**Mathematical Formula**:
```
Final_Score = α × Distance_norm + β × Outbound_norm + γ × Inbound_norm + δ × Preferred_norm
```

**Component Definitions**:

1. **Distance Normalization** (Inverted Min-Max):
   ```python
   # Calculate haversine distances for all providers
   distances = calculate_haversine_distance(user_lat, user_lon, provider_lats, provider_lons)
   
   # Invert so closer = higher value
   max_dist = distances.max()
   min_dist = distances.min()
   Distance_norm = 1 - ((distances - min_dist) / (max_dist - min_dist))
   # Result: 0 (farthest) to 1 (closest)
   ```

2. **Outbound Referral Normalization** (Direct Min-Max):
   ```python
   # More referrals = higher score (direct normalization)
   outbound_counts = provider_df['outbound_referral_count']
   Outbound_norm = (outbound_counts - outbound_counts.min()) / (outbound_counts.max() - outbound_counts.min())
   # Result: 0 (fewest referrals) to 1 (most referrals)
   ```

3. **Inbound Referral Normalization** (Direct Min-Max):
   ```python
   # More inbound referrals = stronger relationship = higher score
   inbound_counts = provider_df['inbound_referral_count']
   Inbound_norm = (inbound_counts - inbound_counts.min()) / (inbound_counts.max() - inbound_counts.min())
   # Result: 0 (no reciprocal referrals) to 1 (strongest relationship)
   ```

4. **Preferred Provider Flag** (Binary):
   ```python
   # Binary indicator for preferred provider status
   Preferred_norm = provider_df['is_preferred'].astype(float)
   # Result: 0 (not preferred) or 1 (preferred)
   ```

**Weight Normalization**:
```python
# User inputs weights via sliders (any positive values)
α, β, γ, δ = user_weights['distance'], user_weights['outbound'], user_weights['inbound'], user_weights['preferred']

# Automatically normalize to sum to 1.0
total = α + β + γ + δ
α_norm = α / total
β_norm = β / total
γ_norm = γ / total
δ_norm = δ / total

# Users don't need to manually normalize - system handles it
```

**Haversine Distance Calculation** (Vectorized with NumPy):
```python
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Vectorized haversine distance calculation in miles."""
    R = 3958.8  # Earth radius in miles
    
    # Convert to radians
    lat1_rad, lon1_rad = np.radians(lat1), np.radians(lon1)
    lat2_rad, lon2_rad = np.radians(lat2), np.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    return R * c  # Distance in miles
```

**Implementation** (`src/utils/scoring.py`):
```python
def recommend_provider(
    user_lat: float,
    user_lon: float,
    providers_df: pd.DataFrame,
    distance_weight: float = 0.4,
    outbound_weight: float = 0.4,
    inbound_weight: float = 0.2,
    preferred_weight: float = 0.0,
    max_radius_miles: float = 50.0,
    min_referrals: int = 1
) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
    """
    Score and rank providers based on multiple factors.
    
    Returns:
        Tuple of (scored_dataframe, top_provider) sorted by score descending
    """
    # Filter, normalize, score, and rank providers
    # See src/utils/scoring.py for full implementation
```

**Scoring Scenarios**:

| Scenario | Distance Weight | Outbound Weight | Inbound Weight | Preferred Weight | Use Case |
|----------|----------------|-----------------|----------------|------------------|----------|
| **Proximity Priority** | 0.7 | 0.2 | 0.1 | 0.0 | Elderly client, transport issues |
| **Balanced** | 0.4 | 0.4 | 0.2 | 0.0 | General use, typical referral |
| **Workload Distribution** | 0.2 | 0.1 | 0.7 | 0.0 | Balance capacity, strengthen partnerships |
| **Preferred Providers** | 0.3 | 0.2 | 0.0 | 0.5 | Strategic network, preferred list |

### 4. Filtering & Ranking

1. Remove providers without valid coordinates or referral counts
2. Apply minimum referral threshold (ensures experience)
3. Filter by maximum radius (geographic boundary)
4. Calculate normalized scores
5. Sort by score (descending) with deterministic tie-breaking
6. Return top recommendation + full ranked list

### 5. Key Design Principles

- **Centralized Data Loading**: Always use `DataIngestionManager.load_data()` for consistent caching and format handling
- **Deduplication Key**: Providers identified by `(normalized_name, normalized_address)` to prevent duplicates
- **Vectorized Operations**: NumPy-based distance calculations for performance
- **Immutable Operations**: All transformations preserve original data (deep copies)
- **Graceful Degradation**: Fallback handling for missing data, failed geocoding, and optional features

## Configuration

### AWS S3 Configuration (Required)

**🔴 CRITICAL**: S3 configuration is mandatory for the application to function. Local file fallbacks have been removed.

**Setup Steps**:

1. **Create IAM User** (if not already done):
   - Navigate to AWS Console → IAM → Users → Add User
   - User name: `jlg-provider-recommender-app`
   - Access type: Programmatic access (generate access key)
   - Permissions: Attach existing policy or create custom policy (see below)

2. **IAM Policy** (minimum required permissions):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::jlg-provider-recommender-bucket/*",
        "arn:aws:s3:::jlg-provider-recommender-bucket"
      ]
    }
  ]
}
```

**Recommended Additional Permissions** (for manual uploads via Update Data page):
```json
{
  "Effect": "Allow",
  "Action": [
    "s3:PutObject",
    "s3:DeleteObject"
  ],
  "Resource": "arn:aws:s3:::jlg-provider-recommender-bucket/*"
}
```

3. **Create Secrets File**:

Create `.streamlit/secrets.toml` in project root:
```toml
[s3]
# AWS credentials (from IAM user creation)
aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# S3 bucket configuration
bucket_name = "jlg-provider-recommender-bucket"
region_name = "us-east-1"  # AWS region where bucket is located

# Folder/prefix configuration (folder IDs or prefixes in S3)
referrals_folder = "990046944"
preferred_providers_folder = "990047553"
```

4. **Verify Configuration**:
```bash
# Test S3 connection using AWS CLI (optional but recommended)
aws s3 ls s3://jlg-provider-recommender-bucket/ --profile provider-recommender

# Or test within the app - it will display configuration errors on startup
streamlit run app.py
```

**S3 Bucket Structure** (expected layout):
```
jlg-provider-recommender-bucket/
├── 990046944/                              # Referrals folder
│   ├── Referrals_App_Full_Contacts_2024-01-15.csv
│   ├── Referrals_App_Full_Contacts_2024-02-10.csv
│   └── Referrals_App_Full_Contacts_2024-03-01.csv  (latest - auto-selected)
└── 990047553/                              # Preferred providers folder
    ├── Preferred_Providers_2024-01-15.csv
    └── Preferred_Providers_2024-03-01.csv  (latest - auto-selected)
```

**File Naming Conventions**:
- Include ISO date format (YYYY-MM-DD) in filename for automatic sorting
- Use consistent prefixes: `Referrals_App_Full_Contacts_` or `Preferred_Providers_`
- Supported formats: CSV (recommended), Excel (.xlsx)

**Environment-Specific Configuration**:

For production deployments (Streamlit Cloud, AWS, etc.), set secrets via platform's secrets management:

**Streamlit Cloud**:
- Go to App Settings → Secrets
- Paste TOML configuration (same format as `.streamlit/secrets.toml`)

**AWS Elastic Beanstalk**:
```bash
# Set environment variables
eb setenv S3_AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
         S3_AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
         S3_BUCKET_NAME=jlg-provider-recommender-bucket \
         S3_REGION_NAME=us-east-1
```

**Docker**:
```yaml
# docker-compose.yml
environment:
  - S3_AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
  - S3_AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  - S3_BUCKET_NAME=jlg-provider-recommender-bucket
  - S3_REGION_NAME=us-east-1
```

### Optional Configuration

**Environment Variables** (`.env` file or system environment):

```bash
# Google Maps API (optional - fallback geocoding)
GOOGLE_MAPS_API_KEY=AIzaSyBXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Streamlit configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=false
STREAMLIT_SERVER_ENABLE_CORS=true

# Logging level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

**Streamlit App Configuration** (`.streamlit/config.toml`):

```toml
[server]
port = 8501
enableCORS = true
enableXsrfProtection = true
maxUploadSize = 200  # Max file upload size in MB

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Data Source Configuration

**DataSource Enum** (`src/data/ingestion.py`):
```python
class DataSource(Enum):
    INBOUND_REFERRALS = "inbound"
    OUTBOUND_REFERRALS = "outbound"
    ALL_REFERRALS = "all_referrals"
    PROVIDER_DATA = "provider"
    PREFERRED_PROVIDERS = "preferred_providers"
```

**Cache File Locations** (auto-generated from S3 data):
```python
{
    DataSource.OUTBOUND_REFERRALS: {
        "cleaned": "data/processed/cleaned_outbound_referrals.parquet",  # Local cache
        "raw_combined": "data/raw/Referrals_App_Full_Contacts.csv",    # Downloaded from S3
    },
    # ... other mappings
}
```

**Note**: All files in `data/processed/` are cache files auto-generated from S3 source data. They are gitignored and recreated as needed.

### Data Refresh & Maintenance

**Routine Data Updates** (recommended frequency: weekly or after significant referral activity):

**Method 1 - Automatic S3 Sync** (Recommended):
1. Upload latest referral data to S3 bucket
   ```bash
   # Using AWS CLI
   aws s3 cp Referrals_App_Full_Contacts_2024-03-15.csv \
       s3://jlg-provider-recommender-bucket/990046944/
   
   aws s3 cp Preferred_Providers_2024-03-15.csv \
       s3://jlg-provider-recommender-bucket/990047553/
   ```

2. Restart the application (auto-downloads latest on launch)
   ```bash
   # Stop app (Ctrl+C in terminal)
   # Restart
   streamlit run app.py
   ```

**Method 2 - Manual Refresh via UI**:
1. Navigate to **🔄 Update Data** page in the app
2. Click **"Pull Latest from S3"** button
3. System downloads, processes, and caches new data
4. Refresh browser to see updated data

**Method 3 - Local File Upload** (for testing or one-off updates):
1. Navigate to **🔄 Update Data** page
2. Use file uploader to select local CSV/Excel file
3. System processes and caches data immediately
4. Note: This does NOT update S3 (upload manually if needed)

**Data Processing Pipeline** (automated steps after S3 download or file upload):
```
1. Download from S3 → data/raw/
2. Parse CSV/Excel → pandas DataFrame
3. Clean and normalize:
   - Split inbound/outbound referrals
   - Normalize addresses and phone numbers
   - Parse coordinates
   - Deduplicate providers
4. Geocode missing coordinates (rate-limited)
5. Save to Parquet → data/processed/
6. Clear Streamlit cache
7. Reload data in application
```

**Cache Management**:

The app uses multiple caching layers for performance:

1. **S3 Download Cache** (`data/raw/`):
   - Local copy of S3 files
   - Skipped if recent file exists locally
   - Cleared on manual refresh

2. **Parquet Cache** (`data/processed/`):
   - Cleaned and optimized data files
   - Regenerated when raw files change
   - Gitignored (not in version control)

3. **Streamlit Data Cache** (in-memory):
   - 1-hour TTL for data loading operations
   - Cleared on app restart or manual cache clear
   - Access via `@st.cache_data` decorator

4. **Geocoding Cache** (in-memory):
   - 1-hour TTL for geocoding results
   - Cleared on app restart
   - Reduces API calls for repeated addresses

**Clear All Caches**:
```python
# In Streamlit app UI
# Press "C" key → "Clear cache" menu appears → Click "Clear cache"

# Or programmatically (add button in Update Data page)
st.cache_data.clear()
```

**Monitor Data Freshness**:
- Navigate to **📊 Data Dashboard** page
- Check "Data Source Information" section
- Verify last modified dates for all data sources
- Review record counts and missing geocode stats

**Backup Strategy** (recommended for production):
```bash
# Backup S3 bucket (weekly)
aws s3 sync s3://jlg-provider-recommender-bucket/ \
    ./backups/s3-backup-$(date +%Y%m%d)/ \
    --region us-east-1

# Keep last 4 weeks of backups
find ./backups/ -type d -mtime +28 -exec rm -rf {} +
```

## Testing

The project includes a comprehensive test suite with 79+ tests:

### Test Coverage
- **Scoring Algorithm** (`test_scoring.py`) - Core recommendation logic, edge cases
- **Validation** (`test_validation.py`) - Address, coordinate, phone number validation
- **Distance Calculation** (`test_distance_calculation.py`) - Haversine accuracy, symmetry
- **Data Cleaning** (`test_cleaning.py`) - Address normalization, state mapping, deduplication
- **Geocoding** (`test_geocode_fallback.py`) - Fallback behavior when geopy unavailable
- **Data Preparation** (`test_data_preparation.py`) - S3 download → cleaning → cache generation pipeline
- **Radius Filtering** (`test_radius_filter.py`) - Geographic filtering logic
- **S3 Integration** (`test_s3_client.py`) - AWS S3 data access, download, mocking, error handling

### Running Tests

```bash
# All tests with verbose output
pytest tests/ -v

# Specific test file
pytest tests/test_scoring.py -v

# With coverage report
pytest tests/ --cov=src --cov-report=html

# Quick run (summary only)
pytest tests/ -q
```

See `tests/README.md` for detailed test documentation.

## Development Guidelines

### Code Style
- **Formatting**: Black (line length 120) + isort
- **Linting**: flake8 (configured via `.flake8`)
- **Type Hints**: Encouraged for public APIs
- **Documentation**: Docstrings for all public functions/classes

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Best Practices
1. **Small, Incremental Changes**: Keep PRs focused on a single feature/fix
2. **Test Coverage**: Add/update tests for new functionality
3. **Centralized Data Access**: Use `DataIngestionManager` instead of direct file reads
4. **Immutable Operations**: Preserve original data with `.copy(deep=True)`
5. **Graceful Error Handling**: Provide fallbacks and clear error messages
6. **Performance**: Cache expensive operations (`@st.cache_data`, `@performance.timer`)

### Adding New Features

**New Scoring Factors**:
1. Add normalization logic in `src/utils/scoring.py`
2. Update `recommend_provider()` function signature
3. Add UI controls in `pages/1_🔎_Search.py`
4. Update tests in `tests/test_scoring.py`
5. Document in `pages/10_🛠️_How_It_Works.py`

**New Data Sources**:
1. Add enum value to `DataSource` in `src/data/ingestion.py`
2. Update `_build_file_registry()` with file mappings
3. Add source-specific processing if needed
4. Update `DataIngestionManager.load_data()` documentation

**New Validation Rules**:
1. Add validation function to `src/utils/validation.py`
2. Add tests to `tests/test_validation.py`
3. Integrate into UI forms where applicable

## Troubleshooting

### Common Issues & Solutions

#### 🔴 S3 Configuration Errors

**Error**: `S3 is not configured` or `No data file found for [source]`

**Root Causes**:
1. Missing `.streamlit/secrets.toml` file
2. Invalid AWS credentials (access key or secret key)
3. Incorrect bucket name or region
4. S3 bucket is empty or files are in wrong folder
5. IAM user lacks required permissions

**Diagnostic Steps**:
```bash
# 1. Verify secrets file exists
ls -la .streamlit/secrets.toml

# 2. Test AWS credentials using AWS CLI
aws s3 ls s3://jlg-provider-recommender-bucket/ --region us-east-1

# 3. Check folder contents
aws s3 ls s3://jlg-provider-recommender-bucket/990046944/ --region us-east-1
aws s3 ls s3://jlg-provider-recommender-bucket/990047553/ --region us-east-1

# 4. Test IAM permissions
aws s3 cp s3://jlg-provider-recommender-bucket/990046944/test.csv ./test.csv
```

**Solutions**:
1. Create `.streamlit/secrets.toml` with valid S3 credentials (see Configuration section)
2. Verify credentials in AWS Console → IAM → Users → Security Credentials
3. Check bucket name matches exactly (case-sensitive)
4. Upload data files to correct S3 folders
5. Attach IAM policy with `s3:GetObject` and `s3:ListBucket` permissions

**Verification**:
- Navigate to **🔄 Update Data** page
- Click **"Pull Latest from S3"**
- Should see success message and data processing logs

---

#### 🌐 Geocoding Failures

**Error**: `Geocoding service temporarily unavailable` or returns `None`

**Root Causes**:
1. Network connectivity issues
2. Nominatim API rate limit exceeded (>1 req/sec)
3. Invalid or malformed address
4. Service downtime (rare)

**Diagnostic Steps**:
```python
# Test geocoding directly
from src.utils.geocoding import geocode_address_with_cache

# Test with known good address
result = geocode_address_with_cache("1600 Amphitheatre Parkway, Mountain View, CA")
print(result)  # Should return (lat, lon) tuple

# Check for errors
import logging
logging.basicConfig(level=logging.DEBUG)
# Re-run geocoding with debug output
```

**Solutions**:
1. **Network issues**: Check internet connection, verify firewall rules
2. **Rate limiting**: 
   - Reduce concurrent geocoding operations
   - Increase `min_delay_seconds` in `geocoding.py` (currently 1.0)
   - Batch geocode during off-hours
3. **Invalid addresses**: 
   - Verify address format: `street, city, state, zip`
   - Check for special characters or encoding issues
   - Use Data Dashboard to identify problematic addresses
4. **Service downtime**: 
   - Check Nominatim status: https://status.openstreetmap.org/
   - Wait and retry later
   - Consider Google Maps fallback (requires API key)

**Performance Optimization**:
```python
# Pre-geocode all providers offline (recommended for large datasets)
# See prepare_contacts/Contact_Geocode_Search.ipynb
```

---

#### ⚡ Slow Performance

**Symptom**: App takes >5 seconds to load pages or execute searches

**Diagnostic Steps**:
```python
# 1. Check Streamlit cache status
# In browser console: Streamlit → Settings → Show cache statistics

# 2. Profile data loading
import time
start = time.time()
from src.data.ingestion import DataIngestionManager, DataSource
manager = DataIngestionManager()
df = manager.load_data(DataSource.OUTBOUND_REFERRALS)
print(f"Load time: {time.time() - start:.2f}s")
# Should be <0.5s with local cache, <5s on first load from S3

# 3. Check file sizes
du -sh data/raw/*
du -sh data/processed/*
```

**Solutions**:

1. **Large CSV files** (>50MB):
   ```bash
   # Check if local cache files exist (auto-generated from S3)
   ls -lh data/processed/cleaned_*.parquet
   
   # If missing or stale, refresh via Update Data page (pulls from S3 and regenerates cache)
   ```

2. **Cache not being used**:
   ```bash
   # Verify local cache files exist
   ls -lh data/processed/cleaned_*.parquet
   
   # If missing, they'll be regenerated from S3 (slower first load)
   # Navigate to Update Data page and refresh to regenerate cache
   ```

3. **Too many geocoding calls**:
   ```python
   # Check geocoding cache hit rate
   # Add this to Search page temporarily:
   st.write(f"Geocoding cache info: {geocode_address_with_cache.cache_info()}")
   ```

4. **Database connection pooling** (if using external DB):
   ```python
   # Ensure connection reuse, not creating new connections per query
   ```

**Performance Benchmarks** (target metrics):
- S3 download (first time): 2-5 seconds
- S3 download (cached locally): <100ms (skipped if recent)
- Data loading (from local cache): <500ms for 10k rows
- Search execution: <1s for typical dataset
- Geocoding (cached): <10ms
- Page navigation: <200ms

---

#### 🚫 No Providers Returned

**Symptom**: Search returns 0 results or "No providers found"

**Root Causes**:
1. Filters too restrictive (radius, min referrals)
2. Missing or invalid coordinates for all providers
3. Data not loaded properly
4. Geographic mismatch (client far from all providers)

**Diagnostic Steps**:
```python
# Check provider data loaded
from src.data.ingestion import DataIngestionManager, DataSource
manager = DataIngestionManager()
providers = manager.load_data(DataSource.PROVIDER_DATA)

print(f"Total providers: {len(providers)}")
print(f"Providers with coordinates: {providers[['latitude', 'longitude']].notna().all(axis=1).sum()}")
print(f"Providers with >0 referrals: {(providers['outbound_referral_count'] > 0).sum()}")
```

**Solutions**:
1. **Relax filters**:
   - Increase max radius (try 100+ miles)
   - Decrease min referrals to 0 or 1
   - Check filter values in Search page sidebar

2. **Fix missing coordinates**:
   - Navigate to **📊 Data Dashboard**
   - Check "Missing Geocodes" section
   - Run geocoding for missing providers (Update Data page)

3. **Verify data loaded**:
   - Check Data Dashboard shows correct record counts
   - Compare with source CSV file
   - Re-pull from S3 if counts don't match

4. **Geographic mismatch**:
   - Verify client address geocoded correctly
   - Check provider locations in Data Dashboard map
   - Consider expanding service area

---

#### ⭐ Preferred Provider Issues

**See detailed documentation**: [Preferred Providers Attribution Guide](docs/PREFERRED_PROVIDERS_ATTRIBUTION.md)

**Symptom 1**: All providers marked as preferred (⭐ Yes)

**Root Cause**: Preferred providers file in S3 contains ALL providers instead of just preferred ones

**Diagnostic Steps**:
```bash
# Check S3 preferred providers file
aws s3 ls s3://jlg-provider-recommender-bucket/990047553/

# Download and inspect
aws s3 cp s3://jlg-provider-recommender-bucket/990047553/Preferred_Providers_latest.csv ./
wc -l Preferred_Providers_latest.csv  # Should be 10-100 rows, not 1000+
```

**Solution**:
1. Verify the correct file is uploaded to S3 `preferred_providers` folder
2. File should contain only firm's preferred provider contacts (typically 10-50)
3. Upload correct file if needed
4. Refresh app data (Update Data page → Pull Latest from S3)
5. Check logs for validation warnings:
   ```
   WARNING: 85.0% of providers are marked as preferred. This is unusually high...
   ```

**Symptom 2**: No providers marked as preferred (all show "No")

**Root Causes**:
1. No file in S3 `preferred_providers` folder
2. Provider names don't match between files
3. Wrong column structure in preferred file

**Diagnostic Steps**:
```bash
# Check if file exists
aws s3 ls s3://jlg-provider-recommender-bucket/990047553/

# Download and check structure
aws s3 cp s3://jlg-provider-recommender-bucket/990047553/Preferred_Providers_latest.csv ./
head -n 5 Preferred_Providers_latest.csv

# Should have column: "Contact Full Name"
```

**Solution**:
1. Upload preferred providers file to correct S3 folder
2. Ensure column "Contact Full Name" exists
3. Verify names match exactly (case-sensitive) with referrals data
4. Check logs:
   ```
   INFO: Loaded X unique preferred providers from preferred providers file
   INFO: Marked Y out of Z providers as preferred (P%)
   ```

**Expected Values**:
- 10-100 unique preferred providers (typically)
- 10-30% of total providers marked as preferred
- Warning logged if >80% are preferred

---

#### 🧪 Test Failures

**Error**: `pytest` tests fail or hang

**Common Test Issues**:

1. **Missing dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **S3 mocking issues** (`test_s3_client.py`):
   ```python
   # Ensure moto[s3] installed for S3 mocking
   pip install 'moto[s3]>=4.0.0'
   ```

3. **Geocoding tests fail** (`test_geocode_fallback.py`):
   ```python
   # These tests intentionally mock geopy as unavailable
   # Should pass even without geopy installed
   # If failing, check mock configuration in conftest.py
   ```

4. **Test data missing**:
   ```bash
   # Verify test fixtures exist
   ls -lh tests/fixtures/
   # Should contain sample_referrals.parquet, sample_providers.parquet
   ```

**Solutions**:
```bash
# Run tests with verbose output to identify failures
pytest tests/ -v --tb=short

# Run specific failing test with full traceback
pytest tests/test_s3_client.py::test_download_file -vvs

# Skip slow integration tests during development
pytest tests/ -m "not slow"

# Clear pytest cache
pytest --cache-clear
```

---

#### 🔐 Permission Errors

**Error**: `AccessDenied` or `Forbidden` when accessing S3

**Solutions**:
1. Verify IAM policy includes required actions:
   ```json
   {
     "Effect": "Allow",
     "Action": ["s3:GetObject", "s3:ListBucket"],
     "Resource": [
       "arn:aws:s3:::bucket-name/*",
       "arn:aws:s3:::bucket-name"
     ]
   }
   ```

2. Check bucket policies and CORS settings in S3 console

3. Verify credentials haven't expired (temporary credentials)

4. Test with AWS CLI to isolate app-specific vs. credential issues

---

#### 📦 Import Errors

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solutions**:
```bash
# Ensure running from project root
pwd  # Should be .../JLG_Provider_Recommender

# Set PYTHONPATH if needed
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Verify project structure
ls -la src/
# Should see __init__.py and other modules
```

---

### Debugging Tools

**Enable Debug Logging**:
```python
# Add to top of app.py or page files
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Streamlit Debugging**:
```bash
# Run with debug mode
streamlit run app.py --logger.level=debug

# Check Streamlit version
streamlit version

# Clear all caches and restart
# In browser: Press 'c' → Clear cache → Rerun
```

**Check Data Quality**:
```python
# Navigate to Data Dashboard page
# Review sections:
# - Data Source Information (file paths, dates, sizes)
# - Missing Geocodes (providers without coordinates)
# - Referral Statistics (counts, distributions)
```

## Deployment

### Production Deployment Options

#### Option 1: Streamlit Community Cloud (Recommended for Small Teams)

**Advantages**: Free hosting, automatic HTTPS, easy setup, integrated secrets management

**Steps**:
1. **Push code to GitHub** (this repository)
2. **Sign in to Streamlit Cloud**: https://share.streamlit.io/
3. **Deploy new app**:
   - Connect GitHub account
   - Select repository: `The-Jaklitsch-Law-Group/JLG_Provider_Recommender`
   - Main file: `app.py`
   - Python version: 3.10+
4. **Configure secrets** (App Settings → Secrets):
   ```toml
   [s3]
   aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
   aws_secret_access_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
   bucket_name = "jlg-provider-recommender-bucket"
   region_name = "us-east-1"
   referrals_folder = "990046944"
   preferred_providers_folder = "990047553"
   ```
5. **Deploy**: App will automatically deploy and be accessible at custom URL

**Resource Limits**:
- 1 CPU core
- 800MB RAM
- Limited to 1 app for free tier
- Auto-sleep after inactivity (spins up on access)

**Monitoring**:
- View logs in Streamlit Cloud dashboard
- Set up email alerts for crashes
- Monitor usage metrics

---

#### Option 2: AWS Elastic Beanstalk (Recommended for Production)

**Advantages**: Scalable, reliable, full control, integrated with AWS ecosystem

**Prerequisites**:
- AWS account with billing enabled
- AWS CLI installed and configured
- EB CLI installed: `pip install awsebcli`

**Deployment Steps**:

1. **Initialize EB application**:
```bash
cd JLG_Provider_Recommender
eb init -p python-3.10 provider-recommender --region us-east-1
```

2. **Create environment configuration** (`.ebextensions/streamlit.config`):
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: app:app
  aws:elasticbeanstalk:application:environment:
    STREAMLIT_SERVER_PORT: 8501
    STREAMLIT_SERVER_HEADLESS: true
    STREAMLIT_SERVER_ENABLE_CORS: true
    
commands:
  01_install_streamlit:
    command: "pip install streamlit"
```

3. **Create Procfile**:
```
web: streamlit run app.py --server.port=$PORT --server.headless=true
```

4. **Set environment variables**:
```bash
eb setenv \
  S3_AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
  S3_AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  S3_BUCKET_NAME=jlg-provider-recommender-bucket \
  S3_REGION_NAME=us-east-1 \
  REFERRALS_FOLDER=990046944 \
  PREFERRED_PROVIDERS_FOLDER=990047553
```

5. **Deploy**:
```bash
eb create provider-recommender-prod --instance-type t3.medium
eb deploy
```

**Scaling Configuration**:
```bash
# Auto-scaling based on CPU usage
eb scale 2  # Min 2 instances

# Configure load balancer
eb config  # Edit auto-scaling settings
```

**Cost Estimate** (monthly):
- t3.medium instance (2 vCPU, 4GB RAM): ~$30-40
- Load balancer: ~$20
- S3 storage (10GB): ~$0.23
- Data transfer: ~$10-20
- **Total**: ~$60-80/month

---

#### Option 3: Docker Container (Recommended for On-Premise)

**Advantages**: Portable, consistent environment, works on any Docker host

**Dockerfile**:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  provider-recommender:
    build: .
    ports:
      - "8501:8501"
    environment:
      - S3_AWS_ACCESS_KEY_ID=${S3_AWS_ACCESS_KEY_ID}
      - S3_AWS_SECRET_ACCESS_KEY=${S3_AWS_SECRET_ACCESS_KEY}
      - S3_BUCKET_NAME=${S3_BUCKET_NAME}
      - S3_REGION_NAME=us-east-1
    volumes:
      - ./data/processed:/app/data/processed  # Cache persistence
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**Build and run**:
```bash
# Build image
docker build -t jlg-provider-recommender:latest .

# Run container
docker-compose up -d

# View logs
docker-compose logs -f

# Access app
open http://localhost:8501
```

**Production considerations**:
- Use multi-stage builds to reduce image size
- Set up reverse proxy (nginx) for HTTPS
- Configure log aggregation (CloudWatch, ELK stack)
- Implement container orchestration (Kubernetes, ECS)

---

### CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci.yml`):
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Lint with flake8
      run: flake8 src/ tests/ --max-line-length=120
    
    - name: Check formatting
      run: |
        black --check src/ tests/ --line-length=120
        isort --check-only src/ tests/ --profile=black

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Streamlit Cloud
      run: |
        # Streamlit Cloud auto-deploys on push to main
        echo "Deployment triggered"
```

---

### Monitoring & Observability

**Application Logging**:
```python
# Add to app.py
import logging
from logging.handlers import RotatingFileHandler

# Configure rotating file handler
handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler, logging.StreamHandler()]
)
```

**AWS CloudWatch Integration**:
```python
# Install watchtower
pip install watchtower

# Add to app.py
import watchtower

logging.getLogger().addHandler(
    watchtower.CloudWatchLogHandler(
        log_group='provider-recommender',
        stream_name='application'
    )
)
```

**Performance Metrics**:
```python
# Add to critical functions
from src.utils.performance import timer

@timer
def load_data():
    # ... data loading logic
    pass

# Logs execution time automatically
```

**Health Check Endpoint**:
```python
# Streamlit provides built-in health check
# Access at: http://your-app/_stcore/health
# Returns 200 OK if app is running
```

---

### Security Best Practices

**1. Secrets Management**:
- Never commit `.streamlit/secrets.toml` to version control
- Use environment variables in production
- Rotate AWS credentials every 90 days
- Use IAM roles instead of access keys where possible

**2. Network Security**:
```python
# Enable HTTPS in production
# .streamlit/config.toml
[server]
enableCORS = true
enableXsrfProtection = true
```

**3. Dependency Management**:
```bash
# Regularly update dependencies
pip list --outdated
pip install --upgrade -r requirements.txt

# Security audit
pip install safety
safety check
```

**4. Access Control**:
- Implement authentication for production deployments
- Consider Streamlit's built-in authentication or OAuth
- Restrict S3 bucket access to specific IP ranges

**5. Data Protection**:
- Ensure HTTPS for all external communications
- Encrypt sensitive data at rest (S3 encryption)
- Implement audit logging for data access

---

## Maintenance Schedule

### Daily Tasks
- [ ] Monitor application health (Streamlit Cloud dashboard or logs)
- [ ] Check for S3 upload errors
- [ ] Review user-reported issues

### Weekly Tasks
- [ ] Update referral data from Filevine to S3
- [ ] Review Data Dashboard for data quality issues
- [ ] Check for missing geocodes and resolve
- [ ] Verify cache files regenerated properly

### Monthly Tasks
- [ ] Review and update dependencies (`pip list --outdated`)
- [ ] Run security audit (`safety check`)
- [ ] Analyze provider workload distribution
- [ ] Archive old S3 data (files >6 months old)
- [ ] Review application logs for errors/warnings

### Quarterly Tasks
- [ ] Rotate AWS credentials (access keys)
- [ ] Review and optimize scoring algorithm weights
- [ ] Conduct user training sessions
- [ ] Backup S3 bucket
- [ ] Review test coverage and add missing tests

### Annual Tasks
- [ ] Major dependency upgrades (Python, Streamlit, pandas)
- [ ] Security audit and penetration testing
- [ ] Performance benchmarking and optimization
- [ ] User feedback survey and feature prioritization

---

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**: Follow code style and best practices (see below)
4. **Add/update tests**: Ensure all tests pass (`pytest tests/`)
5. **Run pre-commit hooks**: `pre-commit run --all-files`
6. **Commit your changes**: Use clear, descriptive commit messages
7. **Push to your fork**: `git push origin feature/your-feature-name`
8. **Open a Pull Request**: Target the `dev` branch, not `main`

### Code Quality Standards

**Formatting**:
```bash
# Black formatter (line length 120)
black src/ tests/ --line-length=120

# Import sorting
isort src/ tests/ --profile=black --line-length=120
```

**Linting**:
```bash
# Flake8 (configured in .flake8)
flake8 src/ tests/ --max-line-length=120
```

**Pre-commit Hooks**:
```bash
# Install pre-commit hooks (runs on every commit)
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

**Testing Requirements**:
- All new features must include tests
- Maintain >80% code coverage
- Tests must pass in Python 3.10, 3.11, and 3.12
- Mock external services (S3, geocoding APIs)

### PR Guidelines
- Include description of changes and motivation
- Reference any related issues
- Ensure all tests pass
- Update documentation if behavior changes
- Keep changes focused and atomic

## License

See `LICENSE` for license details.

## Contact

For questions, issues, or feature requests:
- Open an issue on GitHub
- Contact the Data Operations team at The Jaklitsch Law Group

---

**Built with:** Python • Streamlit • Pandas • NumPy • GeoPy • Pytest
