"""
Streamlit app entrypoint — Landing page for the Provider Recommender.

This module serves as the lightweight home/landing page in a proper Streamlit
multipage app. It provides clear navigation to the core pages: Search, Data
Dashboard, and Update Data.

**ETL Process Orchestration:**

This module is responsible for triggering the complete ETL pipeline on app startup:

1. **Extract**: Downloads latest data from S3 bucket (CSV or Excel format)
   - Referrals data (inbound/outbound)
   - Preferred providers contact list
   - Handled by src.data.ingestion.DataIngestionManager._get_s3_data()

2. **Transform**: Processes and cleans the raw data
   - Normalizes column names and data types
   - Applies deduplication logic (normalized name + address)
   - Prepares geocoding data
   - Handled by src.data.preparation.process_referral_data()

3. **Load**: Stores processed DataFrames in Streamlit's cache
   - Uses @st.cache_data decorator for performance
   - Invalidates cache based on S3 file modification timestamps
   - Cache TTL: 1 hour (configurable in DataIngestionManager)
   - Handled by src.data.ingestion.DataIngestionManager._load_and_process_data_cached()

**ETL Triggers:**

- **On app startup**: Background thread runs auto_update_data_from_s3()
  - Calls DataIngestionManager.preload_data()
  - Warms cache for immediate app responsiveness
  - Status written to data/processed/s3_auto_update_status.txt

- **Daily refresh (4 AM)**: Main thread checks check_and_refresh_daily_cache()
  - Clears cache and re-runs full ETL if after 4 AM and not refreshed today
  - Ensures app always has fresh data each day

**Data Flow:**

S3 Bucket → auto_update_data_from_s3() → DataIngestionManager.preload_data() →
_load_and_process_data() → _load_and_process_data_cached() (Extract from S3) →
process_referral_data() (Transform) → @st.cache_data (Load) → App usage

**Notes:**

- Heavy logic (data loading, geocoding, scoring) lives in dedicated pages and utils
- Tests expect certain symbols to be exported from this module (filter_providers_by_radius,
  geocode_address_with_cache, etc.) for backward compatibility
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st

st.set_page_config(page_title="JLG Provider Recommender", page_icon=":hospital:", layout="wide")

logger = logging.getLogger(__name__)

from src.app_logic import filter_providers_by_radius  # re-exported for tests

# Try to import the real geocoding helper. Tests expect a fallback
# `geocode_address_with_cache` to exist when `geopy` is not installed.
try:
    import geopy  # noqa: F401 - optional dependency

    GEOPY_AVAILABLE = True

    # Real implementation provided by the utils package
    from src.utils.geocoding import geocode_address_with_cache  # type: ignore
except Exception:  # pragma: no cover - environment dependent
    GEOPY_AVAILABLE = False

    def geocode_address_with_cache(address: str) -> Optional[Tuple[float, float]]:  # type: ignore[override]
        """Fallback geocode function used when geopy isn't available.

        The function intentionally returns None to signal that geocoding
        is unavailable in the current environment. Tests rely on this
        fallback behavior.
        """
        # We use Streamlit to surface a friendly message in the UI.
        st.warning(
            "geopy package not available. Geocoding disabled (returns None). "
            "Install with: pip install geopy"
        )
        return None


# Symbols exported when this module is imported elsewhere (tests)
__all__ = ["filter_providers_by_radius", "geocode_address_with_cache", "GEOPY_AVAILABLE", "show_auto_update_status"]


def show_auto_update_status():
    """
    Display the auto-update status message if available.

    This function can be called from any page to show the result
    of the automatic S3 data update that occurs on app launch.
    """
    # Prefer a status file written by the background updater (safer than
    # accessing session state from background threads). If the file exists,
    # show its content once and then remove it.
    status_file = Path("data/processed/s3_auto_update_status.txt")
    try:
        if status_file.exists():
            text = status_file.read_text(encoding="utf-8").strip()
            if text.startswith("✅"):
                st.success(text)
            elif text.startswith("❌"):
                st.error(text)
            else:
                st.info(text)
            try:
                status_file.unlink()
            except Exception:
                # If deletion fails, ignore — it's just a convenience file
                pass
            return
    except Exception:
        # If anything goes wrong reading the file, fall back silently
        return


def auto_update_data_from_s3():
    """
    Automatically trigger the ETL process on app launch.

    This function orchestrates the complete ETL pipeline:
    1. **Extract**: Downloads latest data from S3 (CSV or Excel format)
    2. **Transform**: Processes and cleans data via src.data.preparation.process_referral_data
    3. **Load**: Stores processed DataFrames in Streamlit's st.cache_data for app usage

    The ETL process is handled by DataIngestionManager.preload_data() which:
    - Downloads referrals and preferred providers from S3
    - Applies data transformations (normalization, deduplication, geocoding prep)
    - Caches results in st.cache_data with S3 metadata-based invalidation
    - Warms the cache for immediate app responsiveness
    
    If S3 is not configured, falls back to local parquet cache files.

    This function runs once per session in a background thread to avoid blocking
    the initial page render. Daily refresh checks are handled separately in the
    main thread via check_and_refresh_daily_cache().

    Status is written to data/processed/s3_auto_update_status.txt for UI display.
    """
    # Background worker: avoid using Streamlit APIs here (no st.* calls).
    # Write a status file into data/processed/ that the main thread can read.
    status_file = Path("data/processed/s3_auto_update_status.txt")
    try:
        from src.data.ingestion import get_data_manager

        data_manager = get_data_manager()

        # Check if S3 is configured
        from src.utils.config import is_api_enabled
        if not is_api_enabled("s3"):
            logger.info("S3 not configured - using local cache files if available")
            try:
                status_file.parent.mkdir(parents=True, exist_ok=True)
                status_file.write_text(
                    "ℹ️ S3 not configured — using local cache files. "
                    "Configure S3 in .streamlit/secrets.toml for production use.", 
                    encoding="utf-8"
                )
            except Exception:
                pass
            # Still try to preload data from local files
            try:
                data_manager.preload_data()
            except Exception as e:
                logger.warning(f"Failed to preload data from local files: {e}")
            return

        # Trigger the ETL process (Extract → Transform → Load)
        logger.info("Starting ETL process: Extract from S3 → Transform → Load to cache...")
        try:
            # This triggers the full ETL pipeline via DataIngestionManager
            data_manager.preload_data()
            msg = "✅ ETL complete: Data extracted from S3, transformed, and loaded to cache"
            logger.info(msg)
            try:
                status_file.parent.mkdir(parents=True, exist_ok=True)
                status_file.write_text(msg, encoding="utf-8")
            except Exception:
                logger.exception("Failed to write ETL status file")
        except Exception as e:
            logger.exception(f"ETL process failed: {e}")
            try:
                status_file.parent.mkdir(parents=True, exist_ok=True)
                status_file.write_text(f"❌ ETL process failed: {e}", encoding="utf-8")
            except Exception:
                pass

    except ImportError as e:
        logger.info(f"Data ingestion module not available - skipping ETL process: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during ETL process: {e}")
        try:
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(f"❌ ETL process failed: {e}", encoding="utf-8")
        except Exception:
            pass


# Build navigation pages but exclude this module (app.py) to avoid
# re-importing and creating an import/recursion loop when Streamlit
# loads the selected page.
_current_file = Path(__file__).name
_nav_items = [
    ("pages/1_🔎_Search.py", "Search", "🔎"),
    ("pages/2_📄_Results.py", "Results", "📄"),
    ("pages/10_🛠️_How_It_Works.py", "How It Works", "🛠️"),
    ("pages/20_📊_Data_Dashboard.py", "Data Dashboard", "📊"),
    ("pages/30_🔄_Update_Data.py", "Update Data", "🔄"),
]


def _build_and_run_app():
    """Build navigation pages and trigger ETL processes on app startup.

    This function orchestrates two ETL-related processes:
    
    1. **Daily cache refresh check**: Runs synchronously on every app load.
       - If it's after 4 AM and cache hasn't been refreshed today, clears cache
       - Then re-runs the full ETL pipeline to get fresh data from S3
    
    2. **Background ETL on app launch**: Runs asynchronously in a background thread.
       - Triggers the complete ETL pipeline (Extract → Transform → Load)
       - Warms the cache without blocking the initial page render
       - Status is written to a file for UI display

    The ETL pipeline is handled by src.data.ingestion.DataIngestionManager which:
    - Extracts data from S3 (CSV or Excel format)
    - Transforms data via src.data.preparation.process_referral_data
    - Loads processed DataFrames into Streamlit's st.cache_data

    Note: This is intentionally encapsulated so importing `app` from a page module
    does not execute the navigation or ETL logic (which would cause duplicate rendering).
    """

    # Check for daily refresh on each app load (Streamlit reruns frequently)
    # This may trigger a full ETL pipeline if it's time for daily refresh
    try:
        from src.data.ingestion import get_data_manager
        data_manager = get_data_manager()
        refreshed = data_manager.check_and_refresh_daily_cache()
        if refreshed:
            logger.info("Daily cache refresh triggered full ETL pipeline")
    except Exception as e:
        logger.warning(f"Could not check daily refresh on app load: {e}")

    # Only include pages whose path does not point to this module file.
    nav_pages = [st.Page(path, title=title, icon=icon) for path, title, icon in _nav_items if path != _current_file]

    import threading

    # Run ETL pipeline on app launch (before navigation setup) in a background thread
    # so it doesn't block Streamlit's startup or the initial page render.
    try:
        thread = threading.Thread(target=auto_update_data_from_s3, daemon=True)
        thread.start()
    except Exception:
        # Fallback to synchronous call if threading is unavailable for any reason
        auto_update_data_from_s3()

    pg = st.navigation(nav_pages)
    pg.run()


if __name__ == "__main__":
    _build_and_run_app()
