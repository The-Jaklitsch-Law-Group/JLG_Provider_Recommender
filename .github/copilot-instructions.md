# Copilot instructions — JLG Provider Recommender

This file gives precise, repo-specific guidance for an AI coding agent working on this project.

Keep edits small and incremental. Core principles:

- High-level: app is a Streamlit frontend (`app.py`, `data_dashboard.py`) that queries cleaned provider data (Parquet in `data/processed/`) and uses `src/utils/providers.py` + `src/utils/scoring.py` to score recommendations.
- Data flow: raw Excel (data/raw/*.xlsx) → cleaning (`prepare_contacts/contact_cleaning.ipynb`, `src/utils/cleaning.py`) → parquet (`data/processed/*.parquet`) → loaded via `src/data/ingestion.py` (use DataIngestionManager and DataSource enums).
- Geocoding & distance: implemented in `src/utils/geocoding.py` (Nominatim by default; Google Maps optional via env). Distance calculations are vectorized (haversine in NumPy).

Important files to read first:

- `app.py` — streamlit entry; contains session state keys: user_lat/lon, last_best, last_scored_df and UI controls.
- `src/data/ingestion.py` — canonical data-loading helper. Always prefer DataIngestionManager.load_data(DataSource.X).
- `src/utils/providers.py` and `src/utils/scoring.py` — recommendation and scoring logic (weighting, tie-breakers).
- `src/utils/cleaning.py` and `prepare_contacts/contact_cleaning.ipynb` — canonical data-cleaning and deduplication rules.
- `src/utils/geocoding.py` — geocoder interface and caching behavior.
- `tests/` and top-level `test_*.py` — unit and integration test examples and fixtures.

Run / test commands (use workspace root):

- Install deps: pip install -r requirements.txt
- Run app locally: streamlit run app.py
- Run tests: pytest -q (or python -m pytest)

Patterns & conventions (explicit to this repo):

- Centralized ingestion: do not read Parquet/Excel directly in new code; use DataIngestionManager to preserve loading precedence and caching.
- Scoring: follow existing normalized formula in `providers.py` (distance norm + in_ref + out_ref with weights summing to 1). Sliders in the UI normalize weights before calling scoring.
- Caching: heavy ops (geocoding, ingestion) expect Streamlit cache or explicit TTL. Look for `@st.cache_data` and `performance.py` decorators.
- Deduplication key: provider identity is (normalized_name, normalized_address). Cleaning helpers live in `src/utils/cleaning.py`.
- Tests mock external geocoding; follow tests in `tests/test_geocode_fallback.py` for examples.

When changing behavior, update or add tests under `tests/` and run pytest. Prefer small PRs that change one area (ingestion, scoring, UI) and include a test.

If uncertain about data shapes, open `data/processed/` parquet samples (cleaned_*.parquet) or inspect `src/data/ingestion.py` to see expected columns.

If interacting with external APIs (Google Maps), use the existing env variable convention and follow the geocoding fallback tests.

Questions or incomplete areas to confirm with maintainers:

- exact env vars for Google Maps if needed (look for .env usage in repo)
- preferred CI commands beyond pytest (CI config not in repo copy)

After updating this file: ask for feedback which sections were unclear or need more examples.
