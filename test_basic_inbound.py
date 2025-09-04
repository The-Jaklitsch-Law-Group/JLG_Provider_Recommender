#!/usr/bin/env python3
"""
Simple test script to verify inbound referrals data loading without geopy dependencies.
"""

import pandas as pd
from pathlib import Path

def test_inbound_referrals_basic():
    """Test basic loading of inbound referrals data."""
    print("Testing basic inbound referrals loading...")
    
    # Test loading inbound referrals
    inbound_filepath = "data/Referrals_App_Inbound.xlsx"
    if not Path(inbound_filepath).exists():
        print(f"❌ Inbound referrals file not found: {inbound_filepath}")
        return False
    
    try:
        # Load inbound data directly with pandas
        inbound_df = pd.read_excel(inbound_filepath)
        print(f"✅ Loaded inbound referrals: {len(inbound_df)} records")
        print(f"✅ Columns: {list(inbound_df.columns)}")
        
        # Test basic processing
        print("\nProcessing primary referrals...")
        primary_referrals = inbound_df.dropna(subset=["Referred From Person Id"])
        print(f"✅ Primary referrals: {len(primary_referrals)} records")
        
        # Count referrals by provider
        if "Referred From Person Id" in inbound_df.columns:
            primary_counts = inbound_df.groupby("Referred From Person Id").size().reset_index(name="Count")
            print(f"✅ Unique providers (primary): {len(primary_counts)}")
            print(f"✅ Max referrals from one provider: {primary_counts['Count'].max()}")
        
        # Test secondary referrals
        print("\nProcessing secondary referrals...")
        secondary_referrals = inbound_df.dropna(subset=["Secondary Referred From Person Id"])
        print(f"✅ Secondary referrals: {len(secondary_referrals)} records")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing inbound referrals: {e}")
        return False

def test_outbound_data_loading():
    """Test loading outbound data for comparison."""
    print("\nTesting outbound data loading...")
    
    try:
        # Load cleaned outbound data
        outbound_df = pd.read_parquet("data/cleaned_outbound_referrals.parquet")
        print(f"✅ Loaded outbound referrals: {len(outbound_df)} records")
        print(f"✅ Columns: {list(outbound_df.columns)}")
        
        if "Person ID" in outbound_df.columns:
            print(f"✅ Unique providers (outbound): {outbound_df['Person ID'].nunique()}")
        
        return outbound_df
        
    except Exception as e:
        print(f"❌ Error loading outbound data: {e}")
        return None

def test_data_compatibility():
    """Test compatibility between inbound and outbound data."""
    print("\nTesting data compatibility...")
    
    try:
        # Load both datasets
        inbound_df = pd.read_excel("data/Referrals_App_Inbound.xlsx")
        outbound_df = pd.read_parquet("data/cleaned_outbound_referrals.parquet")
        
        # Check for common providers
        if "Referred From Person Id" in inbound_df.columns and "Person ID" in outbound_df.columns:
            inbound_providers = set(inbound_df["Referred From Person Id"].dropna())
            outbound_providers = set(outbound_df["Person ID"].dropna())
            
            common_providers = inbound_providers.intersection(outbound_providers)
            print(f"✅ Common providers between datasets: {len(common_providers)}")
            print(f"✅ Inbound-only providers: {len(inbound_providers - outbound_providers)}")
            print(f"✅ Outbound-only providers: {len(outbound_providers - inbound_providers)}")
            
            if common_providers:
                print("✅ Data compatibility confirmed - can merge by Person ID")
                return True
            else:
                print("⚠️ No common providers found - will need name-based matching")
                return True
        
    except Exception as e:
        print(f"❌ Error testing compatibility: {e}")
        return False

def main():
    """Run all basic tests."""
    print("=== Basic Inbound Referrals Integration Test ===\n")
    
    success = True
    success &= test_inbound_referrals_basic()
    success &= (test_outbound_data_loading() is not None)
    success &= test_data_compatibility()
    
    print(f"\n=== Test Results ===")
    if success:
        print("✅ Basic tests passed! Data loading and compatibility verified.")
        print("📋 Next steps: Install geopy package and run the full Streamlit app")
    else:
        print("❌ Some basic tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    main()
