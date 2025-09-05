#!/usr/bin/env python3
"""Debug script to isolate the 'Full Name' field error."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Test the individual components
    print("Testing data loading components...")
    
    from src.data.ingestion import load_provider_data, load_detailed_referrals
    
    print("1. Loading provider data...")
    provider_df = load_provider_data()
    print(f"   Provider data shape: {provider_df.shape}")
    print(f"   Provider data columns: {list(provider_df.columns)}")
    print(f"   Has 'Full Name': {'Full Name' in provider_df.columns}")
    
    print("\n2. Loading detailed referrals...")
    detailed_df = load_detailed_referrals()
    print(f"   Detailed data shape: {detailed_df.shape}")
    print(f"   Detailed data columns: {list(detailed_df.columns)}")
    print(f"   Has 'Full Name': {'Full Name' in detailed_df.columns}")
    
    print("\n3. Testing validation function...")
    from src.utils.providers import validate_provider_data
    
    is_valid, message = validate_provider_data(provider_df)
    print(f"   Validation result: {is_valid}")
    print(f"   Validation message: {message}")
    
    print("\n4. Testing calculate_referral_counts function...")
    def calculate_referral_counts(provider_df, detailed_df):
        """Calculate referral counts if missing from provider data."""
        if not detailed_df.empty and "Full Name" in detailed_df.columns:
            print(f"   Found 'Full Name' in detailed_df with {len(detailed_df)} rows")
            referral_counts = detailed_df.groupby("Full Name").size().reset_index(name="Referral Count")
            print(f"   Calculated referral counts for {len(referral_counts)} providers")
            # Merge with provider data
            provider_df = provider_df.merge(referral_counts, on="Full Name", how="left")
            provider_df["Referral Count"] = provider_df["Referral Count"].fillna(0)
            print(f"   Merged results: {provider_df.shape}")
        else:
            print(f"   No 'Full Name' in detailed_df or detailed_df is empty")
            # If no detailed referral data, set all counts to 0
            provider_df["Referral Count"] = 0
        
        return provider_df
    
    # Test referral count calculation
    if "Referral Count" not in provider_df.columns:
        print("   'Referral Count' not in provider_df, calculating...")
        provider_df = calculate_referral_counts(provider_df, detailed_df)
        print(f"   After calculation: 'Referral Count' in columns: {'Referral Count' in provider_df.columns}")
    else:
        print("   'Referral Count' already in provider_df")
    
    print("\n✅ All tests completed successfully!")
    print("The 'Full Name' field should be available.")
    
except Exception as e:
    print(f"\n❌ Error occurred: {e}")
    import traceback
    print(f"Traceback: {traceback.format_exc()}")
