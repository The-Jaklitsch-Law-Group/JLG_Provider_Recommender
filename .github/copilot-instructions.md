# Copilot instructions — JLG Provider Recommender

This concise guide helps an AI coding agent become productive quickly in this repo. Keep edits small, prefer the canonical helpers, and include tests for behavioral changes.

Big picture

- UI: Streamlit app. Entry points are `app.py` and `pages/*.py` (notably `pages/1_🔎_Search.py` and `pages/20_📊_Data_Dashboard.py`). Session state keys live in `app.py` (examples: `user_lat`, `user_lon`, `last_best`, `last_scored_df`).
- Business logic: `src/app_logic.py` orchestrates flows. Helpers and domain logic live in `src/utils/` (e.g., `geocoding.py`, `scoring.py`, `providers.py`, `cleaning.py`, `io_utils.py`).
- Data flow: raw Excel in `data/raw/` → cleaning in `prepare_contacts/*.ipynb` + `src/utils/cleaning.py` → outputs in `data/processed/*.parquet` and `data/processed/geocode_cache.json` → loaded using `src/data/ingestion.py`.

Canonical contracts and conventions (do these exactly)

- Ingestion: ALWAYS use `DataIngestionManager.load_data(DataSource.X)` from `src/data/ingestion.py`. This enforces precedence, caching, and expected transforms — do not read Parquet/Excel directly in new code.
- Scoring & providers: scoring logic is in `src/utils/scoring.py` and `src/utils/providers.py`. Scores are normalized and combined; UI sliders normalize weight inputs before scoring. Follow the existing functions and normalized formula rather than inventing new score combinations.
- Geocoding: use `src/utils/geocoding.py`. Default geocoder is Nominatim; Google Maps is optional and guarded by environment variables. Geocoding results are cached in `data/processed/geocode_cache.json` — update cache handling when changing geocode behavior.
- Distance calculations: implemented vectorized (NumPy) haversine computations — prefer batch/vectorized operations for performance.
- Deduplication: canonical provider identity is (normalized_name, normalized_address) — see `src/utils/cleaning.py` and `prepare_contacts/contact_cleaning.ipynb` for exact transformations.
- Caching: heavy operations use Streamlit cache decorators (`@st.cache_data`) or local cache files; respect these to avoid expensive re-runs in the UI.

Tests & examples

- Run tests: `pytest -q` (from repo root). Use `tests/conftest.py` fixtures. Many tests show how to mock external services:
  - `tests/test_geocode_fallback.py` demonstrates geocoding fallbacks and mocking patterns.
  - `tests/test_s3_client.py` shows S3 mocks for `src/utils/s3_client.py`.
- When modifying ingestion, scoring, or geocoding, add or update tests and run the relevant test files locally (targeted runs are faster).

Developer commands (repo root)

- Install deps: pip install -r requirements.txt
- Run app: streamlit run app.py
- Run tests: pytest -q
- Lint: flake8
- Format: black . --line-length=120 && isort . --profile=black --line-length=120
- Pre-commit: pre-commit run --all-files

Integration & environment notes

- S3: optional integration in `src/utils/s3_client.py`. Tests mock S3; to enable in dev, supply credentials and mimic test mocks as needed.
- Google Maps: controlled by env vars in `src/utils/geocoding.py`. If you add keys, update tests that assert fallback behavior.
- Data samples: Parquet files in `data/processed/` (e.g., `cleaned_all_referrals.parquet`) are useful for offline experiments — but load them through the ingestion manager in code.

Practical editing rules

- Keep PRs small and focused (one area: ingestion, scoring, or UI). Include unit tests for changed behavior.
- When adding data sources, add a `DataSource` enum entry and use `DataIngestionManager` so caching and precedence remain correct.
- If changing geocoding: update cache handling (`data/processed/geocode_cache.json`) and associated tests (`tests/test_geocode_fallback.py`).

Files to read first (priority)

1. `app.py`
2. `src/data/ingestion.py`
3. `src/utils/geocoding.py`
4. `src/utils/scoring.py` and `src/utils/providers.py`
5. `src/utils/cleaning.py` and `prepare_contacts/contact_cleaning.ipynb`

If anything here is unclear or you want more examples (e.g., exact session keys, example test patterns, or sample DataSource values), tell me which section and I'll expand it.
