import pytest

# Importing the top-level app will initialize GEOPY_AVAILABLE flag and
# (if geopy is missing) the fallback `geocode_address_with_cache`.
import app


def test_geocode_fallback_returns_none_when_geopy_missing():
    """Ensure the app provides a fallback geocode function when geopy is not installed.

    This test is environment-sensitive and will be skipped when geopy is available
    (i.e., when the real geocoding implementation is active).
    """
    if getattr(app, "GEOPY_AVAILABLE", False):
        pytest.skip("geopy is installed in this environment; fallback not active")

    # Fallback function should exist and be callable
    assert hasattr(app, "geocode_address_with_cache") and callable(app.geocode_address_with_cache)

    # Calling the fallback should return None (and produce a user-facing message via Streamlit)
    result = app.geocode_address_with_cache("1600 Pennsylvania Ave NW, Washington, DC")
    assert result is None
