"""Unified referral data cleaning script.

This script consolidates the cleaning and preparation workflows for both inbound and outbound
referral datasets, processing them into a single comprehensive parquet file.

Features:
- Processes both inbound and outbound referral data
- Standardizes column names and data types
- Aggregates referral counts by provider
- Combines datasets with proper source identification
- Outputs a single consolidated parquet file

Usage:
    python prepare_contacts/unified_referral_cleaning.py

Input files:
    - data/raw/Referrals_App_Inbound.xlsx
    - data/raw/Referrals_App_Outbound.xlsx

Output files:
    - data/processed/unified_referrals.parquet
    - data/processed/unified_referrals_detailed.parquet (with individual referral records)
"""

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def clean_numeric_columns(df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
    """Clean numeric columns by converting to proper numeric format and handling invalid values."""
    df_clean = df.copy()
    for col in numeric_columns:
        if col in df_clean.columns:
            # Convert to numeric, replacing invalid values with NaN
            df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
    return df_clean


def standardize_text_columns(df: pd.DataFrame, text_columns: List[str]) -> pd.DataFrame:
    """Standardize text columns by stripping whitespace and applying title case."""
    df_clean = df.copy()
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip().str.title()
    return df_clean


def standardize_state_column(df: pd.DataFrame, state_column: str) -> pd.DataFrame:
    """Standardize state column by stripping whitespace and applying uppercase."""
    df_clean = df.copy()
    if state_column in df_clean.columns:
        df_clean[state_column] = df_clean[state_column].astype(str).str.strip().str.upper()
    return df_clean


def standardize_date_columns(df: pd.DataFrame, date_columns: List[str]) -> pd.DataFrame:
    """Convert date columns to proper datetime format."""
    df_clean = df.copy()
    for col in date_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors="coerce")
    return df_clean


def process_outbound_referrals(file_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Process outbound referral data (cases referred by JLG to other providers).

    Returns:
        Tuple of (aggregated_data, detailed_data)
    """
    print(f"Processing outbound referrals from: {file_path}")

    # Read raw data
    df_out = pd.read_excel(file_path)

    # Define columns for text standardization
    text_cols = [
        "Dr/Facility Referred To Full Name",
        "Dr/Facility Referred To Address 1 Line 1",
        "Dr/Facility Referred To Address 1 City",
    ]

    # Standardize text columns
    df_out = standardize_text_columns(df_out, text_cols)

    # Standardize state column
    df_out = standardize_state_column(df_out, "Dr/Facility Referred To Address 1 State")

    # Standardize date columns
    date_cols = ["Create Date", "Date of Intake"]
    df_out = standardize_date_columns(df_out, date_cols)

    # Clean numeric columns (latitude/longitude)
    numeric_cols = ["Dr/Facility Referred To's Details: Latitude", "Dr/Facility Referred To's Details: Longitude"]
    df_out = clean_numeric_columns(df_out, numeric_cols)

    # Remove rows with missing Person ID
    df_out = df_out[df_out["Dr/Facility Referred To Person Id"].notna()]

    # Create referral date (use Create Date as primary, Date of Intake as fallback)
    df_out["Referral Date"] = df_out["Create Date"].fillna(df_out["Date of Intake"])

    # Define grouping columns for provider aggregation
    provider_cols = [
        "Dr/Facility Referred To Person Id",
        "Dr/Facility Referred To Full Name",
        "Dr/Facility Referred To Address 1 Line 1",
        "Dr/Facility Referred To Address 1 City",
        "Dr/Facility Referred To Address 1 State",
        "Dr/Facility Referred To Address 1 Zip",
        "Dr/Facility Referred To's Details: Latitude",
        "Dr/Facility Referred To's Details: Longitude",
        "Dr/Facility Referred To Phone 1",
    ]

    # Create detailed dataset for time-based analysis
    detailed_cols = provider_cols + ["Referral Date", "Project ID"]
    detailed_out = df_out[detailed_cols].copy()
    detailed_out = detailed_out[detailed_out["Referral Date"].notna()]

    # Aggregate by provider
    df_out_grouped = df_out.groupby(provider_cols, as_index=False, sort=False)["Project ID"].count()
    df_out_agg = df_out_grouped.rename(columns={"Project ID": "Referral Count"})  # type: ignore
    df_out_agg = df_out_agg.sort_values(by="Referral Count", ascending=False)

    # Standardize column names
    outbound_col_mapping = {
        "Dr/Facility Referred To Person Id": "Person ID",
        "Dr/Facility Referred To Full Name": "Full Name",
        "Dr/Facility Referred To Address 1 Line 1": "Street",
        "Dr/Facility Referred To Address 1 City": "City",
        "Dr/Facility Referred To Address 1 State": "State",
        "Dr/Facility Referred To Address 1 Zip": "Zip",
        "Dr/Facility Referred To's Details: Latitude": "Latitude",
        "Dr/Facility Referred To's Details: Longitude": "Longitude",
        "Dr/Facility Referred To Phone 1": "Phone Number",
    }

    df_out_agg = df_out_agg.rename(columns=outbound_col_mapping)
    detailed_out = detailed_out.rename(columns=outbound_col_mapping)

    # Add source identifier
    df_out_agg["Referral Type"] = "Outbound"
    df_out_agg["Description"] = "Cases referred by JLG to this provider"

    detailed_out["Referral Type"] = "Outbound"
    detailed_out["Description"] = "Cases referred by JLG to this provider"

    print(f"Processed {len(df_out_agg)} unique outbound providers from {len(df_out)} referrals")

    return df_out_agg, detailed_out


def process_inbound_referrals(file_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Process inbound referral data (cases referred to JLG by other providers).

    Returns:
        Tuple of (aggregated_data, detailed_data)
    """
    print(f"Processing inbound referrals from: {file_path}")

    # Read raw data
    df_in = pd.read_excel(file_path)

    # Standardize date columns
    date_cols = ["Create Date", "Date of Intake"]
    df_in = standardize_date_columns(df_in, date_cols)

    # Create referral date
    df_in["Referral Date"] = df_in["Create Date"].fillna(df_in["Date of Intake"])

    # Define shared columns for both primary and secondary referrers
    shared_cols = ["Project ID", "Create Date", "Date of Intake", "Referral Date"]

    # Primary referrer columns
    primary_cols = [
        "Referral Source",
        "Referred From Person Id",
        "Referred From Full Name",
        "Referred From Address 1 Line 1",
        "Referred From Address 1 City",
        "Referred From Address 1 State",
        "Referred From Address 1 Zip",
        "Referred From's Details: Latitude",
        "Referred From's Details: Longitude",
    ]

    # Secondary referrer columns
    secondary_cols = [
        "Secondary Referral Source",
        "Secondary Referred From Person Id",
        "Secondary Referred From Full Name",
        "Secondary Referred From Address 1 Line 1",
        "Secondary Referred From Address 1 City",
        "Secondary Referred From Address 1 State",
        "Secondary Referred From Address 1 Zip",
        "Secondary Referred From's Details: Latitude",
        "Secondary Referred From's Details: Longitude",
    ]

    # Process primary referrers
    df_primary = df_in[shared_cols + primary_cols].copy()
    df_primary = df_primary[df_primary["Referred From Person Id"].notna()]

    # Process secondary referrers
    df_secondary = df_in[shared_cols + secondary_cols].copy()
    df_secondary = df_secondary[df_secondary["Secondary Referred From Person Id"].notna()]

    # Standardize secondary referrer column names to match primary
    secondary_col_mapping = {
        "Secondary Referral Source": "Referral Source",
        "Secondary Referred From Person Id": "Referred From Person Id",
        "Secondary Referred From Full Name": "Referred From Full Name",
        "Secondary Referred From Address 1 Line 1": "Referred From Address 1 Line 1",
        "Secondary Referred From Address 1 City": "Referred From Address 1 City",
        "Secondary Referred From Address 1 State": "Referred From Address 1 State",
        "Secondary Referred From Address 1 Zip": "Referred From Address 1 Zip",
        "Secondary Referred From's Details: Latitude": "Referred From's Details: Latitude",
        "Secondary Referred From's Details: Longitude": "Referred From's Details: Longitude",
    }

    df_secondary = df_secondary.rename(columns=secondary_col_mapping)

    # Combine primary and secondary referrers
    df_in_combined = pd.concat([df_primary, df_secondary], axis=0, ignore_index=True)

    # Filter for doctor referrals only and remove missing data
    df_in_combined = df_in_combined.dropna(subset=["Referral Source", "Referred From Person Id"], how="any")
    df_in_combined = df_in_combined[
        df_in_combined["Referral Source"].str.contains("Doctor", case=False, na=False)
    ].reset_index(drop=True)

    # Standardize text columns
    text_cols = [
        "Referred From Full Name",
        "Referred From Address 1 Line 1",
        "Referred From Address 1 City",
    ]
    df_in_combined = standardize_text_columns(df_in_combined, text_cols)
    df_in_combined = standardize_state_column(df_in_combined, "Referred From Address 1 State")

    # Clean numeric columns (latitude/longitude)
    numeric_cols = ["Referred From's Details: Latitude", "Referred From's Details: Longitude"]
    df_in_combined = clean_numeric_columns(df_in_combined, numeric_cols)

    # Define grouping columns for provider aggregation
    provider_cols = [
        "Referred From Person Id",
        "Referred From Full Name",
        "Referred From Address 1 Line 1",
        "Referred From Address 1 City",
        "Referred From Address 1 State",
        "Referred From Address 1 Zip",
        "Referred From's Details: Latitude",
        "Referred From's Details: Longitude",
    ]

    # Create detailed dataset
    detailed_cols = provider_cols + ["Referral Date", "Project ID", "Referral Source"]
    detailed_in = df_in_combined[detailed_cols].copy()
    detailed_in = detailed_in[detailed_in["Referral Date"].notna()]

    # Aggregate by provider
    df_in_grouped = df_in_combined.groupby(provider_cols, as_index=False)["Project ID"].count()
    df_in_agg = df_in_grouped.rename(columns={"Project ID": "Referral Count"})  # type: ignore
    df_in_agg = df_in_agg.sort_values(by="Referral Count", ascending=False)

    # Standardize column names to match outbound format
    inbound_col_mapping = {
        "Referred From Person Id": "Person ID",
        "Referred From Full Name": "Full Name",
        "Referred From Address 1 Line 1": "Street",
        "Referred From Address 1 City": "City",
        "Referred From Address 1 State": "State",
        "Referred From Address 1 Zip": "Zip",
        "Referred From's Details: Latitude": "Latitude",
        "Referred From's Details: Longitude": "Longitude",
    }

    df_in_agg = df_in_agg.rename(columns=inbound_col_mapping)
    detailed_in = detailed_in.rename(columns=inbound_col_mapping)

    # Add phone number column (empty for inbound data)
    df_in_agg["Phone Number"] = np.nan
    detailed_in["Phone Number"] = np.nan

    # Add source identifier
    df_in_agg["Referral Type"] = "Inbound"
    df_in_agg["Description"] = "Cases referred to JLG by this provider"

    detailed_in["Referral Type"] = "Inbound"
    detailed_in["Description"] = "Cases referred to JLG by this provider"

    print(f"Processed {len(df_in_agg)} unique inbound providers from {len(df_in_combined)} referrals")

    return df_in_agg, detailed_in


def create_unified_dataset(
    inbound_agg: pd.DataFrame,
    outbound_agg: pd.DataFrame,
    inbound_detailed: pd.DataFrame,
    outbound_detailed: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Combine inbound and outbound datasets into unified format.

    Returns:
        Tuple of (unified_aggregated, unified_detailed)
    """
    print("Creating unified dataset...")

    # Ensure consistent column order
    common_cols = [
        "Person ID",
        "Full Name",
        "Street",
        "City",
        "State",
        "Zip",
        "Latitude",
        "Longitude",
        "Phone Number",
        "Referral Count",
        "Referral Type",
        "Description",
    ]

    # Reorder columns for aggregated data
    unified_agg = pd.concat([inbound_agg[common_cols], outbound_agg[common_cols]], axis=0, ignore_index=True)

    # Create full address for easier analysis
    unified_agg["Full Address"] = (
        (
            unified_agg["Street"].astype(str)
            + ", "
            + unified_agg["City"].astype(str)
            + ", "
            + unified_agg["State"].astype(str)
            + ", "
            + unified_agg["Zip"].astype(str)
        )
        .str.replace("nan, ", "")
        .str.replace(", nan", "")
    )

    # Ensure Zip is string type
    unified_agg["Zip"] = unified_agg["Zip"].astype(str)

    # Sort by referral count
    unified_agg = unified_agg.sort_values(by="Referral Count", ascending=False).reset_index(drop=True)

    # Combine detailed datasets
    detailed_common_cols = [
        "Person ID",
        "Full Name",
        "Street",
        "City",
        "State",
        "Zip",
        "Latitude",
        "Longitude",
        "Phone Number",
        "Project ID",
        "Referral Date",
        "Referral Type",
        "Description",
    ]

    # Add missing columns for inbound detailed data
    if "Referral Source" in inbound_detailed.columns:
        inbound_detailed = inbound_detailed.drop(columns=["Referral Source"])

    unified_detailed = pd.concat(
        [inbound_detailed[detailed_common_cols], outbound_detailed[detailed_common_cols]], axis=0, ignore_index=True
    )

    # Create full address for detailed data
    unified_detailed["Full Address"] = (
        (
            unified_detailed["Street"].astype(str)
            + ", "
            + unified_detailed["City"].astype(str)
            + ", "
            + unified_detailed["State"].astype(str)
            + ", "
            + unified_detailed["Zip"].astype(str)
        )
        .str.replace("nan, ", "")
        .str.replace(", nan", "")
    )

    # Sort by referral date
    unified_detailed = unified_detailed.sort_values(by="Referral Date", ascending=False).reset_index(drop=True)

    print(f"Unified dataset created:")
    print(f"  - Aggregated: {len(unified_agg)} providers")
    print(f"  - Detailed: {len(unified_detailed)} individual referrals")
    print(f"  - Inbound providers: {len(inbound_agg)}")
    print(f"  - Outbound providers: {len(outbound_agg)}")

    return unified_agg, unified_detailed


def main():
    """Main execution function."""
    repo_root = Path(__file__).resolve().parent.parent

    # Input files
    inbound_file = repo_root / "data" / "raw" / "Referrals_App_Inbound.xlsx"
    outbound_file = repo_root / "data" / "raw" / "Referrals_App_Outbound.xlsx"

    # Output files
    output_agg = repo_root / "data" / "processed" / "unified_referrals.parquet"
    output_detailed = repo_root / "data" / "processed" / "unified_referrals_detailed.parquet"

    # Check input files exist
    if not inbound_file.exists():
        raise FileNotFoundError(f"Inbound file not found: {inbound_file}")
    if not outbound_file.exists():
        raise FileNotFoundError(f"Outbound file not found: {outbound_file}")

    print("=== UNIFIED REFERRAL DATA CLEANING ===")
    print(f"Input files:")
    print(f"  - Inbound: {inbound_file}")
    print(f"  - Outbound: {outbound_file}")
    print()

    # Process datasets
    try:
        # Process inbound referrals
        inbound_agg, inbound_detailed = process_inbound_referrals(inbound_file)

        # Process outbound referrals
        outbound_agg, outbound_detailed = process_outbound_referrals(outbound_file)

        # Create unified dataset
        unified_agg, unified_detailed = create_unified_dataset(
            inbound_agg, outbound_agg, inbound_detailed, outbound_detailed
        )

        # Save outputs
        print(f"\nSaving outputs...")
        unified_agg.to_parquet(output_agg, index=False)
        unified_detailed.to_parquet(output_detailed, index=False)

        print(f"✅ Aggregated data saved to: {output_agg}")
        print(f"✅ Detailed data saved to: {output_detailed}")

        # Display summary
        print(f"\n=== SUMMARY ===")
        print(f"Unified aggregated data shape: {unified_agg.shape}")
        print(f"Unified detailed data shape: {unified_detailed.shape}")

        print(f"\nReferral type breakdown:")
        print(unified_agg["Referral Type"].value_counts())

        print(f"\nTop 5 providers by referral count:")
        print(unified_agg[["Full Name", "City", "State", "Referral Count", "Referral Type"]].head())

    except Exception as e:
        print(f"❌ Error processing data: {e}")
        raise


if __name__ == "__main__":
    main()
