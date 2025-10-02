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

st.title("🏥 Provider Recommender")
st.markdown(
    """
    **Smart provider recommendations for optimal client care**
    
    This system helps you find the best legal service provider for your clients by intelligently 
    balancing proximity, workload distribution, and referral relationships.
    """
)

st.divider()

st.subheader("🚀 Getting Started")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔍 Search")
    st.write(
        """
        Find the best provider based on your client's address and your preferences.
        
        **Quick and easy:**
        - Enter client address
        - Set search radius
        - Get instant recommendations
        """
    )
    st.page_link("pages/1_Search.py", label="Start Searching", icon="🔎")

with col2:
    st.markdown("### 📊 Dashboard")
    st.write(
        """
        Explore provider and referral data with interactive visualizations.
        
        **Data insights:**
        - View all providers
        - Analyze referral patterns
        - Check data quality
        """
    )
    st.page_link("pages/21_Data_Dashboard.py", label="View Dashboard", icon="📊")

with col3:
    st.markdown("### 🔄 Update Data")
    st.write(
        """
        Keep your provider database current with the latest information.
        
        **Data management:**
        - Refresh provider data
        - Update referral counts
        - Maintain accuracy
        """
    )
    st.page_link("pages/30_Update_Data.py", label="Update Data", icon="🔄")

st.divider()

st.subheader("📚 Learn More")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.page_link("pages/10_How_It_Works.py", label="📘 How It Works", icon="📘")
    st.caption("Learn about the recommendation algorithm and scoring system")

with info_col2:
    st.page_link("pages/20_Data_Quality.py", label="🧪 Data Quality", icon="🧪")
    st.caption("Monitor data quality and system health")
