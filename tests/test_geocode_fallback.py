"""Test suite for geocoding fallback behavior.

When geopy is not installed, the app should gracefully handle geocoding
requests by providing a fallback function that returns None and notifies
the user.

This test is environment-sensitive and will be skipped when geopy is available.
"""
import pytest

import app


def test_geocode_fallback_returns_none_when_geopy_missing():
    """Ensure the app provides a fallback geocode function when geopy is unavailable.

    When geopy is not installed:
    - GEOPY_AVAILABLE should be False
    - geocode_address_with_cache should exist and be callable
    - Calling it should return None (and show a warning to the user)
    """
    if getattr(app, "GEOPY_AVAILABLE", False):
        pytest.skip("geopy is installed in this environment; fallback not active")

    # Verify fallback exists and is callable
    assert hasattr(app, "geocode_address_with_cache"), "Fallback function should exist"
    assert callable(app.geocode_address_with_cache), "Fallback function should be callable"

    # Calling the fallback should return None
    result = app.geocode_address_with_cache("1600 Pennsylvania Ave NW, Washington, DC")
    assert result is None, "Fallback should return None when geopy unavailable"


def test_geopy_available_flag():
    """Test that GEOPY_AVAILABLE flag is set correctly."""
    assert hasattr(app, "GEOPY_AVAILABLE"), "GEOPY_AVAILABLE flag should be set"
    assert isinstance(app.GEOPY_AVAILABLE, bool), "GEOPY_AVAILABLE should be a boolean"
