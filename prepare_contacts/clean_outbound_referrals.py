"""Clean outbound referral contacts and write a cleaned parquet file.

This script implements the steps from the `contact_cleaning.ipynb` notebook.

Usage:
    python prepare_contacts/clean_outbound_referrals.py

It reads `../data/Referrals_App_Outbound.parquet` and writes
`../data/cleaned_outbound_referrals.parquet`.
"""

from pathlib import Path

import pandas as pd


def main():
    repo_root = Path(__file__).resolve().parent.parent
    src = repo_root / "data" / "Referrals_App_Outbound.parquet"
    dst = repo_root / "data" / "cleaned_outbound_referrals.parquet"

    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}\nPlease ensure the data file exists at this path.")

    df_out = pd.read_parquet(src)

    # Standardize text columns
    str_cols = [
        "Dr/Facility Referred To Full Name",
        "Dr/Facility Referred To Address 1 Line 1",
        "Dr/Facility Referred To Address 1 City",
    ]

    for col in str_cols:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).str.strip().str.title()

    state_col = "Dr/Facility Referred To Address 1 State"
    if state_col in df_out.columns:
        df_out[state_col] = df_out[state_col].astype(str).str.strip().str.upper()

    # Build grouped summary
    full_address = [
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

    # Remove rows where Person Id is missing
    if "Dr/Facility Referred To Person Id" in df_out.columns:
        df_out = df_out[df_out["Dr/Facility Referred To Person Id"].notna()]

    # Ensure date columns are properly formatted
    date_cols = ["Create Date", "Date of Intake", "Sign Up Date"]
    for col in date_cols:
        if col in df_out.columns:
            df_out[col] = pd.to_datetime(df_out[col], errors="coerce")

    # For time-based filtering, we need to preserve individual referral records with dates
    # Create a detailed dataset with referral dates
    detailed_referrals = df_out.copy()

    # Add a referral date column (use Create Date as primary, with fallbacks)
    detailed_referrals["Referral Date"] = (
        detailed_referrals["Create Date"]
        .fillna(detailed_referrals["Date of Intake"])
        .fillna(detailed_referrals["Sign Up Date"])
    )

    # Keep only records with valid referral dates and provider info
    detailed_referrals = detailed_referrals[
        detailed_referrals["Referral Date"].notna() & detailed_referrals["Dr/Facility Referred To Person Id"].notna()
    ]

    # Select columns needed for time-based analysis
    detailed_cols = full_address + ["Referral Date"]
    detailed_referrals = detailed_referrals[detailed_cols].copy()

    df_out_gb = (
        df_out.groupby(full_address, as_index=False, sort=False)["Project ID"]
        .count()
        .rename(columns={"Project ID": "Referral Count"})
        .sort_values(by="Referral Count", ascending=False)
    )

    # Rename columns to friendly names
    new_col_names = {
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

    df_out_gb = df_out_gb.rename(columns=new_col_names)

    # Also save the detailed referrals data for time-based filtering
    detailed_referrals = detailed_referrals.rename(columns=new_col_names)
    detailed_dst = repo_root / "data" / "detailed_referrals.parquet"
    detailed_referrals.to_parquet(detailed_dst, index=False)
    print(f"Detailed referrals saved to: {detailed_dst}")

    # Ensure Zip is string
    if "Zip" in df_out_gb.columns:
        df_out_gb["Zip"] = df_out_gb["Zip"].astype(str)

    # Write parquet
    df_out_gb.to_parquet(dst, index=False)
    print(f"Wrote cleaned outbound referrals to {dst} (rows={len(df_out_gb)})")
    # Print a short preview
    print(df_out_gb.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
