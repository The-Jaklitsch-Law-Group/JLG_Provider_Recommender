#!/usr/bin/env python3
"""
Test to reproduce the preferred provider bug.

According to the issue:
- All providers are being marked as preferred
- Only providers in the preferred providers file should be marked as preferred
"""

import pandas as pd
import sys

def test_preferred_provider_logic():
    """Test the preferred provider merge logic from app_logic.py"""
    
    # Simulate provider_df from outbound referrals (no Preferred Provider column)
    provider_df = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob', 'Dr. Charlie', 'Dr. David'],
        'Work Address': ['123 Main', '456 Oak', '789 Pine', '321 Elm'],
        'Referral Count': [5, 3, 2, 4]
    })
    
    print("=" * 60)
    print("TEST 1: Normal case - some providers are preferred")
    print("=" * 60)
    print("\nInitial provider_df:")
    print(provider_df)
    
    # Simulate preferred_df with only some providers
    preferred_df = pd.DataFrame({
        'Full Name': ['Dr. Bob', 'Dr. David'],
        'Specialty': ['Cardiology', 'Neurology']
    })
    
    print("\nPreferred providers (only Bob and David):")
    print(preferred_df)
    
    # Apply app_logic.py merge logic
    try:
        if preferred_df is not None and not preferred_df.empty and "Full Name" in preferred_df.columns:
            pref_cols = ["Full Name"]
            if "Specialty" in preferred_df.columns:
                pref_cols.append("Specialty")
            pref_data = preferred_df[pref_cols].drop_duplicates(subset=["Full Name"], keep="first")
            
            provider_df = provider_df.merge(
                pref_data, on="Full Name", how="outer", indicator=True, suffixes=("", "_pref")
            )
            provider_df["Preferred Provider"] = provider_df["_merge"].apply(
                lambda v: True if v in ("both", "right_only") else False
            )
            provider_df = provider_df.drop(columns=["_merge"])
        else:
            provider_df["Preferred Provider"] = provider_df.get("Preferred Provider", False)
    except Exception as e:
        print(f"Exception occurred: {e}")
        provider_df["Preferred Provider"] = provider_df.get("Preferred Provider", False)
    
    print("\nFinal result:")
    print(provider_df[['Full Name', 'Preferred Provider']])
    
    preferred_count = provider_df['Preferred Provider'].sum()
    expected_count = 2
    
    if preferred_count == expected_count:
        print(f"\n✅ PASS: {preferred_count} providers marked as preferred (expected {expected_count})")
    else:
        print(f"\n❌ FAIL: {preferred_count} providers marked as preferred (expected {expected_count})")
        return False
    
    # TEST 2: What if preferred_df contains ALL providers?
    print("\n" + "=" * 60)
    print("TEST 2: Bug case - preferred_df contains ALL providers")
    print("=" * 60)
    
    provider_df = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob', 'Dr. Charlie', 'Dr. David'],
        'Work Address': ['123 Main', '456 Oak', '789 Pine', '321 Elm'],
        'Referral Count': [5, 3, 2, 4]
    })
    
    # BUG: preferred_df contains ALL providers instead of just preferred ones
    preferred_df_bad = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob', 'Dr. Charlie', 'Dr. David'],
        'Specialty': ['Orthopedics', 'Cardiology', 'Dermatology', 'Neurology']
    })
    
    print("\nPreferred providers file (INCORRECTLY contains all providers):")
    print(preferred_df_bad)
    
    try:
        if preferred_df_bad is not None and not preferred_df_bad.empty and "Full Name" in preferred_df_bad.columns:
            pref_cols = ["Full Name"]
            if "Specialty" in preferred_df_bad.columns:
                pref_cols.append("Specialty")
            pref_data = preferred_df_bad[pref_cols].drop_duplicates(subset=["Full Name"], keep="first")
            
            provider_df = provider_df.merge(
                pref_data, on="Full Name", how="outer", indicator=True, suffixes=("", "_pref")
            )
            provider_df["Preferred Provider"] = provider_df["_merge"].apply(
                lambda v: True if v in ("both", "right_only") else False
            )
            provider_df = provider_df.drop(columns=["_merge"])
    except Exception as e:
        print(f"Exception occurred: {e}")
        provider_df["Preferred Provider"] = provider_df.get("Preferred Provider", False)
    
    print("\nFinal result:")
    print(provider_df[['Full Name', 'Preferred Provider']])
    
    all_preferred = provider_df['Preferred Provider'].all()
    
    if all_preferred:
        print(f"\n⚠️  BUG REPRODUCED: All {len(provider_df)} providers marked as preferred!")
        print("This would happen if the preferred providers file in S3 contains ALL providers")
        return False
    else:
        print(f"\n✅ No bug in this scenario")
    
    return True

if __name__ == "__main__":
    success = test_preferred_provider_logic()
    sys.exit(0 if success else 1)
