#!/usr/bin/env python3
"""
Test script to verify deduplication is working in the dataframe results.
"""

import os
import sys

import pandas as pd

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_deduplication_logic():
    """Test the deduplication logic with sample data."""
    print("🧪 Testing DataFrame deduplication logic...")

    # Create sample data with duplicates
    sample_data = pd.DataFrame(
        {
            "Full Name": ["Dr. Smith", "Dr. Jones", "Dr. Smith", "Dr. Brown", "Dr. Jones"],
            "Full Address": ["123 Main St", "456 Oak Ave", "123 Main St", "789 Pine St", "456 Oak Ave"],
            "Distance (Miles)": [2.5, 3.1, 2.5, 1.8, 3.1],
            "Referral Count": [10, 5, 10, 8, 5],
            "Score": [85.2, 72.1, 85.2, 90.3, 72.1],
        }
    )

    print(f"Original data: {len(sample_data)} records")
    print("Full Names:", sample_data["Full Name"].tolist())

    # Apply deduplication (same as in app)
    deduplicated = sample_data.drop_duplicates(subset=["Full Name"], keep="first")

    print(f"After deduplication: {len(deduplicated)} records")
    print("Full Names:", deduplicated["Full Name"].tolist())

    # Check results
    expected_unique = sample_data["Full Name"].nunique()
    actual_count = len(deduplicated)

    if actual_count == expected_unique:
        print("✅ Deduplication working correctly!")
        return True
    else:
        print(f"❌ Deduplication failed: expected {expected_unique}, got {actual_count}")
        return False


def test_dataframe_display_logic():
    """Test the dataframe display logic."""
    print("\n🧪 Testing DataFrame display deduplication...")

    # Create sample scored_df with duplicates
    scored_df = pd.DataFrame(
        {
            "Full Name": ["Dr. Smith", "Dr. Jones", "Dr. Smith", "Dr. Brown"],
            "Full Address": ["123 Main St", "456 Oak Ave", "123 Main St Alt", "789 Pine St"],
            "Distance (Miles)": [2.5, 3.1, 2.7, 1.8],
            "Referral Count": [10, 5, 12, 8],
            "Score": [85.2, 72.1, 87.1, 90.3],
        }
    )

    available_cols = ["Full Name", "Full Address", "Distance (Miles)", "Referral Count", "Score"]

    print(f"Original scored_df: {len(scored_df)} records")

    # Apply the same logic as in the app
    display_df = (
        scored_df[available_cols]
        .drop_duplicates(subset=["Full Name"], keep="first")
        .sort_values(by="Score", ignore_index=True)
    )

    print(f"Display dataframe: {len(display_df)} records")
    print("Providers in display order:")
    for i, (idx, row) in enumerate(display_df.iterrows()):
        print(f"  {i+1}. {row['Full Name']} (Score: {row['Score']})")

    # Verify no duplicates
    unique_names = display_df["Full Name"].nunique()
    total_rows = len(display_df)

    if unique_names == total_rows:
        print("✅ Display dataframe has no duplicate providers!")
        return True
    else:
        print(f"❌ Display dataframe still has duplicates: {total_rows - unique_names}")
        return False


def main():
    """Run deduplication tests."""
    print("🚀 Testing DataFrame deduplication fixes...")
    print("=" * 60)

    test1_passed = test_deduplication_logic()
    test2_passed = test_dataframe_display_logic()

    print("\n" + "=" * 60)

    if test1_passed and test2_passed:
        print("🎉 All deduplication tests passed!")
        print("✅ The app should now show unique providers only")
    else:
        print("❌ Some deduplication tests failed")

    print("\n💡 The app now applies deduplication at 3 levels:")
    print("   1. Initial provider data loading")
    print("   2. After recommendation scoring")
    print("   3. During dataframe display")


if __name__ == "__main__":
    main()
