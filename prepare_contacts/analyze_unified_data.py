"""
Example usage script for the unified referral dataset.

This script demonstrates how to work with the unified referral data
created by unified_referral_cleaning.py.
"""

from pathlib import Path

import pandas as pd


def load_unified_data(repo_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the unified referral datasets.

    Returns:
        Tuple of (aggregated_data, detailed_data)
    """
    agg_file = repo_root / "data" / "processed" / "unified_referrals.parquet"
    detailed_file = repo_root / "data" / "processed" / "unified_referrals_detailed.parquet"

    if not agg_file.exists():
        raise FileNotFoundError(f"Aggregated file not found: {agg_file}")
    if not detailed_file.exists():
        raise FileNotFoundError(f"Detailed file not found: {detailed_file}")

    agg_data = pd.read_parquet(agg_file)
    detailed_data = pd.read_parquet(detailed_file)

    return agg_data, detailed_data


def analyze_referral_patterns(agg_data: pd.DataFrame, detailed_data: pd.DataFrame):
    """Analyze referral patterns from the unified dataset."""

    print("=== REFERRAL ANALYSIS ===")

    # Overall statistics
    print(f"Total unique providers: {len(agg_data)}")
    print(f"Total referrals: {len(detailed_data)}")
    print()

    # Referral type breakdown
    print("Referral type breakdown:")
    type_counts = agg_data["Referral Type"].value_counts()
    for ref_type, count in type_counts.items():
        print(f"  {ref_type}: {count} providers")
    print()

    # Top referral sources (inbound)
    inbound_providers = agg_data[agg_data["Referral Type"] == "Inbound"]
    if len(inbound_providers) > 0:
        print("Top 5 referral sources (providers referring cases TO JLG):")
        top_inbound = inbound_providers.nlargest(5, "Referral Count")
        for _, row in top_inbound.iterrows():
            print(f"  {row['Full Name']} ({row['City']}, {row['State']}) - {row['Referral Count']} referrals")
        print()

    # Top referral targets (outbound)
    outbound_providers = agg_data[agg_data["Referral Type"] == "Outbound"]
    if len(outbound_providers) > 0:
        print("Top 5 referral targets (providers JLG refers cases TO):")
        top_outbound = outbound_providers.nlargest(5, "Referral Count")
        for _, row in top_outbound.iterrows():
            print(f"  {row['Full Name']} ({row['City']}, {row['State']}) - {row['Referral Count']} referrals")
        print()

    # Geographic distribution
    print("Geographic distribution by state:")
    state_counts = agg_data["State"].value_counts()
    for state, count in state_counts.head(10).items():
        print(f"  {state}: {count} providers")
    print()

    # Time-based analysis
    detailed_data["Referral Date"] = pd.to_datetime(detailed_data["Referral Date"])
    detailed_data["Year"] = detailed_data["Referral Date"].dt.year

    print("Referrals by year:")
    year_counts = detailed_data["Year"].value_counts().sort_index()
    for year, count in year_counts.items():
        print(f"  {year}: {count} referrals")
    print()


def find_bidirectional_relationships(agg_data: pd.DataFrame) -> pd.DataFrame:
    """Find providers that have both inbound and outbound relationships with JLG."""

    # Group by provider details to find providers with both types
    provider_cols = ["Full Name", "Street", "City", "State", "Zip"]

    provider_types = agg_data.groupby(provider_cols)["Referral Type"].apply(list).reset_index()

    # Find providers with both inbound and outbound
    bidirectional = provider_types[provider_types["Referral Type"].apply(lambda x: len(set(x)) > 1)]

    if len(bidirectional) > 0:
        print("Bidirectional relationships (providers with both inbound and outbound referrals):")
        for _, row in bidirectional.iterrows():
            print(f"  {row['Full Name']} ({row['City']}, {row['State']})")
            # Get details for this provider
            provider_data = agg_data[
                (agg_data["Full Name"] == row["Full Name"])
                & (agg_data["City"] == row["City"])
                & (agg_data["State"] == row["State"])
            ]
            for _, detail in provider_data.iterrows():
                print(f"    - {detail['Referral Type']}: {detail['Referral Count']} referrals")
        print()
    else:
        print("No bidirectional relationships found.")
        print()

    return bidirectional


def export_provider_summary(agg_data: pd.DataFrame, output_path: Path):
    """Export a summary of all providers to Excel for easy viewing."""

    # Create a more readable summary
    summary = agg_data.copy()

    # Reorder columns for better readability
    column_order = [
        "Full Name",
        "Street",
        "City",
        "State",
        "Zip",
        "Referral Type",
        "Referral Count",
        "Description",
        "Phone Number",
        "Latitude",
        "Longitude",
        "Full Address",
    ]

    summary = summary[column_order]

    # Sort by referral count
    summary = summary.sort_values(["Referral Count", "Full Name"], ascending=[False, True])

    # Export to Excel
    summary.to_excel(output_path, index=False, sheet_name="Provider Summary")
    print(f"Provider summary exported to: {output_path}")


def main():
    """Main analysis function."""
    repo_root = Path(__file__).resolve().parent.parent

    try:
        # Load data
        print("Loading unified referral data...")
        agg_data, detailed_data = load_unified_data(repo_root)

        # Run analysis
        analyze_referral_patterns(agg_data, detailed_data)

        # Find bidirectional relationships
        find_bidirectional_relationships(agg_data)

        # Export summary
        output_file = repo_root / "data" / "processed" / "provider_summary.xlsx"
        export_provider_summary(agg_data, output_file)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
