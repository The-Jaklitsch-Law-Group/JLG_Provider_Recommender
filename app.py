import streamlit as st
from src.app_logic import filter_providers_by_radius  # re-export for tests

# Maintain backward-compatible geocoding fallback expected by tests
try:
    import geopy  # noqa: F401

    GEOPY_AVAILABLE = True
    from src.utils.geocoding import geocode_address_with_cache  # real implementation
except Exception:  # pragma: no cover - environment dependent
    GEOPY_AVAILABLE = False

    def geocode_address_with_cache(address: str):  # type: ignore
        st.warning(
            "geopy package not available. Geocoding disabled (returns None). Install with: pip install geopy"
        )
        return None

st.set_page_config(page_title="Provider Recommender", page_icon=":hospital:", layout="wide")

__all__ = ["filter_providers_by_radius", "geocode_address_with_cache", "GEOPY_AVAILABLE"]

st.title("Provider Recommender")
st.info("Use the Search page to begin.")

if st.button("Go to Search", type="primary"):
    try:
        st.switch_page("pages/1_Search.py")
    except Exception:
        st.warning("Switch page not available in this environment.")