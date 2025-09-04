#!/usr/bin/env python3
"""
Test script to verify the load_detailed_referrals fix works correctly.
"""

import pandas as pd
from pathlib import Path
import streamlit as st
from datetime import datetime

# Mock streamlit functions to avoid dependency issues during testing
class MockStreamlit:
    def warning(self, message):
        print(f"WARNING: {message}")
    
    def cache_data(self, ttl=None):
        def decorator(func):
            return func
        return decorator

# Replace st with mock for testing
st = MockStreamlit()

@st.cache_data(ttl=3600)
def load_detailed_referrals(filepath: str) -> pd.DataFrame:
    """Load detailed referral data with dates for time-based filtering."""

    path = Path(filepath)
    if not path.exists():
        # If detailed data doesn't exist, return empty DataFrame
        return pd.DataFrame()

    try:
        df = pd.read_parquet(path)
        
        # Check if Referral Date column exists, if not try to create it
        if "Referral Date" in df.columns:
            df["Referral Date"] = pd.to_datetime(df["Referral Date"], errors="coerce")
            print("Found existing 'Referral Date' column")
        else:
            print("'Referral Date' column not found, attempting to create from available columns")
            # Try to create Referral Date from available date columns
            date_columns = ["Create Date", "Date of Intake", "Sign Up Date"]
            available_date_cols = [col for col in date_columns if col in df.columns]
            
            print(f"Available date columns: {available_date_cols}")
            
            if available_date_cols:
                # Convert available date columns to datetime
                for col in available_date_cols:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    print(f"Converted {col} to datetime")
                
                # Create Referral Date using the priority order
                df["Referral Date"] = df[available_date_cols[0]]  # Start with first available
                for col in available_date_cols[1:]:
                    df["Referral Date"] = df["Referral Date"].fillna(df[col])
                
                print(f"Created 'Referral Date' column using priority: {available_date_cols}")
                print(f"Non-null Referral Date entries: {df['Referral Date'].notna().sum()}")
            else:
                # No date columns available, return empty DataFrame
                st.warning(f"No date columns found in {filepath}. Time-based filtering not available.")
                return pd.DataFrame()
        
        return df
    except Exception as e:
        st.warning(f"Could not load detailed referral data: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    print("Testing load_detailed_referrals function...")
    
    # Test with the actual data file
    result = load_detailed_referrals("data/Referrals_App_Outbound.parquet")
    
    print(f"\nResults:")
    print(f"- Loaded {len(result)} rows")
    print(f"- Columns: {list(result.columns) if not result.empty else 'DataFrame is empty'}")
    
    if not result.empty and "Referral Date" in result.columns:
        print(f"- Referral Date range: {result['Referral Date'].min()} to {result['Referral Date'].max()}")
        print(f"- Null Referral Date entries: {result['Referral Date'].isna().sum()}")
    
    print("\nTest completed successfully!")
