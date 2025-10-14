"""Test suite for Last Verified Date functionality.

Tests verify that:
- Last Verified Date fields are correctly mapped from source data
- Date normalization works for Last Verified Date
- Freshness indicators are calculated correctly
- Display formatting works as expected
"""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from src.data.preparation import process_and_save_cleaned_referrals
from src.utils.freshness import (
    calculate_data_age_days,
    get_freshness_indicator,
    format_last_verified_display,
)


@pytest.fixture
def sample_data_with_last_verified():
    """Create sample data with Last Verified Date fields."""
    return pd.DataFrame(
        [
            {
                "Project ID": 1001,
                "Date of Intake": pd.Timestamp("2024-01-15"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. Primary",
                "Referred From's Work Phone": "301-555-1234",
                "Referred From's Work Address": "1 Main St, Annapolis, MD",
                "Referred From's Details: Latitude": "38.9784",
                "Referred From's Details: Longitude": "-76.4922",
                "Referred From's Details: Last Verified Date": pd.Timestamp("2024-09-01"),
                "Dr/Facility Referred To Full Name": "Clinic Destination",
                "Dr/Facility Referred To's Work Phone": "2025559876",
                "Dr/Facility Referred To's Work Address": "10 Care Blvd, Washington, DC",
                "Dr/Facility Referred To's Details: Latitude": "38.9072",
                "Dr/Facility Referred To's Details: Longitude": "-77.0369",
                "Dr/Facility Referred To's Details: Last Verified Date": pd.Timestamp("2024-10-01"),
            },
            {
                "Project ID": 1002,
                "Date of Intake": pd.Timestamp("2024-02-01"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. Solo",
                "Referred From's Work Phone": "410-555-0000",
                "Referred From's Work Address": "3 Another Rd, Bowie, MD",
                "Referred From's Details: Latitude": "39.0068",
                "Referred From's Details: Longitude": "-76.7791",
                "Referred From's Details: Last Verified Date": pd.Timestamp("2023-12-01"),
                "Dr/Facility Referred To Full Name": "Therapy Partners",
                "Dr/Facility Referred To's Work Phone": "301-555-9999",
                "Dr/Facility Referred To's Work Address": "20 Wellness Ave, Greenbelt, MD",
                "Dr/Facility Referred To's Details: Latitude": "39.0046",
                "Dr/Facility Referred To's Details: Longitude": "-76.8755",
                "Dr/Facility Referred To's Details: Last Verified Date": pd.NaT,
            },
        ]
    )


def test_last_verified_date_mapping(tmp_path, sample_data_with_last_verified, disable_s3_only_mode):
    """Test that Last Verified Date fields are correctly mapped in data preparation."""
    # Setup paths
    raw_path = tmp_path / "Referrals_App_Full_Contacts.csv"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save sample data to CSV
    sample_data_with_last_verified.to_csv(raw_path, index=False)

    # Process the data
    summary = process_and_save_cleaned_referrals(raw_path, processed_dir)

    # Verify outbound data has Last Verified Date
    outbound_file = processed_dir / "cleaned_outbound_referrals.parquet"
    assert outbound_file.exists()

    outbound_df = pd.read_parquet(outbound_file)
    assert "Last Verified Date" in outbound_df.columns

    # Check that dates were properly mapped
    clinic_row = outbound_df[outbound_df["Full Name"] == "Clinic Destination"]
    assert len(clinic_row) > 0
    assert pd.notna(clinic_row.iloc[0]["Last Verified Date"])

    # Check for provider with missing Last Verified Date
    therapy_row = outbound_df[outbound_df["Full Name"] == "Therapy Partners"]
    assert len(therapy_row) > 0
    # Can be NaT or missing depending on how it's handled


def test_freshness_indicator_fresh():
    """Test freshness indicator for fresh data (within 90 days)."""
    recent_date = pd.Timestamp(datetime.now() - timedelta(days=30))
    indicator, status = get_freshness_indicator(recent_date)

    assert indicator == "✅"
    assert status == "Fresh"


def test_freshness_indicator_stale():
    """Test freshness indicator for stale data (90-180 days)."""
    stale_date = pd.Timestamp(datetime.now() - timedelta(days=120))
    indicator, status = get_freshness_indicator(stale_date)

    assert indicator == "⚠️"
    assert status == "Stale"


def test_freshness_indicator_very_stale():
    """Test freshness indicator for very stale data (>180 days)."""
    very_stale_date = pd.Timestamp(datetime.now() - timedelta(days=200))
    indicator, status = get_freshness_indicator(very_stale_date)

    assert indicator == "❌"
    assert status == "Very Stale"


def test_freshness_indicator_missing():
    """Test freshness indicator for missing date."""
    indicator, status = get_freshness_indicator(None)

    assert indicator == "❓"
    assert status == "Unknown"


def test_data_age_calculation():
    """Test data age calculation in days."""
    date_30_days_ago = pd.Timestamp(datetime.now() - timedelta(days=30))
    age = calculate_data_age_days(date_30_days_ago)

    assert age is not None
    assert 29 <= age <= 31  # Allow for test execution time


def test_data_age_missing():
    """Test data age calculation with missing date."""
    age = calculate_data_age_days(None)
    assert age is None


def test_format_last_verified_display():
    """Test formatted display of Last Verified Date."""
    test_date = pd.Timestamp("2024-01-15")
    formatted = format_last_verified_display(test_date, include_age=False, include_indicator=True)

    assert "2024-01-15" in formatted
    assert formatted.startswith(("✅", "⚠️", "❌"))  # Should have some indicator


def test_format_last_verified_display_with_age():
    """Test formatted display with age included."""
    test_date = pd.Timestamp(datetime.now() - timedelta(days=45))
    formatted = format_last_verified_display(test_date, include_age=True, include_indicator=True)

    assert "45 days ago" in formatted


def test_format_last_verified_display_missing():
    """Test formatted display for missing date."""
    formatted = format_last_verified_display(None)
    assert formatted == "Not Available"


def test_custom_thresholds():
    """Test freshness indicator with custom thresholds."""
    test_date = pd.Timestamp(datetime.now() - timedelta(days=100))

    # With default thresholds (90, 180), should be stale
    indicator1, status1 = get_freshness_indicator(test_date)
    assert status1 == "Stale"

    # With custom thresholds (120, 240), should be fresh
    indicator2, status2 = get_freshness_indicator(test_date, stale_threshold_days=120, very_stale_threshold_days=240)
    assert status2 == "Fresh"
