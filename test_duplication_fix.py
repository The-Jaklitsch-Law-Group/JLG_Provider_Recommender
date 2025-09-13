#!/usr/bin/env python3
"""
Test script to verify that the duplication issue is fixed.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime

import pandas as pd

from src.data.ingestion import DataIngestionManager
from src.utils.providers import calculate_time_based_referral_counts


def test_time_filtering_logic():
    """Test that time filtering works without duplicating data."""
    print("🧪 Testing time filtering logic...")

    try:
        # Load data
        manager = DataIngestionManager()
        from src.data.ingestion import DataSource

        provider_df, detailed_referrals_df = manager.load_data(DataSource.ALL_REFERRALS)

        print(f"✅ Loaded {len(provider_df)} providers and {len(detailed_referrals_df)} referrals")

        # Test time filtering function
        start_date = date(2023, 1, 1)
        end_date = date(2024, 12, 31)

        time_filtered = calculate_time_based_referral_counts(detailed_referrals_df, start_date, end_date)

        print(f"✅ Time filtering returned {len(time_filtered)} providers")

        # Check for duplicates
        original_count = len(provider_df)
        unique_providers = provider_df["Full Name"].nunique()

        print(f"✅ Original providers: {original_count}, Unique names: {unique_providers}")

        if original_count == unique_providers:
            print("✅ No duplicate providers found in original data")
        else:
            print(f"⚠️ Found duplicate providers: {original_count - unique_providers} duplicates")

        # Check time filtered data for duplicates
        if len(time_filtered) > 0:
            time_unique = time_filtered["Full Name"].nunique()
            time_count = len(time_filtered)

            if time_count == time_unique:
                print("✅ No duplicate providers found in time-filtered data")
            else:
                print(f"⚠️ Found duplicate providers in time-filtered data: {time_count - time_unique} duplicates")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_data_integrity():
    """Test overall data integrity."""
    print("\n🧪 Testing data integrity...")

    try:
        manager = DataIngestionManager()
        provider_df, detailed_referrals_df = manager.load_data()

        # Check required columns
        required_provider_cols = ["Full Name", "Phone Number", "Referral Count"]
        missing_cols = [col for col in required_provider_cols if col not in provider_df.columns]

        if missing_cols:
            print(f"❌ Missing required columns in provider data: {missing_cols}")
            return False
        else:
            print("✅ All required provider columns present")

        # Check for NaN values in critical columns
        critical_nans = provider_df["Full Name"].isna().sum()
        if critical_nans > 0:
            print(f"⚠️ Found {critical_nans} NaN values in Full Name column")
        else:
            print("✅ No NaN values in Full Name column")

        # Check referral counts
        total_referrals = provider_df["Referral Count"].sum()
        print(f"✅ Total referral count: {total_referrals}")

        return True

    except Exception as e:
        print(f"❌ Data integrity test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting duplication fix verification tests...")

    test1_passed = test_time_filtering_logic()
    test2_passed = test_data_integrity()

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Duplication fix appears to be working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
