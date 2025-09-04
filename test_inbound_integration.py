#!/usr/bin/env python3
"""
Test script to verify inbound referrals integration works correctly.
This script tests the new functionality without running the full Streamlit app.
"""

import pandas as pd
import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from provider_utils import (
    load_inbound_referrals,
    calculate_inbound_referral_counts,
    load_provider_data,
    recommend_provider,
    calculate_distances
)

def test_inbound_referrals_loading():
    """Test loading and processing inbound referrals data."""
    print("Testing inbound referrals loading...")
    
    # Test loading inbound referrals
    inbound_filepath = "data/Referrals_App_Inbound.xlsx"
    if not Path(inbound_filepath).exists():
        print(f"❌ Inbound referrals file not found: {inbound_filepath}")
        return False
    
    try:
        inbound_df = load_inbound_referrals(inbound_filepath)
        print(f"✅ Loaded inbound referrals: {len(inbound_df)} records")
        
        if inbound_df.empty:
            print("❌ Inbound referrals dataframe is empty")
            return False
        
        # Test calculating inbound referral counts
        inbound_counts = calculate_inbound_referral_counts(inbound_df)
        print(f"✅ Calculated inbound counts: {len(inbound_counts)} providers")
        
        if not inbound_counts.empty:
            print("Top 5 providers by inbound referrals:")
            print(inbound_counts[['Full Name', 'Inbound Referral Count']].head())
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing inbound referrals: {e}")
        return False

def test_provider_data_merging():
    """Test merging inbound referrals with provider data."""
    print("\nTesting provider data merging...")
    
    try:
        # Load provider data
        provider_df = load_provider_data("data/cleaned_outbound_referrals.parquet")
        print(f"✅ Loaded provider data: {len(provider_df)} providers")
        
        # Load inbound referrals
        inbound_df = load_inbound_referrals("data/Referrals_App_Inbound.xlsx")
        inbound_counts = calculate_inbound_referral_counts(inbound_df)
        
        # Merge data
        if not inbound_counts.empty and not provider_df.empty:
            if "Person ID" in provider_df.columns and "Person ID" in inbound_counts.columns:
                merged_df = provider_df.merge(
                    inbound_counts[["Person ID", "Inbound Referral Count"]], 
                    on="Person ID", 
                    how="left"
                )
            else:
                merged_df = provider_df.merge(
                    inbound_counts[["Full Name", "Inbound Referral Count"]], 
                    on="Full Name", 
                    how="left"
                )
            
            merged_df["Inbound Referral Count"] = merged_df["Inbound Referral Count"].fillna(0)
            
            print(f"✅ Merged data: {len(merged_df)} providers")
            print(f"✅ Providers with inbound referrals: {(merged_df['Inbound Referral Count'] > 0).sum()}")
            
            # Show summary statistics
            print(f"✅ Max inbound referrals: {merged_df['Inbound Referral Count'].max()}")
            print(f"✅ Mean inbound referrals: {merged_df['Inbound Referral Count'].mean():.2f}")
            
            return merged_df
        
    except Exception as e:
        print(f"❌ Error merging data: {e}")
        return None

def test_three_factor_scoring():
    """Test the new three-factor scoring algorithm."""
    print("\nTesting three-factor scoring...")
    
    try:
        merged_df = test_provider_data_merging()
        if merged_df is None:
            return False
        
        # Add fake distance data for testing
        merged_df["Distance (Miles)"] = [1.0, 2.0, 3.0, 4.0, 5.0][:len(merged_df)]
        
        # Test three-factor recommendation
        best, scored_df = recommend_provider(
            merged_df.head(5),  # Use first 5 providers for testing
            distance_weight=0.4,
            referral_weight=0.4, 
            inbound_weight=0.2,
            min_referrals=0
        )
        
        if best is not None and scored_df is not None:
            print("✅ Three-factor scoring works!")
            print(f"✅ Best provider: {best['Full Name']}")
            print(f"✅ Score: {best['Score']:.3f}")
            
            # Show top 3 providers
            print("\nTop 3 providers by score:")
            display_cols = ["Full Name", "Distance (Miles)", "Referral Count", "Inbound Referral Count", "Score"]
            available_cols = [col for col in display_cols if col in scored_df.columns]
            print(scored_df[available_cols].head(3))
            
            return True
        else:
            print("❌ Three-factor scoring returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error in three-factor scoring: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Testing Inbound Referrals Integration ===\n")
    
    success = True
    success &= test_inbound_referrals_loading()
    success &= (test_provider_data_merging() is not None)
    success &= test_three_factor_scoring()
    
    print(f"\n=== Test Results ===")
    if success:
        print("✅ All tests passed! Inbound referrals integration is working.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    main()
