"""Test suite for specialty filtering functionality.

Tests verify that:
- Unique specialties are correctly extracted from provider data
- Multi-specialty providers (comma-separated) are handled correctly
- Specialty filtering works with various combinations
- Missing/NaN specialty values are handled gracefully
"""
import pandas as pd
import pytest

from src.app_logic import filter_providers_by_specialty, get_unique_specialties


@pytest.fixture
def sample_provider_data():
    """Create sample provider data with various specialty configurations."""
    return pd.DataFrame([
        {
            "Full Name": "Dr. Smith",
            "Specialty": "Chiropractic",
            "Work Address": "123 Main St",
            "Latitude": 38.9,
            "Longitude": -77.0,
            "Referral Count": 10,
        },
        {
            "Full Name": "Dr. Jones",
            "Specialty": "Physical Therapy",
            "Work Address": "456 Oak Ave",
            "Latitude": 38.95,
            "Longitude": -77.05,
            "Referral Count": 15,
        },
        {
            "Full Name": "Dr. Johnson",
            "Specialty": "Chiropractic, Physical Therapy",  # Multi-specialty
            "Work Address": "789 Pine St",
            "Latitude": 39.0,
            "Longitude": -77.1,
            "Referral Count": 20,
        },
        {
            "Full Name": "Dr. Brown",
            "Specialty": "Neurology",
            "Work Address": "321 Elm St",
            "Latitude": 39.05,
            "Longitude": -77.15,
            "Referral Count": 8,
        },
        {
            "Full Name": "Dr. Davis",
            "Specialty": None,  # Missing specialty
            "Work Address": "654 Maple Dr",
            "Latitude": 39.1,
            "Longitude": -77.2,
            "Referral Count": 5,
        },
        {
            "Full Name": "Dr. Wilson",
            "Specialty": "Chiropractic/Physical Therapy",  # Alternative separator
            "Work Address": "987 Cedar Ln",
            "Latitude": 39.15,
            "Longitude": -77.25,
            "Referral Count": 12,
        },
    ])


def test_get_unique_specialties(sample_provider_data):
    """Test extracting unique specialties from provider data."""
    specialties = get_unique_specialties(sample_provider_data)
    
    # Should extract all unique specialties, handling comma-separated values
    assert "Chiropractic" in specialties
    assert "Physical Therapy" in specialties
    assert "Neurology" in specialties
    assert "Chiropractic/Physical Therapy" in specialties  # Alternative separator is kept as-is
    
    # Should be sorted
    assert specialties == sorted(specialties)


def test_get_unique_specialties_empty_df():
    """Test getting specialties from empty DataFrame."""
    empty_df = pd.DataFrame()
    specialties = get_unique_specialties(empty_df)
    assert specialties == []


def test_get_unique_specialties_no_specialty_column():
    """Test getting specialties when column doesn't exist."""
    df = pd.DataFrame([
        {"Full Name": "Dr. Test", "Referral Count": 5}
    ])
    specialties = get_unique_specialties(df)
    assert specialties == []


def test_get_unique_specialties_all_null():
    """Test getting specialties when all values are null."""
    df = pd.DataFrame([
        {"Full Name": "Dr. A", "Specialty": None},
        {"Full Name": "Dr. B", "Specialty": pd.NA},
        {"Full Name": "Dr. C", "Specialty": ""},
    ])
    specialties = get_unique_specialties(df)
    assert specialties == []


def test_filter_by_single_specialty(sample_provider_data):
    """Test filtering by a single specialty."""
    filtered = filter_providers_by_specialty(sample_provider_data, ["Chiropractic"])
    
    # Should include providers with Chiropractic (including multi-specialty)
    names = set(filtered["Full Name"].tolist())
    assert "Dr. Smith" in names  # Pure chiropractic
    assert "Dr. Johnson" in names  # Multi-specialty with comma
    assert "Dr. Jones" not in names  # Physical therapy only
    assert "Dr. Brown" not in names  # Neurology only
    assert "Dr. Davis" not in names  # No specialty
    assert "Dr. Wilson" not in names  # Uses "/" separator instead of ","


def test_filter_by_multiple_specialties(sample_provider_data):
    """Test filtering by multiple specialties."""
    filtered = filter_providers_by_specialty(
        sample_provider_data, 
        ["Chiropractic", "Physical Therapy"]
    )
    
    # Should include providers with either specialty
    names = set(filtered["Full Name"].tolist())
    assert "Dr. Smith" in names  # Chiropractic
    assert "Dr. Jones" in names  # Physical Therapy
    assert "Dr. Johnson" in names  # Both (comma-separated)
    assert "Dr. Brown" not in names  # Neurology
    assert "Dr. Davis" not in names  # No specialty
    assert "Dr. Wilson" not in names  # Uses "/" separator


def test_filter_by_all_specialties(sample_provider_data):
    """Test filtering with all specialties selected (inclusive approach)."""
    all_specialties = get_unique_specialties(sample_provider_data)
    filtered = filter_providers_by_specialty(sample_provider_data, all_specialties)
    
    # Should include all providers with any specialty
    assert len(filtered) == 5  # Excludes only Dr. Davis (no specialty)


def test_filter_by_empty_specialty_list(sample_provider_data):
    """Test that empty specialty list returns all providers."""
    filtered = filter_providers_by_specialty(sample_provider_data, [])
    
    # Empty list should return all providers (no filtering)
    assert len(filtered) == len(sample_provider_data)


def test_filter_by_none_specialty_list(sample_provider_data):
    """Test that None specialty list returns all providers."""
    filtered = filter_providers_by_specialty(sample_provider_data, None)
    
    # None should return all providers (no filtering)
    assert len(filtered) == len(sample_provider_data)


def test_filter_empty_dataframe():
    """Test filtering empty DataFrame."""
    empty_df = pd.DataFrame()
    filtered = filter_providers_by_specialty(empty_df, ["Chiropractic"])
    
    assert filtered.empty


def test_filter_no_specialty_column():
    """Test filtering when Specialty column doesn't exist."""
    df = pd.DataFrame([
        {"Full Name": "Dr. Test", "Referral Count": 5}
    ])
    filtered = filter_providers_by_specialty(df, ["Chiropractic"])
    
    # Should return all providers when column doesn't exist
    assert len(filtered) == len(df)


def test_filter_whitespace_handling():
    """Test that whitespace in specialties is handled correctly."""
    df = pd.DataFrame([
        {"Full Name": "Dr. A", "Specialty": "Chiropractic, Physical Therapy"},
        {"Full Name": "Dr. B", "Specialty": "Chiropractic,Physical Therapy"},  # No space after comma
        {"Full Name": "Dr. C", "Specialty": "  Chiropractic  ,  Physical Therapy  "},  # Extra whitespace
    ])
    
    filtered = filter_providers_by_specialty(df, ["Chiropractic"])
    
    # All should match because whitespace is stripped
    assert len(filtered) == 3


def test_multi_specialty_partial_match(sample_provider_data):
    """Test that multi-specialty providers match on any of their specialties."""
    # Dr. Johnson has "Chiropractic, Physical Therapy"
    
    # Should match on first specialty
    filtered1 = filter_providers_by_specialty(sample_provider_data, ["Chiropractic"])
    assert "Dr. Johnson" in filtered1["Full Name"].tolist()
    
    # Should match on second specialty
    filtered2 = filter_providers_by_specialty(sample_provider_data, ["Physical Therapy"])
    assert "Dr. Johnson" in filtered2["Full Name"].tolist()
    
    # Should match when both are selected
    filtered3 = filter_providers_by_specialty(
        sample_provider_data, 
        ["Chiropractic", "Physical Therapy"]
    )
    assert "Dr. Johnson" in filtered3["Full Name"].tolist()


def test_filter_preserves_dataframe_structure(sample_provider_data):
    """Test that filtering preserves all columns in the DataFrame."""
    filtered = filter_providers_by_specialty(sample_provider_data, ["Neurology"])
    
    # Should have same columns as original
    assert set(filtered.columns) == set(sample_provider_data.columns)
    
    # Should be a copy, not a view
    filtered["Test"] = "value"
    assert "Test" not in sample_provider_data.columns
