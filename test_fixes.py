#!/usr/bin/env python3
"""
Test script to verify the string concatenation fixes.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add the project directory to the path
sys.path.append(str(Path(__file__).parent))

from app import build_full_address, clean_address_data


def test_clean_address_data():
    """Test the clean_address_data function with various edge cases."""
    print("Testing clean_address_data function...")

    # Create test data with problematic values
    test_data = pd.DataFrame(
        {
            "Street": ["123 Main St", np.nan, "None", 456, ""],
            "City": ["Baltimore", "NaN", None, "Annapolis", "null"],
            "State": ["MD", "MD", "NULL", np.nan, "VA"],
            "Zip": [21201, np.nan, "21202", "NULL", ""],
            "Full Name": ["Dr. Smith", "Dr. Jones", "Dr. Brown", "Dr. Wilson", "Dr. Davis"],
        }
    )

    print("Original data:")
    print(test_data)
    print(f"Data types:\n{test_data.dtypes}")

    # Clean the data
    cleaned_data = clean_address_data(test_data)

    print("\nCleaned data:")
    print(cleaned_data)
    print(f"Data types:\n{cleaned_data.dtypes}")

    # Verify all address columns are strings
    address_cols = ["Street", "City", "State", "Zip"]
    for col in address_cols:
        if col in cleaned_data.columns:
            assert cleaned_data[col].dtype == "object", f"{col} should be string type"
            # Check no 'nan' strings remain
            assert not any(cleaned_data[col].str.contains("nan", na=False)), f"{col} contains 'nan' strings"

    print("✅ clean_address_data test passed!")
    return cleaned_data


def test_build_full_address():
    """Test the build_full_address function."""
    print("\nTesting build_full_address function...")

    # Create test data with mixed address completeness
    test_data = pd.DataFrame(
        {
            "Street": ["123 Main St", "456 Oak Ave", "", "789 Pine St", ""],
            "City": ["Baltimore", "", "Annapolis", "Frederick", "Rockville"],
            "State": ["MD", "MD", "MD", "", "MD"],
            "Zip": ["21201", "21202", "", "21703", "20850"],
            "Full Name": ["Dr. Smith", "Dr. Jones", "Dr. Brown", "Dr. Wilson", "Dr. Davis"],
        }
    )

    print("Test data before building addresses:")
    print(test_data)

    # Build full addresses
    result_data = build_full_address(test_data)

    print("\nData after building full addresses:")
    print(result_data[["Full Name", "Street", "City", "State", "Zip", "Full Address"]])

    # Verify Full Address column was created
    assert "Full Address" in result_data.columns, "Full Address column should be created"

    # Check specific cases
    assert result_data.loc[0, "Full Address"] == "123 Main St, Baltimore, MD, 21201"
    assert result_data.loc[4, "Full Address"] == "Rockville, MD, 20850"  # Missing street

    print("✅ build_full_address test passed!")
    return result_data


def test_string_concatenation_safety():
    """Test that string concatenation doesn't fail with mixed types."""
    print("\nTesting string concatenation safety...")

    # Create problematic data that would cause the original error
    problematic_data = pd.DataFrame(
        {
            "Street": [123, np.nan, "None", "456 Oak St"],  # Mixed int/string/nan
            "City": ["Baltimore", None, 789, "Annapolis"],  # Mixed types
            "State": ["MD", "MD", np.nan, "MD"],
            "Zip": [21201, "21202", np.nan, None],  # Mixed int/string/nan
            "Full Name": ["Dr. A", "Dr. B", "Dr. C", "Dr. D"],
        }
    )

    print("Problematic data (mixed types):")
    print(problematic_data)
    print(f"Data types:\n{problematic_data.dtypes}")

    try:
        # Clean and build addresses - this should not raise an error
        cleaned = clean_address_data(problematic_data)
        with_addresses = build_full_address(cleaned)

        print("\nSuccessfully processed mixed-type data:")
        print(with_addresses[["Full Name", "Full Address"]])
        print("✅ String concatenation safety test passed!")
        return True

    except Exception as e:
        print(f"❌ String concatenation safety test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Running string concatenation fix tests...\n")

    try:
        # Test individual functions
        cleaned_data = test_clean_address_data()
        addressed_data = test_build_full_address()
        safety_passed = test_string_concatenation_safety()

        if safety_passed:
            print("\n🎉 All tests passed! The string concatenation fixes are working correctly.")
        else:
            print("\n❌ Some tests failed. Please check the implementation.")

    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
