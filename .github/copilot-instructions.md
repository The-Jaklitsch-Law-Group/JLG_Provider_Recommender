# Copilot Instructions: JLG Provider Recommender

## Project Overview
A Streamlit-based healthcare provider recommendation system for The Jaklitsch Law Group. The app geocodes client addresses and recommends medical providers based on proximity and referral history.

## Architecture & Data Flow

### Core Components
- **`app.py`**: Main Streamlit application with 4 tabs (Find Provider, How Selection Works, Data Quality, Update Data)
- **`data_dashboard.py`**: Standalone data quality monitoring dashboard
- **`src/data/ingestion.py`**: Centralized data loading with smart format prioritization (Parquet > Excel)
- **`src/utils/providers.py`**: Provider recommendation algorithm and geocoding utilities
- **`prepare_contacts/contact_cleaning.ipynb`**: Jupyter notebook for data preprocessing

### Data Processing Pipeline
1. **Raw Data**: Excel files in `data/raw/` (Referrals_App_Full_Contacts.xlsx)
2. **Processed Data**: Optimized Parquet files in `data/processed/` (cleaned_*.parquet)
3. **Data Sources**: Inbound referrals, outbound referrals, and provider data unified through `DataIngestionManager`

## Key Development Patterns

### Data Loading Strategy
- **Priority order**: `cleaned_*.parquet` → `original_*.parquet` → `*.xlsx`
- Always use `DataIngestionManager` for data access, not direct file loading
- Leverage `@st.cache_data(ttl=3600)` for performance optimization

### Provider Recommendation Algorithm
Located in `src/utils/providers.py`, uses multi-factor scoring:
- **Distance weight** (alpha): Geographic proximity via geopy/geodesic
- **Referral count weight** (beta): Historical referral frequency
- **Time decay** (gamma): Recent referral preference
- Algorithm: `score = alpha * (1/distance) + beta * referral_count + gamma * time_factor`

### Geocoding Implementation
- Uses Nominatim (free service) with `RateLimiter(min_delay_seconds=2, max_retries=3)`
- Implements caching via `geocode_address_with_cache()` function
- Address validation through `validate_address()` before geocoding
- Coordinate validation: lat (-90,90), lng (-180,180)
- No API keys required - relies on OpenStreetMap's Nominatim service

## Development Workflows

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run main app
streamlit run app.py

# Run data quality dashboard
streamlit run data_dashboard.py --server.port 8502
```

### Manual Weekly Data Update Workflow
1. **Upload**: Place new Excel files in `data/raw/` (typically `Referrals_App_Full_Contacts.xlsx`)
2. **Clean**: Run `prepare_contacts/contact_cleaning.ipynb` to generate cleaned Parquet files
3. **Refresh**: Use "Update Data" tab in app or call `refresh_data_cache()` to clear Streamlit cache
4. **Validate**: Check "Data Quality" tab for data integrity metrics and ensure new data loaded correctly

### Data Validation
- Use `src/utils/validation.py` to test data ingestion workflow integrity
- Data quality metrics available through `data_dashboard.py`
- Manual verification through app's "Data Quality" tab after each weekly update

## Critical Integration Points

### Streamlit Session State Management
Key session variables in `app.py`:
- `user_lat`, `user_lon`: Geocoded client coordinates
- `last_best`, `last_scored_df`: Cached recommendation results
- Scoring parameters: `alpha`, `beta`, `gamma`, `scoring_type`

### Cross-Module Dependencies
- `src.data.ingestion` → `src.utils.providers` for data loading
- `app.py` imports both data and utils modules
- `data_dashboard.py` uses same ingestion patterns as main app

### File Format Handling
- **Excel**: `pd.read_excel()` with `openpyxl` engine
- **Parquet**: `pd.read_parquet()` with `pyarrow` backend
- **Address formatting**: Concatenated as "Street, City, State Zip"
- **Phone numbers**: Formatted as "(XXX) XXX-XXXX" via `clean_phone_number()`

## Project-Specific Conventions

### Error Handling
- Geocoding errors caught with geopy-specific exceptions: `GeocoderServiceError`, `GeocoderTimedOut`
- Data loading uses graceful fallbacks through `DataIngestionManager._get_best_available_file()`
- Missing data handled with pandas `.fillna("")` for address components

### Performance Optimizations
- Streamlit caching with 1-hour TTL on all data loading functions
- Parquet format preferred for 10x faster loading vs Excel
- Rate-limited geocoding to prevent service blocking
- Lazy loading through `DataIngestionManager.load_data()`
- Weekly data refresh cycle maintains manageable dataset sizes

### UI/UX Patterns
- Always show spinner feedback: `with st.spinner("🔍 Finding your location..."):`
- Use emoji prefixes for visual clarity: "✅", "❌", "🔍", "📊"
- Tab-based navigation in main app: Find Provider | How Selection Works | Data Quality | Update Data
- Sidebar for algorithm parameter tuning (alpha, beta, gamma sliders)
