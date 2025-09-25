"""
Streamlit app entrypoint — Landing page for the Provider Recommender.

This module now serves as the lightweight home/landing page in a proper
Streamlit multipage app. It provides clear navigation to the core pages:
Search, Data Dashboard, and Update Data. Heavy logic (data loading,
geocoding, scoring) lives in the dedicated pages and utils.

Note: We still expose a few symbols for tests that import from `app.py`.
"""

from __future__ import annotations

from typing import Optional, Tuple
import streamlit as st

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


st.set_page_config(page_title="Provider Recommender", page_icon=":hospital:", layout="wide")

# Symbols exported when this module is imported elsewhere (tests)
__all__ = ["filter_providers_by_radius", "geocode_address_with_cache", "GEOPY_AVAILABLE"]

st.title("Provider Recommender")
st.caption("Choose where to start.")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Search")
    st.write("Find the best provider based on address and referral data.")
    st.page_link("pages/1_Search.py", label="Open Search", icon="🔎")

with col2:
    st.subheader("Data Dashboard")
    st.write("Explore cleaned provider and referral data.")
    st.page_link("pages/20_Data_Dashboard.py", label="Open Dashboard", icon="📊")

with col3:
    st.subheader("Update Data")
    st.write("Refresh processed data using the current pipeline.")
    st.page_link("pages/30_Update_Data.py", label="Open Update Data", icon="🔄")

st.divider()
st.page_link("pages/10_How_It_Works.py", label="How it works", icon="📘")
    # Deprecated: Data quality page removed (duplicate). Previously: "pages/20_Data_Quality.py"
