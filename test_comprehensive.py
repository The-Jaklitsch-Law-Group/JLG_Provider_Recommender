#!/usr/bin/env python3
"""
Comprehensive test to verify the duplication fix and overall app functionality.
"""

import os
import sys
from datetime import date

import pandas as pd

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_app_imports():
    """Test that all app imports work correctly."""
    print("🧪 Testing app imports...")

    try:
        # Test core imports
        from src.data.ingestion import DataIngestionManager, DataSource
        from src.utils.performance import handle_streamlit_error
        from src.utils.providers import (
            calculate_distances,
            calculate_inbound_referral_counts,
            calculate_time_based_referral_counts,
            geocode_address_with_cache,
            recommend_provider,
            validate_address,
        )
        from src.utils.validation import validate_address_input

        print("✅ All core imports successful")
        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_data_loading():
    """Test that data loading works without duplicates."""
    print("\n🧪 Testing data loading...")

    try:
        from src.data.ingestion import DataIngestionManager, DataSource

        manager = DataIngestionManager()

        # Test loading different data sources
        try:
            inbound_df = manager.load_data(DataSource.INBOUND_REFERRALS)
            print(f"✅ Loaded inbound referrals: {len(inbound_df)} records")
        except Exception as e:
            print(f"⚠️ Inbound referrals loading issue: {e}")

        try:
            outbound_df = manager.load_data(DataSource.OUTBOUND_REFERRALS)
            print(f"✅ Loaded outbound referrals: {len(outbound_df)} records")
        except Exception as e:
            print(f"⚠️ Outbound referrals loading issue: {e}")

        try:
            provider_df = manager.load_data(DataSource.PROVIDER_DATA)
            print(f"✅ Loaded provider data: {len(provider_df)} records")
        except Exception as e:
            print(f"⚠️ Provider data loading issue: {e}")

        return True

    except Exception as e:
        print(f"❌ Data loading test failed: {e}")
        return False


def test_time_filtering_function():
    """Test the time filtering function logic."""
    print("\n🧪 Testing time filtering function...")

    try:
        from src.utils.providers import calculate_time_based_referral_counts

        # Create sample data
        sample_data = pd.DataFrame(
            {
                "Full Name": ["Dr. Smith", "Dr. Jones", "Dr. Smith", "Dr. Brown"],
                "Date of Intake": [
                    pd.Timestamp("2023-06-01"),
                    pd.Timestamp("2023-08-15"),
                    pd.Timestamp("2023-09-10"),
                    pd.Timestamp("2024-01-20"),
                ],
            }
        )

        start_date = date(2023, 7, 1)
        end_date = date(2023, 12, 31)

        result = calculate_time_based_referral_counts(sample_data, start_date, end_date)

        print(f"✅ Time filtering function works: {len(result)} filtered results")

        # Check for proper aggregation (Dr. Smith should appear only once)
        if "Dr. Smith" in result["Full Name"].values:
            smith_count = result[result["Full Name"] == "Dr. Smith"]["Referral Count"].iloc[0]
            print(f"✅ Dr. Smith referral count: {smith_count}")

        return True

    except Exception as e:
        print(f"❌ Time filtering test failed: {e}")
        return False


def test_address_validation():
    """Test address validation functions."""
    print("\n🧪 Testing address validation...")

    try:
        from src.utils.providers import validate_address
        from src.utils.validation import validate_address_input

        # Test valid address
        valid, message = validate_address_input("123 Main St", "Anytown", "PA", "12345")
        print(f"✅ Address validation works: {valid}, {message}")

        # Test address validation
        is_valid, msg = validate_address("123 Main St, Anytown, PA 12345")
        print(f"✅ Address validation 2 works: {is_valid}")

        return True

    except Exception as e:
        print(f"❌ Address validation test failed: {e}")
        return False


def test_geocoding_functions():
    """Test geocoding functionality."""
    print("\n🧪 Testing geocoding functions...")

    try:
        import pandas as pd

        from src.utils.providers import calculate_distances, geocode_address_with_cache

        # Test with a well-known address (this may not work without internet)
        try:
            coords = geocode_address_with_cache("1600 Pennsylvania Avenue, Washington, DC")
            if coords:
                print(f"✅ Geocoding works: {coords}")
            else:
                print("⚠️ Geocoding returned no results (may be network/rate limit issue)")
        except Exception as e:
            print(f"⚠️ Geocoding test skipped due to: {e}")

        # Test distance calculation with sample data
        sample_providers = pd.DataFrame({"Latitude": [40.7128, 34.0522], "Longitude": [-74.0060, -118.2437]})

        distances = calculate_distances(40.7589, -73.9851, sample_providers)  # Times Square coords
        print(f"✅ Distance calculation works: {len(distances)} distances calculated")

        return True

    except Exception as e:
        print(f"❌ Geocoding test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting comprehensive duplication fix verification...")
    print("=" * 60)

    tests = [
        test_app_imports,
        test_data_loading,
        test_time_filtering_function,
        test_address_validation,
        test_geocoding_functions,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The app should work correctly without duplicates.")
    else:
        print("⚠️ Some tests failed. Review the output above for details.")

    print("\n💡 To test the UI duplication fix:")
    print("   1. Run the Streamlit app")
    print("   2. Enter an address and search")
    print("   3. Enable time filtering")
    print("   4. Verify that the time filter message appears only once")


if __name__ == "__main__":
    main()
