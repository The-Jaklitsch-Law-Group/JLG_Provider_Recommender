# JLG Provider Recommender

Small Streamlit app and utilities to recommend legal service providers using cleaned provider/referral data.

This repository contains data preparation, geocoding, scoring and a Streamlit front-end for exploring and recommending providers.

## Features

- Load and validate cleaned provider and referral data (Parquet/Excel).
- Vectorized distance calculations and geocoding with fallback support.
- Configurable scoring (distance / outbound referrals / inbound referrals).
- Streamlit UI with search, filters, rankings and data quality/dashboard pages.

## Quick start

Prerequisites

- Python 3.10+ (tested on 3.10 - 3.12)
- A working virtual environment is recommended

Install dependencies

```bash
pip install -r requirements.txt
```

Run the Streamlit app

```bash
# Primary entry (most common in this repo)
streamlit run Main_Page.py

# If you have a different entrypoint (some setups use Main_Page.py):
# streamlit run Main_Page.py
```

Run tests

```bash
pytest -q
```

## Project layout (high level)

- `Main_Page.py` - Streamlit front-end entry used in this repo.
- `pages/` - additional Streamlit multi-page views (search, results, data quality, etc.).
- `src/` - application logic and utilities
  - `src/data/` - ingestion and preparation helpers
  - `src/utils/` - cleaning, geocoding, scoring, provider helpers
- `data/` - sample or processed data (raw Excel files and processed Parquet)
- `prepare_contacts/` - notebooks used for cleaning/preparing source contact spreadsheets
- `tests/` - pytest test suite and fixtures
- `assets/` - images and logo helpers

## Data flow & conventions

- Raw Excel files live under `data/raw/`. Cleaned outputs are stored in `data/processed/` as Parquet files.
- Use the ingestion helpers in `src/data/ingestion.py` to load data consistently (this preserves caching and loading precedence).
- Deduplication and cleaning routines are in `src/utils/cleaning.py` and related helpers.
- Geocoding defaults to Nominatim but supports optional Google Maps API via environment variables (see `src/utils/geocoding.py`).

## Configuration and environment

- Environment variables (optional):
  - `GOOGLE_MAPS_API_KEY` (only if you want to enable Google geocoding fallback)

## Developer notes

- Tests mock external geocoding providers — run tests offline.
- Keep heavy operations cached where appropriate (the Streamlit app uses `st.cache_data` for expensive loads).
- When adding data-loading logic, prefer the existing ingestion helpers rather than reading Parquet/Excel directly.

## Contributing

- Fork, add small focused changes, include/update tests, and open a PR against the `dev` branch.

## License

See `LICENSE` for license details.

---