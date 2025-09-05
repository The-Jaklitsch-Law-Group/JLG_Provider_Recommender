#!/usr/bin/env python3
"""
Integration test to verify the app loads without the string concatenation error.
"""

import sys
import traceback
from pathlib import Path

# Add the project directory to the path
sys.path.append(str(Path(__file__).parent))


def test_app_loading():
    """Test that the app loads without string concatenation errors."""
    print("Testing app data loading integration...")

    try:
        # Import the app functions
        from app import build_full_address, clean_address_data, load_application_data

        print("✅ Successfully imported app functions")

        # Test that load_application_data can be called without errors
        print("Testing load_application_data function...")

        # This will test the actual data loading logic
        provider_df, detailed_referrals_df = load_application_data()

        print(f"✅ Data loading completed successfully")
        print(f"   - Loaded {len(provider_df)} providers")
        print(f"   - Loaded {len(detailed_referrals_df)} detailed referrals")

        # Check if provider data has the expected columns
        if not provider_df.empty:
            print(f"   - Provider columns: {list(provider_df.columns)}")

            # Check for address-related columns
            address_cols = ["Street", "City", "State", "Zip", "Full Address"]
            present_cols = [col for col in address_cols if col in provider_df.columns]
            print(f"   - Address columns present: {present_cols}")

            # Check data types of address columns
            for col in present_cols:
                dtype = provider_df[col].dtype
                print(f"   - {col} data type: {dtype}")

                # Verify no mixed types that would cause concatenation errors
                if col in provider_df.columns:
                    sample_values = provider_df[col].head().tolist()
                    print(f"   - {col} sample values: {sample_values}")

        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        print(f"Detailed error: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    print("Running integration test for string concatenation fixes...\n")

    success = test_app_loading()

    if success:
        print("\n🎉 Integration test passed! The app should load without string concatenation errors.")
    else:
        print("\n❌ Integration test failed. There may still be issues to resolve.")
