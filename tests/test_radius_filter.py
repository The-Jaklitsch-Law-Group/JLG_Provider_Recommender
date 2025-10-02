"""Test suite for radius-based provider filtering.

Tests verify that the filter correctly keeps providers within the specified
distance threshold and excludes those beyond it.
"""
import pandas as pd
import pytest

from src.app_logic import filter_providers_by_radius


@pytest.fixture
def providers_at_various_distances():
    """Create providers at known distances (in miles)."""
    # Approximate km to miles conversion
    km_to_miles = 0.621371
    distances_km = [10, 30, 40, 100]
    distances_miles = [d * km_to_miles for d in distances_km]

    return pd.DataFrame(
        {"Full Name": [f"Provider_{i}" for i in range(len(distances_miles))], "Distance (Miles)": distances_miles}
    )


def test_filter_providers_by_radius_50km(providers_at_various_distances):
    """Test filtering providers within 50km (~31 miles)."""
    max_radius_miles = 50 * 0.621371  # ~31 miles

    result = filter_providers_by_radius(providers_at_various_distances, max_radius_miles)

    # Should keep providers at 10, 30, 40 km (all within 50km)
    assert len(result) == 3, "Should keep 3 providers within 50km"
    assert list(result["Full Name"]) == ["Provider_0", "Provider_1", "Provider_2"]
    assert all(result["Distance (Miles)"] <= max_radius_miles)


def test_filter_providers_by_radius_20km(providers_at_various_distances):
    """Test filtering providers within 20km (~12.4 miles)."""
    max_radius_miles = 20 * 0.621371  # ~12.4 miles

    result = filter_providers_by_radius(providers_at_various_distances, max_radius_miles)

    # Should keep only the provider at 10 km
    assert len(result) == 1, "Should keep only 1 provider within 20km"
    assert list(result["Full Name"]) == ["Provider_0"]


def test_filter_providers_empty_dataframe():
    """Test filtering an empty DataFrame."""
    df = pd.DataFrame(columns=["Full Name", "Distance (Miles)"])

    result = filter_providers_by_radius(df, 50.0)

    assert result.empty, "Should return empty DataFrame"
    assert list(result.columns) == ["Full Name", "Distance (Miles)"]


def test_filter_providers_all_beyond_radius():
    """Test filtering when all providers are beyond the radius."""
    df = pd.DataFrame({"Full Name": ["Far Away", "Very Far"], "Distance (Miles)": [100.0, 200.0]})

    result = filter_providers_by_radius(df, 10.0)

    assert result.empty, "Should return empty DataFrame when all providers beyond radius"
