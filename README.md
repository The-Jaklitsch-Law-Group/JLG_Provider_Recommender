# JLG Provider Recommender

A Streamlit application that intelligently recommends legal service providers based on geographic proximity, workload distribution, and referral relationships. Built for The Jaklitsch Law Group to optimize client-provider matching and maintain balanced referral networks.

## Overview

The JLG Provider Recommender analyzes historical referral data to suggest the best provider for a client based on:
- **Geographic proximity** - Measured via haversine distance calculations
- **Workload balance** - Considers current referral volume to avoid overloading providers
- **Referral relationships** - Favors mutual referral partnerships
- **Provider preferences** - Optional weighting for preferred providers

The system processes raw Excel exports from Filevine, cleans and geocodes provider data, then applies a configurable scoring algorithm to rank providers. Users can adjust weighting factors via interactive sliders to match different referral scenarios.

## Features

- **Smart Data Loading** - Data automatically synced from AWS S3 with auto-update on app launch (S3-only mode)
- **AWS S3 Integration** - Cloud-native data workflows with **automatic updates** - local parquet files deprecated
- **Accurate Distance Calculation** - Vectorized haversine formula for Earth-curvature-aware measurements
- **Flexible Scoring** - Configurable weights for distance, outbound referrals, inbound referrals, and preferred status
- **Interactive UI** - Multi-page Streamlit app with search, results visualization, and data dashboards
- **Data Quality Tools** - Built-in validation, missing geocode detection, and data freshness monitoring
- **Comprehensive Testing** - 79+ pytest tests covering scoring, distance calculation, validation, data cleaning, and S3 operations

## Quick Start

> **🔴 BREAKING CHANGE:** As of version 2.1+, S3 configuration is **strictly required**. All local parquet file fallbacks have been removed.  
> See [S3 Migration Guide](docs/S3_MIGRATION_GUIDE.md) for detailed setup instructions.

### Prerequisites

- Python 3.10+ (tested on 3.10-3.12)
- Virtual environment recommended (venv, conda, etc.)
- **AWS S3 access configured** (required for data loading - see Configuration section below)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/The-Jaklitsch-Law-Group/JLG_Provider_Recommender.git
cd JLG_Provider_Recommender
```

2. Install dependencies (runtime):
```bash
pip install -r requirements.txt
```

For development and running tests, also install dev dependencies:
```bash
pip install -r requirements-dev.txt
```

### Running the Application

Launch the Streamlit app:
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`. **If S3 is configured, the app will automatically update data from S3 on launch.** Navigate through the pages:
- **🔎 Search** - Enter client address and configure search parameters (landing page)
- **📄 Results** - View ranked provider recommendations
- **📊 Data Dashboard** - Explore referral patterns and data quality
- **🔄 Update Data** - Re-process raw Excel files into cleaned datasets
- **🛠️ How It Works** - Detailed explanation of the scoring algorithm

### Running Tests

Execute the test suite (70 tests covering scoring, validation, distance calculation, and data cleaning):
```bash
pytest tests/ -v
```

Run with coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
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
│   ├── raw/                       # (gitignored) Excel exports from Filevine
│   │   └── Referrals_App_Full_Contacts.xlsx
│   └── processed/                 # (gitignored) Cleaned Parquet cache files
│       ├── cleaned_all_referrals.parquet        # Auto-generated from S3
│       ├── cleaned_inbound_referrals.parquet    # Auto-generated from S3
│       ├── cleaned_outbound_referrals.parquet   # Auto-generated from S3
│       └── cleaned_preferred_providers.parquet  # Auto-generated from S3
├── prepare_contacts/              # Jupyter notebooks for data exploration
│   ├── contact_cleaning.ipynb     # Referral data cleaning workflow
│   └── Cleaning_Preferred_Providers.ipynb
├── tests/                         # Comprehensive pytest suite (70+ tests)
│   ├── fixtures/                  # Small sample data for testing
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

### 1. Data Pipeline

**S3 → Auto-Download → Cleaned Data → Application**

1. **Data Storage**: Referral data stored in AWS S3 bucket
2. **Auto-Update**: On app launch, latest files are automatically downloaded from S3
3. **Data Cleaning** (via `src/data/preparation.py`):
   - Split into inbound/outbound referrals
   - Normalize addresses and phone numbers
   - Parse and validate coordinates
   - Deduplicate providers using (normalized_name, normalized_address)
   - Fill missing geocodes via Nominatim/Google Maps
4. **Optimization**: Save as Parquet files in `data/processed/` (local cache)
5. **Application Loading**: Use `DataIngestionManager` to load from local cache

**Note:** Local parquet files in `data/processed/` are now cache files created from S3 data.
They are not checked into the repository and will be auto-generated on first run.

### 2. Geocoding Strategy

- **Primary**: OpenStreetMap Nominatim (free, no API key required)
- **Fallback**: Google Maps API (optional, set `GOOGLE_MAPS_API_KEY` env variable)
- **Caching**: 24-hour cache to minimize API calls and improve performance
- **Validation**: Coordinate range checking (-90 to 90 latitude, -180 to 180 longitude)

### 3. Scoring Algorithm

The recommendation score combines multiple normalized factors:

```
Score = α × Distance_norm + β × Outbound_norm + γ × Inbound_norm + δ × Preferred_norm
```

Where:
- **α, β, γ, δ** = User-configured weights (automatically normalized to sum to 1.0)
- **Distance_norm** = Inverted distance normalization (0-1, closer is higher/better)
- **Outbound_norm** = Direct referral count normalization (higher count = higher score = better)
- **Inbound_norm** = Min-max normalized inbound referrals (higher = better)
- **Preferred_norm** = Binary preferred provider flag (increases score for preferred providers)
- **Higher scores indicate better matches**

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

### S3 Configuration (Required)

**🔴 IMPORTANT: The app now requires S3 configuration to load data. Local parquet files have been deprecated and removed.**

Configure AWS S3 credentials in `.streamlit/secrets.toml`:

```toml
[s3]
aws_access_key_id = "your-access-key-id"
aws_secret_access_key = "your-secret-access-key"
bucket_name = "your-bucket-name"
region_name = "us-east-1"  # optional, defaults to us-east-1
referrals_folder = "referrals"  # S3 prefix/folder for referrals data
preferred_providers_folder = "preferred_providers"  # S3 prefix/folder for providers
```

**First-time setup:**
1. Create `.streamlit/secrets.toml` with your S3 credentials
2. Upload your referral data files to S3 (CSV or Excel format)
3. Run the app - it will auto-download and process data on launch
4. Or navigate to **🔄 Update Data** page to manually pull from S3

**Note:** S3 is the only supported data source. No local fallback options are available.

### Environment Variables (Optional)

- `GOOGLE_MAPS_API_KEY` - Enable Google Maps geocoding fallback (Nominatim used by default)

### Streamlit Configuration

The app uses Streamlit's session state to preserve:
- User location (`user_lat`, `user_lon`)
- Last search results (`last_best`, `last_scored_df`)
- Search preferences (weights, filters)

Configure secrets in `.streamlit/secrets.toml` (see `docs/API_SECRETS_GUIDE.md` for details):
- AWS S3 credentials for automatic data pulls
- Google Maps API key for enhanced geocoding
- Database connection strings (if needed)

📚 **Documentation**: See `docs/AUTO_S3_UPDATE.md` for details on the automatic S3 data update feature.

### Data Refresh

To update provider data:

**AWS S3 (Required - Recommended for All Deployments)**
1. Upload latest referral files to your S3 bucket (CSV or Excel format)
2. **Option A - Automatic:** Restart the app - it will auto-download on launch
3. **Option B - Manual:** Navigate to **🔄 Update Data** page and click "Pull Latest from S3"
4. Data is automatically downloaded, cleaned, and cached locally

**Local File Upload (Alternative)**
1. Navigate to **🔄 Update Data** page in the app
2. Upload CSV/Excel file using the file uploader
3. Data is automatically processed and cached

**Note:** Local parquet files in `data/processed/` are deprecated and removed from version control.
The app now relies exclusively on S3 as the canonical data source.

## Testing

The project includes a comprehensive test suite with 79+ tests:

### Test Coverage
- **Scoring Algorithm** (`test_scoring.py`) - Core recommendation logic, edge cases
- **Validation** (`test_validation.py`) - Address, coordinate, phone number validation
- **Distance Calculation** (`test_distance_calculation.py`) - Haversine accuracy, symmetry
- **Data Cleaning** (`test_cleaning.py`) - Address normalization, state mapping, deduplication
- **Geocoding** (`test_geocode_fallback.py`) - Fallback behavior when geopy unavailable
- **Data Preparation** (`test_data_preparation.py`) - Full pipeline processing
- **Radius Filtering** (`test_radius_filter.py`) - Geographic filtering logic
- **S3 Integration** (`test_s3_client.py`) - AWS S3 data access, mocking, error handling

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

### Common Issues

**Geocoding fails or returns None**:
- Check internet connection (Nominatim requires network access)
- Verify address format (street, city, state, zip all required)
- Consider adding Google Maps API key for fallback

**Slow data loading**:
- Ensure Parquet files exist in `data/processed/` (10x faster than Excel)
- Check Streamlit cache isn't being invalidated frequently
- Verify file sizes are reasonable (<100MB recommended)

**No providers returned**:
- Lower minimum referral threshold
- Increase maximum radius
- Check that provider data has valid coordinates
- Verify filters aren't too restrictive

**Test failures**:
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version (3.10+ required)
- Review test output for specific assertion failures
- Run with `-v` flag for detailed output

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**: Follow code style and best practices
4. **Add/update tests**: Ensure all tests pass (`pytest tests/`)
5. **Run pre-commit hooks**: `pre-commit run --all-files`
6. **Commit your changes**: Use clear, descriptive commit messages
7. **Push to your fork**: `git push origin feature/your-feature-name`
8. **Open a Pull Request**: Target the `dev` branch, not `main`

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
