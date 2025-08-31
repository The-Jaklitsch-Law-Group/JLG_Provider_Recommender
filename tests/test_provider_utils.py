"""Unit tests for provider utility functions."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import provider_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from provider_utils import (
    sanitize_filename,
    validate_address_input,
    validate_provider_data,
    safe_numeric_conversion,
    validate_and_clean_coordinates,
    calculate_distances,
    recommend_provider,
    handle_geocoding_error,
    calculate_time_based_referral_counts,
)


class TestSanitizeFilename:
    """Test filename sanitization."""
    
    def test_basic_sanitization(self):
        assert sanitize_filename("John Doe") == "John_Doe"
        assert sanitize_filename("Dr. Smith & Associates") == "Dr_Smith__Associates"
        assert sanitize_filename("Provider #1 (Main)") == "Provider_1_Main"
    
    def test_empty_string(self):
        assert sanitize_filename("") == ""
    
    def test_special_characters(self):
        assert sanitize_filename("Test@#$%^&*()") == "Test"


class TestValidateAddressInput:
    """Test address input validation."""
    
    def test_valid_address(self):
        is_valid, message = validate_address_input("123 Main St", "Baltimore", "MD", "21201")
        assert is_valid
        assert "Suggestions" in message  # Should have suggestions but be valid
    
    def test_missing_street(self):
        is_valid, message = validate_address_input("", "Baltimore", "MD", "21201")
        assert not is_valid
        assert "Street address is required" in message
    
    def test_invalid_state(self):
        is_valid, message = validate_address_input("123 Main St", "Baltimore", "XX", "21201")
        assert is_valid  # Still valid, just warning
        assert "may not be a valid US state" in message
    
    def test_invalid_zip(self):
        is_valid, message = validate_address_input("123 Main St", "Baltimore", "MD", "abc")
        assert is_valid  # Still valid, just warning
        assert "ZIP code should be 5 digits" in message
    
    def test_test_address_warning(self):
        is_valid, message = validate_address_input("test", "Baltimore", "MD", "21201")
        assert is_valid
        assert "test value" in message


class TestValidateProviderData:
    """Test provider data validation."""
    
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        is_valid, message = validate_provider_data(df)
        assert not is_valid
        assert "No provider data available" in message
    
    def test_missing_columns(self):
        df = pd.DataFrame({"Name": ["Dr. Smith"]})
        is_valid, message = validate_provider_data(df)
        assert not is_valid
        assert "Missing required columns" in message
    
    def test_valid_dataframe(self):
        df = pd.DataFrame({
            "Full Name": ["Dr. Smith", "Dr. Jones"],
            "Referral Count": [10, 5],
            "Latitude": [39.2904, 39.2905],
            "Longitude": [-76.6122, -76.6123]
        })
        is_valid, message = validate_provider_data(df)
        assert is_valid
        assert "Total providers in database: 2" in message


class TestSafeNumericConversion:
    """Test safe numeric conversion."""
    
    def test_valid_numbers(self):
        assert safe_numeric_conversion("123.45") == 123.45
        assert safe_numeric_conversion(123) == 123.0
        assert safe_numeric_conversion("0") == 0.0
    
    def test_invalid_values(self):
        assert safe_numeric_conversion("abc") == 0
        assert safe_numeric_conversion(None) == 0
        assert safe_numeric_conversion("") == 0
    
    def test_custom_default(self):
        assert safe_numeric_conversion("abc", -999) == -999
        assert safe_numeric_conversion(None, 100) == 100
    
    def test_nan_values(self):
        assert safe_numeric_conversion(np.nan) == 0
        assert pd.isna(safe_numeric_conversion(np.nan, None))


class TestValidateAndCleanCoordinates:
    """Test coordinate validation and cleaning."""
    
    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = validate_and_clean_coordinates(df)
        assert result.empty
    
    def test_valid_coordinates(self):
        df = pd.DataFrame({
            "Latitude": [39.2904, 40.7128],
            "Longitude": [-76.6122, -74.0060],
            "Name": ["Baltimore", "NYC"]
        })
        result = validate_and_clean_coordinates(df)
        assert len(result) == 2
        assert all(result["Latitude"].notna())
        assert all(result["Longitude"].notna())
    
    def test_invalid_coordinates(self):
        df = pd.DataFrame({
            "Latitude": [39.2904, 999],  # Invalid latitude
            "Longitude": [-76.6122, -74.0060],
            "Name": ["Baltimore", "Invalid"]
        })
        with patch('streamlit.warning') as mock_warning:
            result = validate_and_clean_coordinates(df)
            assert len(result) == 2
            mock_warning.assert_called_once()


class TestCalculateDistances:
    """Test distance calculation."""
    
    def test_basic_distance_calculation(self):
        # Test distance between Baltimore and NYC (approximately 184 miles)
        user_lat, user_lon = 39.2904, -76.6122  # Baltimore
        
        provider_df = pd.DataFrame({
            "Latitude": [40.7128, 39.2904],  # NYC, Baltimore
            "Longitude": [-74.0060, -76.6122],
            "Name": ["NYC", "Baltimore"]
        })
        
        distances = calculate_distances(user_lat, user_lon, provider_df)
        
        assert len(distances) == 2
        assert distances[1] == 0.0 or distances[1] < 1  # Same location
        assert distances[0] > 100  # NYC should be ~184 miles away
        assert distances[0] < 250  # But not too far
    
    def test_missing_coordinates(self):
        user_lat, user_lon = 39.2904, -76.6122
        
        provider_df = pd.DataFrame({
            "Latitude": [40.7128, None],
            "Longitude": [-74.0060, -76.6122],
            "Name": ["NYC", "Missing"]
        })
        
        distances = calculate_distances(user_lat, user_lon, provider_df)
        
        assert len(distances) == 2
        assert distances[0] is not None
        assert distances[1] is None  # Missing coordinates


class TestRecommendProvider:
    """Test provider recommendation logic."""
    
    def test_basic_recommendation(self):
        provider_df = pd.DataFrame({
            "Full Name": ["Dr. Smith", "Dr. Jones", "Dr. Brown"],
            "Distance (Miles)": [5.0, 10.0, 15.0],
            "Referral Count": [10, 5, 20],
            "Full Address": ["123 Main St", "456 Oak Ave", "789 Pine Rd"]
        })
        
        best, scored_df = recommend_provider(
            provider_df, 
            distance_weight=1.0, 
            referral_weight=0.0,  # Only consider distance
            min_referrals=1
        )
        
        assert best is not None
        assert best["Full Name"] == "Dr. Smith"  # Closest provider
        assert len(scored_df) == 3
        assert "Score" in scored_df.columns
    
    def test_empty_dataframe(self):
        provider_df = pd.DataFrame()
        best, scored_df = recommend_provider(provider_df)
        
        assert best is None
        assert scored_df is None
    
    def test_min_referrals_filter(self):
        provider_df = pd.DataFrame({
            "Full Name": ["Dr. Smith", "Dr. Jones"],
            "Distance (Miles)": [5.0, 10.0],
            "Referral Count": [1, 10],
            "Full Address": ["123 Main St", "456 Oak Ave"]
        })
        
        best, scored_df = recommend_provider(
            provider_df, 
            min_referrals=5  # Only Dr. Jones qualifies
        )
        
        assert best["Full Name"] == "Dr. Jones"
        assert len(scored_df) == 1
    
    def test_scoring_weights(self):
        provider_df = pd.DataFrame({
            "Full Name": ["Close & Many Referrals", "Far & Few Referrals"],
            "Distance (Miles)": [1.0, 20.0],
            "Referral Count": [50, 1],
            "Full Address": ["123 Main St", "456 Oak Ave"]
        })
        
        # Test distance priority
        best_distance, _ = recommend_provider(
            provider_df, 
            distance_weight=1.0, 
            referral_weight=0.0
        )
        assert best_distance["Full Name"] == "Close & Many Referrals"
        
        # Test referral priority (fewer is better for load balancing)
        best_referral, _ = recommend_provider(
            provider_df, 
            distance_weight=0.0, 
            referral_weight=1.0
        )
        assert best_referral["Full Name"] == "Far & Few Referrals"


class TestHandleGeocodingError:
    """Test geocoding error handling."""
    
    def test_timeout_error(self):
        error = Exception("timeout occurred")
        message = handle_geocoding_error("123 Main St", error)
        assert "Timeout" in message
        assert "taking too long" in message
    
    def test_service_unavailable(self):
        error = Exception("service unavailable")
        message = handle_geocoding_error("123 Main St", error)
        assert "Service Unavailable" in message
    
    def test_rate_limit_error(self):
        error = Exception("rate limit exceeded")
        message = handle_geocoding_error("123 Main St", error)
        assert "Rate Limited" in message
    
    def test_generic_error(self):
        error = ValueError("invalid input")
        message = handle_geocoding_error("123 Main St", error)
        assert "Geocoding Error" in message
        assert "123 Main St" in message
        assert "ValueError" in message


class TestCalculateTimeBasedReferralCounts:
    """Test time-based referral count calculation."""
    
    def test_basic_time_filtering(self):
        detailed_df = pd.DataFrame({
            "Full Name": ["Dr. Smith", "Dr. Smith", "Dr. Jones"],
            "Street": ["123 Main St", "123 Main St", "456 Oak Ave"],
            "City": ["Baltimore", "Baltimore", "Baltimore"],
            "State": ["MD", "MD", "MD"],
            "Zip": ["21201", "21201", "21202"],
            "Latitude": [39.2904, 39.2904, 39.2905],
            "Longitude": [-76.6122, -76.6122, -76.6123],
            "Phone Number": ["555-1234", "555-1234", "555-5678"],
            "Referral Date": pd.to_datetime([
                "2023-01-01", "2023-06-01", "2023-01-15"
            ])
        })
        
        # Filter for first half of 2023
        result = calculate_time_based_referral_counts(
            detailed_df, 
            start_date="2023-01-01", 
            end_date="2023-06-30"
        )
        
        assert len(result) == 2  # Two unique providers
        # Dr. Smith should have 2 referrals, Dr. Jones should have 1
        smith_count = result[result["Full Name"] == "Dr. Smith"]["Referral Count"].iloc[0]
        jones_count = result[result["Full Name"] == "Dr. Jones"]["Referral Count"].iloc[0]
        assert smith_count == 2
        assert jones_count == 1
    
    def test_empty_dataframe(self):
        result = calculate_time_based_referral_counts(
            pd.DataFrame(), 
            start_date="2023-01-01", 
            end_date="2023-12-31"
        )
        assert result.empty
    
    def test_no_results_in_period(self):
        detailed_df = pd.DataFrame({
            "Full Name": ["Dr. Smith"],
            "Street": ["123 Main St"],
            "City": ["Baltimore"],
            "State": ["MD"],
            "Zip": ["21201"],
            "Latitude": [39.2904],
            "Longitude": [-76.6122],
            "Phone Number": ["555-1234"],
            "Referral Date": pd.to_datetime(["2020-01-01"])
        })
        
        result = calculate_time_based_referral_counts(
            detailed_df, 
            start_date="2023-01-01", 
            end_date="2023-12-31"
        )
        
        assert result.empty


if __name__ == "__main__":
    pytest.main([__file__])
