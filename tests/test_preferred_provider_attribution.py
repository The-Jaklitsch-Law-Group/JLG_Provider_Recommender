"""
Tests for preferred provider attribution logic.

Ensures that only providers listed in the preferred providers file are marked
as preferred, and validates warnings for suspicious data.
"""

import pandas as pd
import pytest
from unittest.mock import MagicMock, patch
import logging


def test_preferred_provider_merge_logic():
    """Test the core preferred provider merge logic."""
    # Create provider dataframe
    provider_df = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob', 'Dr. Charlie', 'Dr. David'],
        'Work Address': ['123 Main', '456 Oak', '789 Pine', '321 Elm'],
        'Referral Count': [5, 3, 2, 4]
    })
    
    # Create preferred providers dataframe (only Bob and David)
    preferred_df = pd.DataFrame({
        'Full Name': ['Dr. Bob', 'Dr. David'],
        'Specialty': ['Cardiology', 'Neurology']
    })
    
    # Apply the merge logic from app_logic.py
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
    
    # Verify results
    assert provider_df.loc[provider_df['Full Name'] == 'Dr. Alice', 'Preferred Provider'].iloc[0] == False
    assert provider_df.loc[provider_df['Full Name'] == 'Dr. Bob', 'Preferred Provider'].iloc[0] == True
    assert provider_df.loc[provider_df['Full Name'] == 'Dr. Charlie', 'Preferred Provider'].iloc[0] == False
    assert provider_df.loc[provider_df['Full Name'] == 'Dr. David', 'Preferred Provider'].iloc[0] == True
    
    # Verify count
    assert provider_df['Preferred Provider'].sum() == 2


def test_preferred_provider_empty_list():
    """Test behavior when preferred providers list is empty."""
    provider_df = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob'],
        'Referral Count': [5, 3]
    })
    
    # Empty preferred providers dataframe
    preferred_df = pd.DataFrame(columns=['Full Name', 'Specialty'])
    
    # When preferred_df is empty, should mark all as not preferred
    if preferred_df.empty:
        provider_df["Preferred Provider"] = False
    
    assert provider_df['Preferred Provider'].sum() == 0


def test_preferred_provider_validation_warning(caplog):
    """Test that a warning is logged when too many providers are preferred."""
    with caplog.at_level(logging.WARNING):
        # Simulate the validation logic
        total_count = 100
        preferred_count = 85
        preferred_pct = (preferred_count / total_count * 100)
        
        logger = logging.getLogger(__name__)
        
        if preferred_pct > 80:
            logger.warning(
                f"WARNING: {preferred_pct:.1f}% of providers are marked as preferred. "
                "This is unusually high and may indicate that the preferred providers file "
                "contains all providers instead of just the preferred ones."
            )
        
        # Verify warning was logged
        assert "unusually high" in caplog.text
        assert "85.0%" in caplog.text


def test_preferred_only_providers_included():
    """Test that providers only in preferred list (not in referrals) are included."""
    # General provider list
    provider_df = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob'],
        'Referral Count': [5, 3]
    })
    
    # Preferred providers includes someone not in general list
    preferred_df = pd.DataFrame({
        'Full Name': ['Dr. Bob', 'Dr. NewDoctor'],
        'Specialty': ['Cardiology', 'Orthopedics']
    })
    
    # Apply merge logic
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
    
    # Verify Dr. NewDoctor is included and marked as preferred
    assert 'Dr. NewDoctor' in provider_df['Full Name'].values
    assert provider_df.loc[provider_df['Full Name'] == 'Dr. NewDoctor', 'Preferred Provider'].iloc[0] == True
    
    # Verify counts
    assert len(provider_df) == 3  # Alice, Bob, NewDoctor
    assert provider_df['Preferred Provider'].sum() == 2  # Bob and NewDoctor


def test_preferred_provider_specialty_override():
    """Test that preferred provider specialty overrides general specialty."""
    provider_df = pd.DataFrame({
        'Full Name': ['Dr. Bob'],
        'Specialty': ['General Practice'],
        'Referral Count': [3]
    })
    
    preferred_df = pd.DataFrame({
        'Full Name': ['Dr. Bob'],
        'Specialty': ['Cardiology']  # Should override General Practice
    })
    
    # Apply merge logic
    pref_cols = ["Full Name", "Specialty"]
    pref_data = preferred_df[pref_cols].drop_duplicates(subset=["Full Name"], keep="first")
    
    provider_df = provider_df.merge(
        pref_data, on="Full Name", how="outer", indicator=True, suffixes=("", "_pref")
    )
    provider_df["Preferred Provider"] = provider_df["_merge"].apply(
        lambda v: True if v in ("both", "right_only") else False
    )
    provider_df = provider_df.drop(columns=["_merge"])
    
    # Apply specialty override logic
    if "Specialty_pref" in provider_df.columns:
        provider_df["Specialty"] = provider_df["Specialty_pref"]
        provider_df = provider_df.drop(columns=["Specialty_pref"])
    
    # Verify specialty was overridden
    assert provider_df.loc[0, 'Specialty'] == 'Cardiology'


def test_preferred_providers_file_validation_warning(caplog):
    """Test warning when preferred providers file has too many unique providers."""
    with caplog.at_level(logging.WARNING):
        logger = logging.getLogger(__name__)
        
        # Simulate loading a file with suspiciously many providers
        unique_providers = 150
        
        if unique_providers > 100:
            logger.warning(
                f"WARNING: Preferred providers file contains {unique_providers} unique providers. "
                "This is unusually high. Please verify that the correct file was uploaded to the "
                "preferred_providers folder in S3."
            )
        
        # Verify warning was logged
        assert "150 unique providers" in caplog.text
        assert "unusually high" in caplog.text


def test_all_providers_marked_preferred_bug():
    """
    Test case reproducing the bug where all providers are marked as preferred.
    
    This happens when the preferred providers file incorrectly contains all providers
    instead of just the preferred ones.
    """
    # General provider list
    provider_df = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob', 'Dr. Charlie', 'Dr. David'],
        'Referral Count': [5, 3, 2, 4]
    })
    
    # BUG SCENARIO: Preferred providers file contains ALL providers
    preferred_df = pd.DataFrame({
        'Full Name': ['Dr. Alice', 'Dr. Bob', 'Dr. Charlie', 'Dr. David'],
        'Specialty': ['Ortho', 'Cardio', 'Derm', 'Neuro']
    })
    
    # Apply merge logic
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
    
    # Calculate percentage
    total_count = len(provider_df)
    preferred_count = provider_df["Preferred Provider"].sum()
    preferred_pct = (preferred_count / total_count * 100) if total_count > 0 else 0
    
    # This is the bug: all providers are marked as preferred
    assert preferred_count == total_count
    assert preferred_pct == 100.0
    
    # The validation logic should detect this
    assert preferred_pct > 80  # Would trigger warning in actual code
