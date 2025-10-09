"""
Streamlit app entrypoint — Landing page for the Provider Recommender.

This module now serves as the lightweight home/landing page in a proper
Streamlit multipage app. It provides clear navigation to the core pages:
Search, Data Dashboard, and Update Data. Heavy logic (data loading,
geocoding, scoring) lives in the dedicated pages and utils.

Note: We still expose a few symbols for tests that import from `app.py`.
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
except Exception as exc:  # pragma: no cover - environment dependent
    GEOPY_AVAILABLE = False

    def geocode_address_with_cache(address: str) -> Optional[Tuple[float, float]]:  # type: ignore[override]
        """Fallback geocode function used when geopy isn't available.

        The function intentionally returns None to signal that geocoding
        is unavailable in the current environment. Tests rely on this
        fallback behavior.
        """
        # We use Streamlit to surface a friendly message in the UI.
        st.warning("geopy package not available. Geocoding disabled (returns None). " "Install with: pip install geopy")
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
    Automatically update data from S3 on app launch if configured.

    This function runs once per session and updates the data files
    from S3 if S3 is properly configured. It runs silently in the
    background without blocking the UI.
    """
    # Background worker: avoid using Streamlit APIs here (no st.* calls).
    # Write a status file into data/processed/ that the main thread can read.
    status_file = Path("data/processed/s3_auto_update_status.txt")
    try:
        from src.data import (
            process_and_save_cleaned_referrals,
            process_and_save_preferred_providers,
            refresh_data_cache,
        )
        from src.utils.s3_client_optimized import S3DataClient

        s3_client = S3DataClient()
        if not s3_client.is_configured():
            logger.info("S3 not configured - skipping auto data update")
            try:
                status_file.parent.mkdir(parents=True, exist_ok=True)
                status_file.write_text("ℹ️ S3 not configured — auto-update skipped")
            except Exception:
                pass
            return

        issues = s3_client.validate_configuration()
        if issues:
            logger.info(f"S3 configuration issues detected - skipping auto data update: {issues}")
            try:
                status_file.parent.mkdir(parents=True, exist_ok=True)
                status_file.write_text("⚠️ S3 configuration issues — auto-update skipped")
            except Exception:
                pass
            return

        latest_files = s3_client.download_latest_files_batch(["referrals", "preferred_providers"])

        updated_files = []

        referrals_result = latest_files.get("referrals")
        if referrals_result:
            referrals_bytes, referrals_name = referrals_result
            try:
                process_and_save_cleaned_referrals(referrals_bytes, Path("data/processed"), filename=referrals_name)
                updated_files.append(f"referrals ({referrals_name})")
            except Exception as e:
                logger.error(f"Failed to process referrals data: {e}")

        providers_result = latest_files.get("preferred_providers")
        if providers_result:
            providers_bytes, providers_name = providers_result
            try:
                process_and_save_preferred_providers(providers_bytes, Path("data/processed"), filename=providers_name)
                updated_files.append(f"providers ({providers_name})")
            except Exception as e:
                logger.error(f"Failed to process providers data: {e}")

        if updated_files:
            try:
                refresh_data_cache()
            except Exception:
                logger.exception("Failed to refresh data cache after auto-update")
            msg = f"✅ Data automatically updated from S3: {', '.join(updated_files)}"
            logger.info(msg)
            try:
                status_file.parent.mkdir(parents=True, exist_ok=True)
                status_file.write_text(msg)
            except Exception:
                logger.exception("Failed to write s3 auto-update status file")
        else:
            logger.info("S3 auto-update: No files found to update")
            try:
                status_file.parent.mkdir(parents=True, exist_ok=True)
                status_file.write_text("ℹ️ S3 auto-update ran: no files to process")
            except Exception:
                pass

    except ImportError as e:
        logger.info(f"S3 client not available - skipping auto data update: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during S3 auto-update: {e}")
        try:
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(f"❌ S3 auto-update failed: {e}")
        except Exception:
            pass


# Build navigation pages but exclude this module (app.py) to avoid
# re-importing and creating an import/recursion loop when Streamlit
# loads the selected page.
_current_file = Path(__file__).name
_nav_items = [
    ("pages/0_🏠_home.py", "Home", "🏠"),
    ("pages/1_🔎_Search.py", "Search", "🔎"),
    ("pages/2_📄_Results.py", "Results", "📄"),
    ("pages/10_🛠️_How_It_Works.py", "How It Works", "🛠️"),
    ("pages/20_📊_Data_Dashboard.py", "Data Dashboard", "📊"),
    ("pages/30_🔄_Update_Data.py", "Update Data", "🔄"),
]

# Only include pages whose path does not point to this module file.
nav_pages = [st.Page(path, title=title, icon=icon) for path, title, icon in _nav_items if path != _current_file]

import threading

# Run auto-update on app launch (before navigation setup) in a background thread
# so it doesn't block Streamlit's startup or the initial page render.
try:
    thread = threading.Thread(target=auto_update_data_from_s3, daemon=True)
    thread.start()
except Exception:
    # Fallback to synchronous call if threading is unavailable for any reason
    auto_update_data_from_s3()

pg = st.navigation(nav_pages)
pg.run()
