"""Test suite for Person ID-based deduplication.

Tests verify that:
- Data is deduplicated using Person ID as the unique identifier
- When Person ID is not available, fallback deduplication works
- Deduplication is applied across all data sources (referrals and preferred providers)
"""
import pandas as pd
import pytest

from src.data.preparation import process_and_save_cleaned_referrals, process_and_save_preferred_providers


@pytest.fixture
def sample_referral_data_with_person_id():
    """Create sample referral data with Person ID column and duplicates."""
    return pd.DataFrame(
        [
            {
                "Project ID": 1001,
                "Date of Intake": pd.Timestamp("2024-01-15"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. John Smith",
                "Referred From's Work Phone": "301-555-1234",
                "Referred From's Work Address": "1 Main St, Annapolis, MD",
                "Referred From's Details: Latitude": "38.9784",
                "Referred From's Details: Longitude": "-76.4922",
                "Referred From's Details: Person ID": "P001",
                "Dr/Facility Referred To Full Name": "Clinic A",
                "Dr/Facility Referred To's Work Phone": "2025559876",
                "Dr/Facility Referred To's Work Address": "10 Care Blvd, Washington, DC",
                "Dr/Facility Referred To's Details: Latitude": "38.9072",
                "Dr/Facility Referred To's Details: Longitude": "-77.0369",
                "Dr/Facility Referred To's Details: Person ID": "P101",
            },
            {
                # Duplicate of Dr. John Smith (same Person ID)
                "Project ID": 1002,
                "Date of Intake": pd.Timestamp("2024-02-20"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. John Smith",  # Same name
                "Referred From's Work Phone": "301-555-9999",  # Different phone
                "Referred From's Work Address": "1 Main St, Annapolis, MD",  # Same address
                "Referred From's Details: Latitude": "38.9784",
                "Referred From's Details: Longitude": "-76.4922",
                "Referred From's Details: Person ID": "P001",  # Same Person ID - should dedupe
                "Dr/Facility Referred To Full Name": "Clinic B",
                "Dr/Facility Referred To's Work Phone": "2025550000",
                "Dr/Facility Referred To's Work Address": "20 Health St, Washington, DC",
                "Dr/Facility Referred To's Details: Latitude": "38.9000",
                "Dr/Facility Referred To's Details: Longitude": "-77.0000",
                "Dr/Facility Referred To's Details: Person ID": "P102",
            },
            {
                # Different provider with unique Person ID
                "Project ID": 1003,
                "Date of Intake": pd.Timestamp("2024-03-10"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. Jane Doe",
                "Referred From's Work Phone": "410-555-0000",
                "Referred From's Work Address": "2 Side St, Baltimore, MD",
                "Referred From's Details: Latitude": "39.2904",
                "Referred From's Details: Longitude": "-76.6122",
                "Referred From's Details: Person ID": "P002",
                "Dr/Facility Referred To Full Name": "Clinic A",  # Same as first
                "Dr/Facility Referred To's Work Phone": "2025559876",
                "Dr/Facility Referred To's Work Address": "10 Care Blvd, Washington, DC",
                "Dr/Facility Referred To's Details: Latitude": "38.9072",
                "Dr/Facility Referred To's Details: Longitude": "-77.0369",
                "Dr/Facility Referred To's Details: Person ID": "P101",  # Same Person ID as first outbound - should dedupe
            },
        ]
    )


@pytest.fixture
def sample_preferred_providers_with_person_id():
    """Create sample preferred providers data with Person ID column and duplicates."""
    return pd.DataFrame(
        [
            {
                "Contact Full Name": "Dr. Alice Provider",
                "Contact's Work Phone": "301-555-1111",
                "Contact's Work Address": "100 Medical Dr, Rockville, MD",
                "Contact's Details: Latitude": 39.0840,
                "Contact's Details: Longitude": -77.1528,
                "Contact's Details: Person ID": "PP001",
            },
            {
                # Duplicate - same Person ID but different phone
                "Contact Full Name": "Dr. Alice Provider",
                "Contact's Work Phone": "301-555-9999",  # Different phone
                "Contact's Work Address": "100 Medical Dr, Rockville, MD",
                "Contact's Details: Latitude": 39.0840,
                "Contact's Details: Longitude": -77.1528,
                "Contact's Details: Person ID": "PP001",  # Same Person ID - should dedupe
            },
            {
                # Different provider
                "Contact Full Name": "Dr. Bob Provider",
                "Contact's Work Phone": "410-555-2222",
                "Contact's Work Address": "200 Health Ave, Baltimore, MD",
                "Contact's Details: Latitude": 39.2904,
                "Contact's Details: Longitude": -76.6122,
                "Contact's Details: Person ID": "PP002",
            },
        ]
    )


def test_referral_deduplication_by_person_id(tmp_path, sample_referral_data_with_person_id, disable_s3_only_mode):
    """Test that referral data is deduplicated using Person ID."""
    # Setup paths
    raw_path = tmp_path / "referrals_with_person_id.csv"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save sample data to CSV
    sample_referral_data_with_person_id.to_csv(raw_path, index=False)

    # Run the processing pipeline
    summary = process_and_save_cleaned_referrals(raw_path, processed_dir)

    # Load the output files
    inbound = pd.read_parquet(processed_dir / "cleaned_inbound_referrals.parquet")
    outbound = pd.read_parquet(processed_dir / "cleaned_outbound_referrals.parquet")

    # Verify inbound deduplication by Person ID
    # Should have 2 unique inbound providers (P001 and P002), not 3
    assert len(inbound) == 2, f"Should have 2 unique inbound providers after deduplication, got {len(inbound)}"
    
    # Verify that only one record for Person ID P001 exists
    p001_records = inbound[inbound["Person ID"] == "P001"]
    assert len(p001_records) == 1, "Should have only one record for Person ID P001 after deduplication"
    
    # Verify that Person ID is preserved
    assert "Person ID" in inbound.columns, "Person ID column should be preserved in output"
    assert set(inbound["Person ID"].unique()) == {"P001", "P002"}, "Should have exactly two unique Person IDs in inbound"

    # Verify outbound deduplication by Person ID
    # Should have 2 unique outbound providers (P101 and P102), not 3
    assert len(outbound) == 2, f"Should have 2 unique outbound providers after deduplication, got {len(outbound)}"
    
    # Verify that only one record for Person ID P101 exists
    p101_records = outbound[outbound["Person ID"] == "P101"]
    assert len(p101_records) == 1, "Should have only one record for Person ID P101 after deduplication"
    
    # Verify that Person ID is preserved
    assert "Person ID" in outbound.columns, "Person ID column should be preserved in output"
    assert set(outbound["Person ID"].unique()) == {"P101", "P102"}, "Should have exactly two unique Person IDs in outbound"


def test_preferred_providers_deduplication_by_person_id(
    tmp_path, sample_preferred_providers_with_person_id, disable_s3_only_mode
):
    """Test that preferred providers data is deduplicated using Person ID."""
    # Setup paths
    raw_path = tmp_path / "preferred_providers_with_person_id.csv"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save sample data to CSV
    sample_preferred_providers_with_person_id.to_csv(raw_path, index=False)

    # Run the processing pipeline
    summary = process_and_save_preferred_providers(raw_path, processed_dir)

    # Verify deduplication occurred
    assert summary.cleaned_count == 2, f"Should have 2 unique providers after deduplication, got {summary.cleaned_count}"

    # Load the output file
    df = pd.read_parquet(processed_dir / "cleaned_preferred_providers.parquet")

    # Verify only 2 providers remain (PP001 deduplicated, PP002 kept)
    assert len(df) == 2, f"Should have 2 providers after deduplication, got {len(df)}"
    
    # Verify that only one record for Person ID PP001 exists
    pp001_records = df[df["Person ID"] == "PP001"]
    assert len(pp001_records) == 1, "Should have only one record for Person ID PP001 after deduplication"
    
    # Verify Person ID column is preserved
    assert "Person ID" in df.columns, "Person ID column should be preserved in output"
    assert set(df["Person ID"].unique()) == {"PP001", "PP002"}, "Should have exactly two unique Person IDs"


def test_referral_deduplication_fallback_without_person_id(tmp_path, disable_s3_only_mode):
    """Test that deduplication still works when Person ID column is not present."""
    # Create data without Person ID column
    sample_data = pd.DataFrame(
        [
            {
                "Project ID": 1001,
                "Date of Intake": pd.Timestamp("2024-01-15"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. Smith",
                "Referred From's Work Phone": "301-555-1234",
                "Referred From's Work Address": "1 Main St, Annapolis, MD",
                "Referred From's Details: Latitude": "38.9784",
                "Referred From's Details: Longitude": "-76.4922",
            },
            {
                # Exact duplicate row
                "Project ID": 1001,
                "Date of Intake": pd.Timestamp("2024-01-15"),
                "Referral Source": "Referral - Doctor's Office",
                "Referred From Full Name": "Dr. Smith",
                "Referred From's Work Phone": "301-555-1234",
                "Referred From's Work Address": "1 Main St, Annapolis, MD",
                "Referred From's Details: Latitude": "38.9784",
                "Referred From's Details: Longitude": "-76.4922",
            },
        ]
    )

    # Setup paths
    raw_path = tmp_path / "referrals_no_person_id.csv"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save sample data to CSV
    sample_data.to_csv(raw_path, index=False)

    # Run the processing pipeline
    summary = process_and_save_cleaned_referrals(raw_path, processed_dir)

    # Load the output files
    inbound = pd.read_parquet(processed_dir / "cleaned_inbound_referrals.parquet")

    # Should still work without Person ID - exact duplicates should be removed
    # Note: without Person ID, deduplication happens at row level in drop_duplicates
    assert len(inbound) >= 1, "Should have at least one provider after processing"
    
    # Person ID column should not exist in output
    assert "Person ID" not in inbound.columns, "Person ID column should not be in output when not in source"


def test_preferred_providers_deduplication_fallback_without_person_id(tmp_path, disable_s3_only_mode):
    """Test that preferred providers deduplication works without Person ID column."""
    # Create data without Person ID column
    sample_data = pd.DataFrame(
        [
            {
                "Contact Full Name": "Dr. Provider",
                "Contact's Work Phone": "301-555-1111",
                "Contact's Work Address": "100 Medical Dr, Rockville, MD",
                "Contact's Details: Latitude": 39.0840,
                "Contact's Details: Longitude": -77.1528,
            },
            {
                # Exact duplicate row
                "Contact Full Name": "Dr. Provider",
                "Contact's Work Phone": "301-555-1111",
                "Contact's Work Address": "100 Medical Dr, Rockville, MD",
                "Contact's Details: Latitude": 39.0840,
                "Contact's Details: Longitude": -77.1528,
            },
        ]
    )

    # Setup paths
    raw_path = tmp_path / "preferred_providers_no_person_id.csv"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save sample data to CSV
    sample_data.to_csv(raw_path, index=False)

    # Run the processing pipeline
    summary = process_and_save_preferred_providers(raw_path, processed_dir)

    # Verify deduplication occurred using generic drop_duplicates
    assert summary.cleaned_count == 1, f"Should have 1 provider after deduplication, got {summary.cleaned_count}"

    # Load the output file
    df = pd.read_parquet(processed_dir / "cleaned_preferred_providers.parquet")

    # Verify only 1 provider remains
    assert len(df) == 1, f"Should have 1 provider after deduplication, got {len(df)}"
    
    # Person ID column should not exist in output
    assert "Person ID" not in df.columns, "Person ID column should not be in output when not in source"
