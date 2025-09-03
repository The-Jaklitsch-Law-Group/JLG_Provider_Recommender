"""Integration tests for the Streamlit app functionality."""

import os
import sys
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from provider_utils import calculate_distances, load_provider_data, recommend_provider


class TestEndToEndWorkflow:
    """Test the complete workflow from data loading to recommendation."""

    def setup_method(self):
        """Create test data for integration tests."""
        self.test_provider_data = pd.DataFrame(
            {
                "Person ID": [1, 2, 3],
                "Full Name": ["Dr. Alice Smith", "Dr. Bob Jones", "Dr. Carol Brown"],
                "Street": ["123 Main St", "456 Oak Ave", "789 Pine Rd"],
                "City": ["Baltimore", "Annapolis", "Columbia"],
                "State": ["MD", "MD", "MD"],
                "Zip": ["21201", "21401", "21044"],
                "Latitude": [39.2904, 38.9784, 39.2037],
                "Longitude": [-76.6122, -76.4951, -76.8610],
                "Phone Number": ["410-555-0001", "410-555-0002", "410-555-0003"],
                "Referral Count": [5, 12, 8],
            }
        )

    def test_complete_recommendation_workflow(self):
        """Test the complete workflow from user location to recommendation."""
        # User location (Baltimore City Hall)
        user_lat, user_lon = 39.2904, -76.6122

        # Calculate distances
        self.test_provider_data["Distance (Miles)"] = calculate_distances(user_lat, user_lon, self.test_provider_data)

        # Get recommendation prioritizing distance
        best, scored_df = recommend_provider(
            self.test_provider_data, distance_weight=0.8, referral_weight=0.2, min_referrals=1
        )

        # Assertions
        assert best is not None
        assert best["Full Name"] == "Dr. Alice Smith"  # Should be closest
        assert len(scored_df) == 3
        assert all(scored_df["Distance (Miles)"].notna())
        assert all(scored_df["Score"].notna())

        # Check score calculation
        assert scored_df.iloc[0]["Score"] <= scored_df.iloc[1]["Score"]  # Best should have lowest score

    def test_load_balancing_recommendation(self):
        """Test recommendation when prioritizing load balancing."""
        user_lat, user_lon = 39.2904, -76.6122

        self.test_provider_data["Distance (Miles)"] = calculate_distances(user_lat, user_lon, self.test_provider_data)

        # Prioritize referral count (load balancing)
        best, scored_df = recommend_provider(
            self.test_provider_data, distance_weight=0.2, referral_weight=0.8, min_referrals=1
        )

        # Should recommend provider with fewer referrals
        assert best["Full Name"] == "Dr. Alice Smith"  # Has only 5 referrals vs 12 and 8

    def test_minimum_referrals_filter(self):
        """Test filtering by minimum referral count."""
        user_lat, user_lon = 39.2904, -76.6122

        self.test_provider_data["Distance (Miles)"] = calculate_distances(user_lat, user_lon, self.test_provider_data)

        # Filter for providers with at least 8 referrals
        best, scored_df = recommend_provider(
            self.test_provider_data, distance_weight=0.5, referral_weight=0.5, min_referrals=8
        )

        # Should only include Dr. Jones (12) and Dr. Brown (8)
        assert len(scored_df) == 2
        assert "Dr. Alice Smith" not in scored_df["Full Name"].values
        assert best["Full Name"] in ["Dr. Bob Jones", "Dr. Carol Brown"]

    def test_edge_case_single_provider(self):
        """Test recommendation with only one qualifying provider."""
        single_provider = self.test_provider_data.iloc[[0]].copy()
        user_lat, user_lon = 39.2904, -76.6122

        single_provider["Distance (Miles)"] = calculate_distances(user_lat, user_lon, single_provider)

        best, scored_df = recommend_provider(single_provider)

        assert best is not None
        assert best["Full Name"] == "Dr. Alice Smith"
        assert len(scored_df) == 1
        assert scored_df.iloc[0]["Score"] == 0.0  # Should be 0 when normalized with single value

    def test_edge_case_no_qualifying_providers(self):
        """Test recommendation when no providers meet minimum requirements."""
        user_lat, user_lon = 39.2904, -76.6122

        self.test_provider_data["Distance (Miles)"] = calculate_distances(user_lat, user_lon, self.test_provider_data)

        # Set minimum referrals higher than any provider has
        best, scored_df = recommend_provider(self.test_provider_data, min_referrals=50)  # Higher than max of 12

        assert best is None
        assert scored_df is None


class TestDataValidationIntegration:
    """Test data validation in realistic scenarios."""

    def test_mixed_quality_data(self):
        """Test handling of data with various quality issues."""
        mixed_data = pd.DataFrame(
            {
                "Full Name": ["Dr. Good", "Dr. Missing Coords", "Dr. Invalid Referrals", ""],
                "Street": ["123 Main St", "456 Oak Ave", "789 Pine Rd", "999 Test St"],
                "City": ["Baltimore", "Baltimore", "Baltimore", "Baltimore"],
                "State": ["MD", "MD", "MD", "MD"],
                "Zip": ["21201", "21202", "21203", "21204"],
                "Latitude": [39.2904, None, 39.2906, 39.2907],
                "Longitude": [-76.6122, -76.6123, None, -76.6125],
                "Phone Number": ["410-555-0001", "410-555-0002", "410-555-0003", "410-555-0004"],
                "Referral Count": [10, 5, None, 3],
            }
        )

        user_lat, user_lon = 39.2904, -76.6122

        # Calculate distances (should handle missing coordinates)
        mixed_data["Distance (Miles)"] = calculate_distances(user_lat, user_lon, mixed_data)

        # Should still be able to make recommendation with valid data
        best, scored_df = recommend_provider(mixed_data, min_referrals=1)

        # Should recommend from providers with valid data
        assert best is not None
        assert best["Full Name"] in ["Dr. Good", ""]  # Empty name but valid other data

        # Check that invalid data is handled gracefully
        valid_distances = [d for d in mixed_data["Distance (Miles)"] if d is not None]
        assert len(valid_distances) >= 2  # Should have some valid distances


class TestPerformanceIntegration:
    """Test performance characteristics with larger datasets."""

    def test_large_dataset_performance(self):
        """Test recommendation performance with larger provider dataset."""
        # Create a larger test dataset
        np.random.seed(42)
        n_providers = 1000

        large_dataset = pd.DataFrame(
            {
                "Person ID": range(n_providers),
                "Full Name": [f"Dr. Provider {i}" for i in range(n_providers)],
                "Street": [f"{100 + i} Test St" for i in range(n_providers)],
                "City": ["Baltimore"] * n_providers,
                "State": ["MD"] * n_providers,
                "Zip": ["21201"] * n_providers,
                "Latitude": np.random.uniform(39.0, 39.5, n_providers),
                "Longitude": np.random.uniform(-77.0, -76.0, n_providers),
                "Phone Number": [f"410-555-{i:04d}" for i in range(n_providers)],
                "Referral Count": np.random.randint(1, 50, n_providers),
            }
        )

        user_lat, user_lon = 39.2904, -76.6122

        # Test distance calculation performance
        import time

        start_time = time.time()
        large_dataset["Distance (Miles)"] = calculate_distances(user_lat, user_lon, large_dataset)
        distance_time = time.time() - start_time

        # Should complete in reasonable time (< 1 second for 1000 providers)
        assert distance_time < 1.0

        # Test recommendation performance
        start_time = time.time()
        best, scored_df = recommend_provider(large_dataset, min_referrals=5)
        recommendation_time = time.time() - start_time

        # Should complete in reasonable time
        assert recommendation_time < 0.5
        assert best is not None
        assert len(scored_df) > 0


if __name__ == "__main__":
    pytest.main([__file__])
