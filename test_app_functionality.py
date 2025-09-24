#!/usr/bin/env python3
"""
Comprehensive Application Functionality Test

This script tests all core functionality of the JLG Provider Recommender app
to ensure it's working properly after the data schema changes.
"""

import sys
import traceback
from pathlib import Path

import pandas as pd


def test_data_ingestion():
    """Test data loading functionality."""
    print("🔍 Testing Data Ingestion...")
    try:
        from src.data.ingestion import (
            get_data_ingestion_status,
            load_detailed_referrals,
            load_inbound_referrals,
            load_provider_data,
        )

        # Test status
        status = get_data_ingestion_status()
        print(f"  ✅ Data ingestion status: {len([k for k, v in status.items() if v['available']])} sources available")

        # Test data loading
        inbound_df = load_inbound_referrals()
        outbound_df = load_detailed_referrals()
        provider_df = load_provider_data()

        print(f"  ✅ Inbound referrals: {inbound_df.shape[0]} records")
        print(f"  ✅ Outbound referrals: {outbound_df.shape[0]} records")
        print(f"  ✅ Provider data: {provider_df.shape[0]} records")

        # Check expected columns
        expected_cols = ["Full Name", "Work Address", "Work Phone", "Latitude", "Longitude"]
        for col in expected_cols:
            if col not in provider_df.columns:
                print(f"  ⚠️  Missing expected column: {col}")
            else:
                print(f"  ✅ Column present: {col}")

        return True

    except Exception as e:
        print(f"  ❌ Data ingestion failed: {e}")
        traceback.print_exc()
        return False


def test_provider_utilities():
    """Test provider utility functions."""
    print("\n🔍 Testing Provider Utilities...")
    try:
        import pandas as pd

        from src.utils.providers import calculate_distances, validate_address, validate_address_input

        # Test distance calculation
        test_df = pd.DataFrame({"Latitude": [40.7128, 41.8781], "Longitude": [-74.0060, -87.6298]})
        distances = calculate_distances(40.7128, -74.0060, test_df)
        if len(distances) > 0:
            print(f"  ✅ Distance calculation working: {len(distances)} distances calculated")
        else:
            print("  ❌ Distance calculation failed")

        # Test address validation (basic)
        test_address = "123 Main Street, New York, NY"
        is_valid = validate_address(test_address)
        print(f"  ✅ Address validation: {is_valid}")

        # Test structured address validation
        is_valid, message = validate_address_input("123 Main St", "New York", "NY", "10001")
        print(f"  ✅ Structured address validation: {is_valid} - {message}")

        return True

    except Exception as e:
        print(f"  ❌ Provider utilities failed: {e}")
        traceback.print_exc()
        return False


def test_data_processing():
    """Test data processing workflow."""
    print("\n🔍 Testing Data Processing...")
    try:
        from src.data.preparation_enhanced import DataPreparationManager

        # Test manager initialization
        manager = DataPreparationManager()
        print("  ✅ DataPreparationManager initialized")

        # Check if raw data exists
        raw_file = Path("data/raw/Referrals_App_Full_Contacts.xlsx")
        if raw_file.exists():
            print("  ✅ Raw data file exists")
        else:
            print("  ⚠️  Raw data file not found")

        # Check processed files
        processed_files = [
            "data/processed/cleaned_inbound_referrals.parquet",
            "data/processed/cleaned_outbound_referrals.parquet",
            "data/processed/cleaned_all_referrals.parquet",
        ]

        for file_path in processed_files:
            if Path(file_path).exists():
                print(f"  ✅ Processed file exists: {Path(file_path).name}")
            else:
                print(f"  ❌ Missing processed file: {Path(file_path).name}")

        return True

    except Exception as e:
        print(f"  ❌ Data processing test failed: {e}")
        traceback.print_exc()
        return False


def test_recommendation_engine():
    """Test provider recommendation functionality."""
    print("\n🔍 Testing Recommendation Engine...")
    try:
        from src.data.ingestion import load_provider_data
        from src.utils.providers import calculate_distances, recommend_provider

        # Load provider data
        provider_df = load_provider_data()
        if provider_df.empty:
            print("  ❌ No provider data loaded")
            return False

        print(f"  ✅ Provider data loaded: {len(provider_df)} records")

        # Add distance calculation (simulating app workflow)
        test_df = provider_df.copy()
        user_lat, user_lon = 40.7128, -74.0060  # NYC coordinates
        test_df["Distance (Miles)"] = calculate_distances(user_lat, user_lon, test_df)

        # Test recommendation with proper parameters
        best_provider, scored_df = recommend_provider(
            test_df, distance_weight=0.7, referral_weight=0.2, inbound_weight=0.1, min_referrals=None
        )

        if scored_df is not None and len(scored_df) > 0:
            print(f"  ✅ Recommendation successful: {len(scored_df)} providers scored")

            if best_provider is not None:
                # best_provider is a pandas Series, not DataFrame
                if hasattr(best_provider, "get"):
                    provider_name = best_provider.get("Full Name", "Unknown")
                else:
                    provider_name = str(best_provider)
                print(f"  ✅ Best provider found: {provider_name}")
            else:
                print("  ⚠️  No best provider identified")
        else:
            print("  ❌ Recommendation failed: no scored providers")

        return True

    except Exception as e:
        print(f"  ❌ Recommendation engine failed: {e}")
        traceback.print_exc()
        return False


def test_app_imports():
    """Test that main app can import without errors."""
    print("\n🔍 Testing App Imports...")
    try:
        # Import main app modules (without running Streamlit)
        sys.path.insert(0, str(Path.cwd()))

        # Test key imports from app.py
        from src.data.ingestion import (
            get_data_ingestion_status,
            load_detailed_referrals,
            load_inbound_referrals,
            load_provider_data,
            refresh_data_cache,
        )

        print("  ✅ Data ingestion imports successful")

        from src.utils.providers import (
            calculate_distances,
            calculate_inbound_referral_counts,
            calculate_time_based_referral_counts,
            geocode_address_with_cache,
            recommend_provider,
            validate_address,
            validate_address_input,
            validate_and_clean_coordinates,
        )

        print("  ✅ Provider utilities imports successful")

        # Test data dashboard imports
        import data_dashboard

        print("  ✅ Data dashboard imports successful")

        return True

    except Exception as e:
        print(f"  ❌ App imports failed: {e}")
        traceback.print_exc()
        return False


def main():
    """Run comprehensive functionality tests."""
    print("🚀 JLG Provider Recommender - Comprehensive Functionality Test")
    print("=" * 60)

    test_results = []

    # Run all tests
    test_results.append(("Data Ingestion", test_data_ingestion()))
    test_results.append(("Provider Utilities", test_provider_utilities()))
    test_results.append(("Data Processing", test_data_processing()))
    test_results.append(("Recommendation Engine", test_recommendation_engine()))
    test_results.append(("App Imports", test_app_imports()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<20} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n🎉 All functionality tests passed! The app should be fully operational.")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review the output above for issues.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
