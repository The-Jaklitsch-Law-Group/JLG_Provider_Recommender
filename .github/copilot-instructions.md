# JLG Provider Recommender – Copilot Development Guide

## Project Overview

A **Streamlit-based healthcare provider recommendation system** for The Jaklitsch Law Group. The application geocodes client addresses and recommends medical providers based on proximity and referral history.

The **end user** is non-technical and requires a **simple, reliable, and accessible interface**. Data ingestion occurs weekly, while provider searches must remain highly performant.

---

## Architecture & Data Flow

### Core Components

- \`\` – Main Streamlit app with 4 tabs:
  - **Find Provider** (main workflow)
  - **How Selection Works** (explanation)
  - **Data Quality** (metrics and validation results)
  - **Update Data** (manual refresh)
- \`\` – Standalone Streamlit dashboard for monitoring data quality.
- \`\` – Centralized data loading, file registry, and enum-based `DataSource` management.
- \`\` – Recommendation algorithm, geocoding utilities, distance calculation, and scoring logic.
- \`\` – Performance decorators and system health tracking.
- \`\` – Jupyter notebook for weekly preprocessing.

### Data Processing Pipeline

1. **Raw Data**: Excel in `data/raw/` (e.g., `Referrals_App_Full_Contacts.xlsx`).
2. **Cleaned Data**: Parquet in `data/processed/` (e.g., `cleaned_providers.parquet`).
3. **Load Strategy**: Prefer `cleaned_*.parquet` → `original_*.parquet` → raw Excel.
4. **Data Access**: Always via `DataIngestionManager.load_data(DataSource.ENUM_VALUE)`.

### Data Schema

**Raw Excel Input**:

- `case_id: str` (unique)
- `signup_date: date`
- `provider_name: str`
- `provider_address: str`
- `provider_phone: str`
- `direction: enum['inbound','outbound']`

**Processed Parquet Output**:

- `provider_id: str`
- `provider_name: str`
- `address_clean: str`
- `lat: float`
- `lon: float`
- `in_ref_count: int`
- `out_ref_count: int`
- `last_referral_date: date`

---

## Provider Recommendation Algorithm

Located in `src/utils/providers.py`.

### Formula

```python
score = (1 - distance_norm) * w_dist \
      + in_ref_norm * w_in \
      + out_ref_norm * w_out
```

- **Distance normalization**: `distance_norm = min(distance_km / MAX_RADIUS, 1)`
- **Referral normalization**: min–max scaling on current dataset
- **Weights**: `w_dist + w_in + w_out = 1`
  - Defaults: `w_dist = 0.5`, `w_in = 0.3`, `w_out = 0.2`
  - Sliders: range [0,1], auto-normalized
- **Optional ratio feature**: `ratio = out/in capped at RATIO_CAP`

### Tie-Breakers

1. Lower distance
2. Higher inbound referrals
3. Alphabetical provider name

### Exclusions

- Exclude providers beyond `MAX_RADIUS` (default: 50 km)

---

## Geocoding & Distance Calculation

- **Interface**: `Geocoder.get_latlon(address: str) -> tuple[float, float]`
- **Default**: Nominatim (rate-limited, cached)
- Geocoding is provided exclusively by Nominatim / OpenStreetMap (no Google Maps API).
- **Caching**:
  - Geocodes: TTL = 30 days
  - Search results: TTL = 10 minutes
- **Distance**: Vectorized haversine (NumPy) across all providers

---

## Data Cleaning & Validation

- Convert Excel dates to UTC datetime
- Normalize provider names (trim, uppercase)
- Standardize phone numbers (E.164)
- Address normalization via `clean_address_data()`
- Deduplicate providers on `(provider_name, normalized_address)`
- Validation rules:
  - Non-null `case_id`
  - Valid dates ≥ 2010
  - Geocode hit rate ≥ 98%
  - Duplicate rate < 1%

---

## Session State Management

Key variables in `app.py`:

- `user_lat`, `user_lon`
- `last_best`, `last_scored_df`
- Scoring parameters: `w_dist`, `w_in`, `w_out`
- Message deduplication flags (e.g., `time_filter_msg_{start}_{end}`)

---

## UI / UX Requirements

### Find Provider Tab

- **Inputs**: client address form (Street, City, State, Zip)
- **Controls**: sliders for distance vs referral weights
- **Action**: **Search** button
- **Outputs**:
  - **Top Recommendation card** (provider name, distance, score)
  - **Results table** (sortable, downloadable as CSV)

### Data Quality Tab

- Validation metrics: duplicates, geocode success rate, missing fields
- Visual indicators with ✅/❌ icons

### Update Data Tab

- File uploader for new Excel files
- Run cleaning and preprocessing pipeline
- Refresh Streamlit cache

### Accessibility

- All form elements labeled
- Keyboard navigation supported
- Color-contrast compliant

---

## Performance & Monitoring

- Use Streamlit caching (`@st.cache_data`) for ingestion and geocoding
- Prefer Parquet over Excel for 10× faster loading
- Apply performance decorators from `performance.py` to track execution and memory
- Target: **<500 ms** response time for 5,000 providers

---

## Testing Strategy

- **Unit Tests**:
  - Data cleaning functions
  - Geocode caching and fallback
  - Scoring function correctness
- **Integration Tests**:
  - End-to-end provider search workflow
  - Combined ingestion and recommendation
- **Mocks**: Replace geocoding API calls with static fixtures during tests
- **Test Files**:
  - `test_app_functionality.py`
  - `test_deduplication.py`
  - `test_comprehensive.py`

---

## Weekly Data Update Workflow

1. Place new Excel file in `data/raw/`
2. Run `contact_cleaning.ipynb` to produce cleaned Parquet
3. Use the **Update Data** tab or call `refresh_data_cache()`
4. Verify results in the **Data Quality** tab

---

## Error Handling

- **Geocoding**: catch `GeocoderServiceError`, `GeocoderTimedOut`
- **Data loading**: graceful fallback via `DataIngestionManager`
- **Missing fields**: handle with `.fillna('')`
- **Streamlit**: use `handle_streamlit_error(e, context)` for user-friendly error messages

---

## Conventions & Best Practices

- Use emojis for clarity: ✅ ❌ 🔍 📊
- Tab-based navigation with sidebar sliders
- Always clean address data before geocoding
- Cache geocoding results for 24h+ to respect rate limits
- Enforce GitHub Actions CI with `mypy`, `ruff`, and `pytest` on pull requests
