"""Test suite for distance calculation using haversine formula.

Tests verify accurate distance calculations between geographic coordinates.
"""
import pandas as pd
import pytest

from src.utils.scoring import calculate_distances


class TestCalculateDistances:
    """Tests for haversine distance calculation."""

    def test_distance_to_same_location(self):
        """Test that distance to same location is zero."""
        df = pd.DataFrame({"Latitude": [40.7128], "Longitude": [-74.0060]})

        distances = calculate_distances(40.7128, -74.0060, df)

        assert len(distances) == 1
        assert distances[0] is not None
        assert distances[0] < 0.01, "Distance to same point should be nearly zero"

    def test_known_distance_nyc_to_philadelphia(self):
        """Test distance calculation between NYC and Philadelphia (~80 miles)."""
        # New York City: 40.7128° N, 74.0060° W
        # Philadelphia: 39.9526° N, 75.1652° W
        # Actual distance: ~80-85 miles

        df = pd.DataFrame({"Latitude": [39.9526], "Longitude": [-75.1652]})

        distances = calculate_distances(40.7128, -74.0060, df)

        assert len(distances) == 1
        assert distances[0] is not None
        assert 75 < distances[0] < 90, f"Expected ~80 miles, got {distances[0]:.1f}"

    def test_known_distance_baltimore_to_dc(self):
        """Test distance calculation between Baltimore and DC (~35-40 miles)."""
        # Baltimore: 39.2904° N, 76.6122° W
        # Washington DC: 38.9072° N, 77.0369° W

        df = pd.DataFrame({"Latitude": [38.9072], "Longitude": [-77.0369]})

        distances = calculate_distances(39.2904, -76.6122, df)

        assert len(distances) == 1
        assert distances[0] is not None
        assert 30 < distances[0] < 45, f"Expected ~35-40 miles, got {distances[0]:.1f}"

    def test_multiple_providers(self):
        """Test distance calculation for multiple providers."""
        df = pd.DataFrame(
            {
                "Latitude": [40.7128, 39.9526, 39.2904],  # NYC, Philly, Baltimore
                "Longitude": [-74.0060, -75.1652, -76.6122],
            }
        )

        # Calculate from NYC
        distances = calculate_distances(40.7128, -74.0060, df)

        assert len(distances) == 3
        assert all(d is not None for d in distances)
        assert distances[0] < 1, "Distance to NYC (same location) should be very small"
        assert 75 < distances[1] < 90, "Distance to Philadelphia should be ~80 miles"
        assert 160 < distances[2] < 180, "Distance to Baltimore should be ~170 miles"

    def test_invalid_coordinates_return_none(self):
        """Test that invalid coordinates return None."""
        df = pd.DataFrame({"Latitude": [float("nan"), 40.7128], "Longitude": [-74.0060, float("nan")]})

        distances = calculate_distances(40.7128, -74.0060, df)

        assert len(distances) == 2
        assert distances[0] is None, "Invalid latitude should return None"
        assert distances[1] is None, "Invalid longitude should return None"

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame({"Latitude": [], "Longitude": []})

        distances = calculate_distances(40.7128, -74.0060, df)

        assert distances == []

    def test_mixed_valid_invalid_coordinates(self):
        """Test handling of mixed valid and invalid coordinates."""
        df = pd.DataFrame({"Latitude": [40.7128, float("nan"), 39.9526], "Longitude": [-74.0060, -75.0, float("nan")]})

        distances = calculate_distances(40.7128, -74.0060, df)

        assert len(distances) == 3
        assert distances[0] is not None, "Valid coordinates should calculate"
        assert distances[1] is None, "Invalid latitude should return None"
        assert distances[2] is None, "Invalid longitude should return None"

    def test_cross_country_distance(self):
        """Test long-distance calculation (NYC to LA ~2,400 miles)."""
        # New York City: 40.7128° N, 74.0060° W
        # Los Angeles: 34.0522° N, 118.2437° W

        df = pd.DataFrame({"Latitude": [34.0522], "Longitude": [-118.2437]})

        distances = calculate_distances(40.7128, -74.0060, df)

        assert len(distances) == 1
        assert distances[0] is not None
        assert 2300 < distances[0] < 2500, f"Expected ~2,400 miles, got {distances[0]:.1f}"

    def test_distance_calculation_is_symmetric(self):
        """Test that distance from A to B equals distance from B to A."""
        loc_a = (40.7128, -74.0060)  # NYC
        loc_b = (39.9526, -75.1652)  # Philadelphia

        # Distance from A to B
        df_b = pd.DataFrame({"Latitude": [loc_b[0]], "Longitude": [loc_b[1]]})
        dist_a_to_b = calculate_distances(loc_a[0], loc_a[1], df_b)[0]

        # Distance from B to A
        df_a = pd.DataFrame({"Latitude": [loc_a[0]], "Longitude": [loc_a[1]]})
        dist_b_to_a = calculate_distances(loc_b[0], loc_b[1], df_a)[0]

        assert dist_a_to_b is not None and dist_b_to_a is not None
        assert abs(dist_a_to_b - dist_b_to_a) < 0.1, "Distance should be symmetric"

    def test_negative_coordinates(self):
        """Test distance calculation with negative coordinates."""
        # Test southern hemisphere and western longitude
        df = pd.DataFrame(
            {
                "Latitude": [-33.8688],  # Sydney, Australia (negative latitude)
                "Longitude": [151.2093],  # Sydney (positive longitude)
            }
        )

        # From Cape Town, South Africa
        distances = calculate_distances(-33.9249, 18.4241, df)

        assert len(distances) == 1
        assert distances[0] is not None
        assert distances[0] > 0, "Distance should be positive"
        # Cape Town to Sydney is ~6,000+ miles
        assert distances[0] > 5000, "Cape Town to Sydney should be very far"
