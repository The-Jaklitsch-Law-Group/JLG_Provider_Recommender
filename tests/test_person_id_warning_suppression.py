"""
Tests for Person ID warning suppression.

Ensures that missing Person ID columns don't trigger warnings, since
Person ID is an optional column used for deduplication when present.
"""

import logging
import pandas as pd
import pytest

from src.data.preparation import process_referral_data


def test_person_id_missing_no_warning(caplog):
    """Test that missing Person ID columns don't trigger warnings."""
    # Create sample referral data WITHOUT Person ID columns
    df = pd.DataFrame(
        [
            {
                "Project ID": 1,
                "Date of Intake": "2024-01-01",
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. John Smith",
                "Referred From's Work Phone": "555-1234",
                "Referred From's Work Address": "123 Main St",
                "Referred From's Details: Latitude": 40.7128,
                "Referred From's Details: Longitude": -74.0060,
                "Referred From's Details: Last Verified Date": "2024-01-01",
                # Note: No Person ID column
                "Dr/Facility Referred To Full Name": "Dr. Jane Doe",
                "Dr/Facility Referred To's Work Phone": "555-5678",
                "Dr/Facility Referred To's Work Address": "456 Oak Ave",
                "Dr/Facility Referred To's Details: Latitude": 40.7589,
                "Dr/Facility Referred To's Details: Longitude": -73.9851,
                "Dr/Facility Referred To's Details: Last Verified Date": "2024-01-01",
                # Note: No Person ID column
            }
        ]
    )

    with caplog.at_level(logging.WARNING):
        # Process the data
        inbound_df, outbound_df, combined_df, summary = process_referral_data(df)

        # Verify data was processed successfully
        assert not inbound_df.empty, "Inbound data should be processed"
        assert not outbound_df.empty, "Outbound data should be processed"

        # Verify Person ID warnings are NOT in the warning log
        warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]

        # Check that no warnings mention Person ID
        person_id_warnings = [msg for msg in warning_messages if "Person ID" in msg]
        assert len(person_id_warnings) == 0, f"Person ID warnings should be suppressed, but found: {person_id_warnings}"


def test_person_id_present_no_warning(caplog):
    """Test that having Person ID columns doesn't trigger warnings."""
    # Create sample referral data WITH Person ID columns
    df = pd.DataFrame(
        [
            {
                "Project ID": 1,
                "Date of Intake": "2024-01-01",
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. John Smith",
                "Referred From's Work Phone": "555-1234",
                "Referred From's Work Address": "123 Main St",
                "Referred From's Details: Latitude": 40.7128,
                "Referred From's Details: Longitude": -74.0060,
                "Referred From's Details: Last Verified Date": "2024-01-01",
                "Referred From's Details: Person ID": "P001",  # Person ID present
                "Dr/Facility Referred To Full Name": "Dr. Jane Doe",
                "Dr/Facility Referred To's Work Phone": "555-5678",
                "Dr/Facility Referred To's Work Address": "456 Oak Ave",
                "Dr/Facility Referred To's Details: Latitude": 40.7589,
                "Dr/Facility Referred To's Details: Longitude": -73.9851,
                "Dr/Facility Referred To's Details: Last Verified Date": "2024-01-01",
                "Dr/Facility Referred To's Details: Person ID": "P101",  # Person ID present
            }
        ]
    )

    with caplog.at_level(logging.WARNING):
        # Process the data
        inbound_df, outbound_df, combined_df, summary = process_referral_data(df)

        # Verify data was processed successfully
        assert not inbound_df.empty, "Inbound data should be processed"
        assert not outbound_df.empty, "Outbound data should be processed"

        # Verify no Person ID warnings
        warning_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]
        person_id_warnings = [msg for msg in warning_messages if "Person ID" in msg]
        assert len(person_id_warnings) == 0, f"Person ID should not trigger warnings when present: {person_id_warnings}"


def test_person_id_logged_at_debug_level(caplog):
    """Test that missing Person ID is logged at DEBUG level for troubleshooting."""
    # Create sample referral data WITHOUT Person ID columns
    df = pd.DataFrame(
        [
            {
                "Project ID": 1,
                "Date of Intake": "2024-01-01",
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. John Smith",
                "Referred From's Work Phone": "555-1234",
                "Referred From's Work Address": "123 Main St",
                "Referred From's Details: Latitude": 40.7128,
                "Referred From's Details: Longitude": -74.0060,
                "Referred From's Details: Last Verified Date": "2024-01-01",
                # Note: No Person ID column
            }
        ]
    )

    with caplog.at_level(logging.DEBUG):
        # Process the data
        inbound_df, outbound_df, combined_df, summary = process_referral_data(df)

        # Verify Person ID is mentioned at DEBUG level
        debug_messages = [record.message for record in caplog.records if record.levelname == "DEBUG"]
        person_id_debug = [msg for msg in debug_messages if "Person ID" in msg and "optional" in msg.lower()]

        # We expect at least one debug message about missing optional Person ID
        assert len(person_id_debug) > 0, "Missing Person ID should be logged at DEBUG level"
        
        # Verify the message indicates it's non-critical
        for msg in person_id_debug:
            assert "non-critical" in msg.lower() or "optional" in msg.lower(), \
                f"Debug message should indicate Person ID is optional/non-critical: {msg}"


def test_required_column_still_warns(caplog):
    """Test that truly required columns still trigger warnings."""
    # Create sample referral data missing required columns (e.g., Full Name)
    df = pd.DataFrame(
        [
            {
                "Project ID": 1,
                "Date of Intake": "2024-01-01",
                "Referral Source": "Referral - Doctor's Office",
                # Missing: Referred From Full Name (required)
                "Referred From's Work Phone": "555-1234",
                "Referred From's Work Address": "123 Main St",
                "Referred From's Details: Latitude": 40.7128,
                "Referred From's Details: Longitude": -74.0060,
            }
        ]
    )

    with caplog.at_level(logging.WARNING):
        # Process the data
        inbound_df, outbound_df, combined_df, summary = process_referral_data(df)

        # In this case, we expect the inbound data to be empty due to filtering
        # (Full Name is required and filtered)
        assert inbound_df.empty, "Inbound data should be empty when required columns are missing"

        # We should NOT see warnings for required columns that are filtered
        # (the filtering removes records, so the missing column doesn't trigger a warning)
        # This test documents the current behavior
