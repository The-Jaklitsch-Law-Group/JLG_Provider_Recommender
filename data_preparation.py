"""
Data Preparation and Cleaning Script for JLG Provider Recommender

This script performs comprehensive data cleaning and converts Excel files to more efficient
Parquet format for faster loading and reduced memory usage.

Usage:
    python data_preparation.py

Output:
    - cleaned_inbound_referrals.parquet
    - cleaned_outbound_referrals.parquet (updated)
    - data_preparation_report.txt
"""

import logging
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data_preparation.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Suppress pandas warnings for cleaner output
warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


class DataPreparer:
    """Comprehensive data preparation and cleaning for referral data."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.report = []
        self.stats = {}

    def log_and_report(self, message: str, level: str = "info"):
        """Log message and add to report."""
        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        self.report.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def analyze_data_quality(self, df: pd.DataFrame, dataset_name: str) -> dict:
        """Analyze data quality metrics."""
        stats = {
            "total_records": len(df),
            "total_columns": len(df.columns),
            "memory_usage_kb": df.memory_usage(deep=True).sum() / 1024,
            "null_counts": df.isnull().sum().to_dict(),
            "duplicate_rows": df.duplicated().sum(),
            "date_columns": [],
            "address_columns": [],
            "numeric_columns": [],
        }

        # Identify column types
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ["date", "created", "sign", "time"]):
                stats["date_columns"].append(col)
            elif any(keyword in col.lower() for keyword in ["address", "street", "city", "state", "zip"]):
                stats["address_columns"].append(col)
            elif df[col].dtype in ["int64", "float64"]:
                stats["numeric_columns"].append(col)

        self.log_and_report(f"Data quality analysis for {dataset_name}:")
        self.log_and_report(f"  - Records: {stats['total_records']:,}")
        self.log_and_report(f"  - Columns: {stats['total_columns']}")
        self.log_and_report(f"  - Memory: {stats['memory_usage_kb']:.1f} KB")
        self.log_and_report(f"  - Duplicates: {stats['duplicate_rows']}")
        self.log_and_report(f"  - Date columns: {stats['date_columns']}")
        self.log_and_report(f"  - Address columns: {stats['address_columns']}")

        return stats

    def clean_excel_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert Excel date formats to proper datetime objects."""
        df = df.copy()
        date_columns = ["Create Date", "Date of Intake", "Sign Up Date"]

        for col in date_columns:
            if col not in df.columns:
                continue

            initial_nulls = df[col].isnull().sum()

            # Handle different Excel date formats
            if df[col].dtype == "float64":
                # Excel serial date format (days since 1900-01-01)
                try:
                    # Convert Excel serial dates to datetime
                    df[col] = pd.to_datetime(df[col], origin="1899-12-30", unit="D", errors="coerce")
                except:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            elif df[col].dtype == "int64":
                # Integer representation of Excel dates
                try:
                    df[col] = pd.to_datetime(df[col], origin="1899-12-30", unit="D", errors="coerce")
                except:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
            else:
                # String or already datetime
                df[col] = pd.to_datetime(df[col], errors="coerce")

            # Filter out invalid dates (before 1990 or future dates)
            min_date = pd.Timestamp("1990-01-01")
            max_date = pd.Timestamp.now() + timedelta(days=365)

            invalid_dates = (df[col] < min_date) | (df[col] > max_date)
            df.loc[invalid_dates, col] = pd.NaT

            final_nulls = df[col].isnull().sum()
            converted_count = len(df) - final_nulls
            invalid_count = invalid_dates.sum()

            self.log_and_report(
                f"  - {col}: converted {converted_count} dates, {invalid_count} invalid, {final_nulls} nulls"
            )

        return df

    def fill_missing_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing Sign Up Date with Create Date values."""
        df = df.copy()

        if "Sign Up Date" in df.columns and "Create Date" in df.columns:
            initial_nulls = df["Sign Up Date"].isnull().sum()
            df["Sign Up Date"] = df["Sign Up Date"].fillna(df["Create Date"])
            filled_count = initial_nulls - df["Sign Up Date"].isnull().sum()

            if filled_count > 0:
                self.log_and_report(f"  - Filled {filled_count} missing 'Sign Up Date' values with 'Create Date'")

        # Create primary referral date
        if "Create Date" in df.columns:
            df["Referral Date"] = df["Create Date"]
        elif "Date of Intake" in df.columns:
            df["Referral Date"] = df["Date of Intake"]
        elif "Sign Up Date" in df.columns:
            df["Referral Date"] = df["Sign Up Date"]

        return df

    def standardize_address_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize address components, create full address."""
        df = df.copy()

        # Identify address columns
        address_mapping = {
            "street": [
                "Street",
                "Address 1 Line 1",
                "Dr/Facility Referred To Address 1 Line 1",
                "Referred From Address 1 Line 1",
                "Secondary Referred From Address 1 Line 1",
            ],
            "city": [
                "City",
                "Address 1 City",
                "Dr/Facility Referred To Address 1 City",
                "Referred From Address 1 City",
                "Secondary Referred From Address 1 City",
            ],
            "state": [
                "State",
                "Address 1 State",
                "Dr/Facility Referred To Address 1 State",
                "Referred From Address 1 State",
                "Secondary Referred From Address 1 State",
            ],
            "zip": [
                "Zip",
                "Address 1 Zip",
                "Dr/Facility Referred To Address 1 Zip",
                "Referred From Address 1 Zip",
                "Secondary Referred From Address 1 Zip",
            ],
        }

        # Standardize column names and clean data
        for standard_name, possible_names in address_mapping.items():
            for col_name in possible_names:
                if col_name in df.columns:
                    # Standardize the column name
                    if col_name != standard_name.title():
                        df[standard_name.title()] = df[col_name]

                    # Clean the address data
                    df[standard_name.title()] = df[standard_name.title()].astype(str)
                    df[standard_name.title()] = df[standard_name.title()].replace(
                        {"nan": "", "None": "", "NaN": "", "null": "", "NULL": "", "<NA>": ""}
                    )
                    df[standard_name.title()] = df[standard_name.title()].fillna("")
                    df[standard_name.title()] = df[standard_name.title()].str.strip()

                    # Remove original if different
                    if col_name != standard_name.title() and col_name in df.columns:
                        df = df.drop(columns=[col_name])
                    break

        # Create Full Address
        address_components = ["Street", "City", "State", "Zip"]
        available_components = [comp for comp in address_components if comp in df.columns]

        if available_components:

            def create_full_address(row):
                parts = []
                for comp in available_components:
                    if comp in row.index and row[comp] and str(row[comp]).strip():
                        parts.append(str(row[comp]).strip())
                return ", ".join(parts) if parts else ""

            df["Full Address"] = df.apply(create_full_address, axis=1)

            # Count successful address creations
            valid_addresses = (df["Full Address"].str.len() > 0).sum()
            self.log_and_report(f"  - Created {valid_addresses} full addresses from components")

        return df

    def standardize_provider_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize provider names and contact information."""
        df = df.copy()

        # Standardize provider name columns
        name_columns = [
            "Full Name",
            "Dr/Facility Referred To Full Name",
            "Referred From Full Name",
            "Secondary Referred From Full Name",
        ]

        for col in name_columns:
            if col in df.columns:
                if col != "Full Name":
                    df["Full Name"] = df[col]
                    df = df.drop(columns=[col])

                # Clean provider names
                df["Full Name"] = df["Full Name"].astype(str)
                df["Full Name"] = df["Full Name"].str.strip()
                df["Full Name"] = df["Full Name"].replace({"nan": "", "None": "", "NaN": ""})
                df["Full Name"] = df["Full Name"].fillna("")
                break

        # Standardize phone numbers
        phone_columns = ["Phone Number", "Phone 1", "Dr/Facility Referred To Phone 1"]
        for col in phone_columns:
            if col in df.columns:
                if col != "Phone Number":
                    df["Phone Number"] = df[col]
                    df = df.drop(columns=[col])

                # Clean phone numbers
                df["Phone Number"] = df["Phone Number"].astype(str)
                df["Phone Number"] = df["Phone Number"].str.strip()
                df["Phone Number"] = df["Phone Number"].replace({"nan": "", "None": "", "NaN": ""})
                break

        # Standardize Person ID
        id_columns = [
            "Person ID",
            "Dr/Facility Referred To Person Id",
            "Referred From Person Id",
            "Secondary Referred From Person Id",
        ]

        for col in id_columns:
            if col in df.columns:
                if col != "Person ID":
                    df["Person ID"] = df[col]
                    df = df.drop(columns=[col])

                # Clean Person IDs
                df["Person ID"] = df["Person ID"].astype(str)
                df["Person ID"] = df["Person ID"].str.strip()
                df["Person ID"] = df["Person ID"].replace({"nan": "", "None": "", "NaN": ""})
                break

        return df

    def clean_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate geographic coordinates."""
        df = df.copy()

        lat_columns = [
            "Latitude",
            "Dr/Facility Referred To's Details: Latitude",
            "Referred From's Details: Latitude",
            "Secondary Referred From's Details: Latitude",
        ]
        lon_columns = [
            "Longitude",
            "Dr/Facility Referred To's Details: Longitude",
            "Referred From's Details: Longitude",
            "Secondary Referred From's Details: Longitude",
        ]

        # Standardize latitude
        for col in lat_columns:
            if col in df.columns:
                if col != "Latitude":
                    df["Latitude"] = df[col]
                    df = df.drop(columns=[col])

                df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
                # Validate latitude range
                df.loc[(df["Latitude"] < -90) | (df["Latitude"] > 90), "Latitude"] = np.nan
                break

        # Standardize longitude
        for col in lon_columns:
            if col in df.columns:
                if col != "Longitude":
                    df["Longitude"] = df[col]
                    df = df.drop(columns=[col])

                df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
                # Validate longitude range
                df.loc[(df["Longitude"] < -180) | (df["Longitude"] > 180), "Longitude"] = np.nan
                break

        # Count valid coordinates
        if "Latitude" in df.columns and "Longitude" in df.columns:
            valid_coords = (df["Latitude"].notna() & df["Longitude"].notna()).sum()
            self.log_and_report(f"  - {valid_coords} records have valid coordinates")

        return df

    def remove_duplicates(self, df: pd.DataFrame, subset_cols: list | None = None) -> pd.DataFrame:
        """Remove duplicate records based on specified columns."""
        df = df.copy()
        initial_count = len(df)

        if subset_cols:
            # Remove duplicates based on specific columns
            available_cols = [col for col in subset_cols if col in df.columns]
            if available_cols:
                df = df.drop_duplicates(subset=available_cols, keep="first")
        else:
            # Remove complete duplicates
            df = df.drop_duplicates(keep="first")

        removed_count = initial_count - len(df)
        if removed_count > 0:
            self.log_and_report(f"  - Removed {removed_count} duplicate records")

        return df

    def process_inbound_referrals(self) -> pd.DataFrame:
        """Process inbound referrals data."""
        self.log_and_report("Processing inbound referrals data...")

        # Load Excel file
        input_file = self.data_dir / "Referrals_App_Inbound.xlsx"
        if not input_file.exists():
            self.log_and_report(f"Input file not found: {input_file}", "error")
            return pd.DataFrame()

        df = pd.read_excel(input_file)
        initial_stats = self.analyze_data_quality(df, "Inbound Referrals (Raw)")

        # Apply cleaning steps
        df = self.clean_excel_dates(df)
        df = self.fill_missing_dates(df)
        df = self.standardize_address_data(df)
        df = self.standardize_provider_data(df)
        df = self.clean_coordinates(df)
        df = self.remove_duplicates(df, subset_cols=["Person ID", "Full Name", "Create Date"])

        # Final quality check
        final_stats = self.analyze_data_quality(df, "Inbound Referrals (Cleaned)")

        self.stats["inbound"] = {
            "initial": initial_stats,
            "final": final_stats,
            "reduction_ratio": (initial_stats["memory_usage_kb"] - final_stats["memory_usage_kb"])
            / initial_stats["memory_usage_kb"],
        }

        return df

    def process_outbound_referrals(self) -> pd.DataFrame:
        """Process outbound referrals data."""
        self.log_and_report("Processing outbound referrals data...")

        # Try Parquet first, then Excel
        parquet_file = self.data_dir / "Referrals_App_Outbound.parquet"
        excel_file = self.data_dir / "Referrals_App_Outbound.xlsx"

        if parquet_file.exists():
            df = pd.read_parquet(parquet_file)
            self.log_and_report("Loaded from existing Parquet file")
        elif excel_file.exists():
            df = pd.read_excel(excel_file)
            self.log_and_report("Loaded from Excel file")
        else:
            self.log_and_report("No outbound referrals file found", "error")
            return pd.DataFrame()

        initial_stats = self.analyze_data_quality(df, "Outbound Referrals (Raw)")

        # Apply cleaning steps
        df = self.clean_excel_dates(df)
        df = self.fill_missing_dates(df)
        df = self.standardize_address_data(df)
        df = self.standardize_provider_data(df)
        df = self.clean_coordinates(df)
        df = self.remove_duplicates(df, subset_cols=["Person ID", "Full Name", "Create Date"])

        # Final quality check
        final_stats = self.analyze_data_quality(df, "Outbound Referrals (Cleaned)")

        self.stats["outbound"] = {
            "initial": initial_stats,
            "final": final_stats,
            "reduction_ratio": (initial_stats["memory_usage_kb"] - final_stats["memory_usage_kb"])
            / initial_stats["memory_usage_kb"],
        }

        return df

    def prepare_for_parquet(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame for Parquet format by ensuring compatible data types."""
        df = df.copy()

        # Convert all object columns to string to avoid type conflicts
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str)
                # Replace pandas nan string representations
                df[col] = df[col].replace({"nan": "", "None": "", "NaN": "", "<NA>": ""})

        # Ensure date columns are properly typed
        date_columns = ["Create Date", "Date of Intake", "Sign Up Date", "Referral Date"]
        for col in date_columns:
            if col in df.columns and df[col].dtype != "datetime64[ns]":
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Ensure numeric columns are properly typed
        numeric_columns = ["Latitude", "Longitude", "Person ID"]
        for col in numeric_columns:
            if col in df.columns:
                if col in ["Latitude", "Longitude"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif col == "Person ID":
                    # Keep Person ID as string to handle mixed ID formats
                    df[col] = df[col].astype(str)

        return df

    def save_cleaned_data(self, inbound_df: pd.DataFrame, outbound_df: pd.DataFrame):
        """Save cleaned data to Parquet format."""
        self.log_and_report("Saving cleaned data...")

        if not inbound_df.empty:
            # Prepare data for Parquet format
            inbound_cleaned = self.prepare_for_parquet(inbound_df)
            output_file = self.data_dir / "cleaned_inbound_referrals.parquet"
            inbound_cleaned.to_parquet(output_file, index=False, compression="snappy")
            file_size = output_file.stat().st_size / 1024
            self.log_and_report(f"Saved inbound data: {output_file} ({file_size:.1f} KB)")

        if not outbound_df.empty:
            # Prepare data for Parquet format
            outbound_cleaned = self.prepare_for_parquet(outbound_df)
            output_file = self.data_dir / "cleaned_outbound_referrals.parquet"
            outbound_cleaned.to_parquet(output_file, index=False, compression="snappy")
            file_size = output_file.stat().st_size / 1024
            self.log_and_report(f"Saved outbound data: {output_file} ({file_size:.1f} KB)")

    def generate_report(self):
        """Generate comprehensive data preparation report."""
        report_content = [
            "=" * 80,
            "JLG PROVIDER RECOMMENDER - DATA PREPARATION REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            "PROCESSING LOG:",
            "=" * 40,
        ]

        report_content.extend(self.report)

        if self.stats:
            report_content.extend(["", "PERFORMANCE SUMMARY:", "=" * 40])

            for dataset, stats in self.stats.items():
                report_content.extend(
                    [
                        f"",
                        f"{dataset.upper()} DATASET:",
                        f"  Records: {stats['initial']['total_records']:,} -> {stats['final']['total_records']:,}",
                        f"  Memory: {stats['initial']['memory_usage_kb']:.1f} KB -> {stats['final']['memory_usage_kb']:.1f} KB",
                        f"  Reduction: {stats['reduction_ratio']*100:.1f}%",
                        f"  Duplicates removed: {stats['initial']['duplicate_rows']}",
                    ]
                )

        # Save report
        report_file = self.data_dir / "data_preparation_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_content))

        self.log_and_report(f"Report saved: {report_file}")

    def run(self):
        """Execute the complete data preparation pipeline."""
        self.log_and_report("Starting data preparation pipeline...")
        start_time = datetime.now()

        try:
            # Process datasets
            inbound_df = self.process_inbound_referrals()
            outbound_df = self.process_outbound_referrals()

            # Save cleaned data
            self.save_cleaned_data(inbound_df, outbound_df)

            # Generate report
            self.generate_report()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self.log_and_report(f"Data preparation completed in {duration:.2f} seconds")

        except Exception as e:
            self.log_and_report(f"Error during data preparation: {e}", "error")
            raise


def main():
    """Main entry point for data preparation."""
    preparer = DataPreparer()
    preparer.run()


if __name__ == "__main__":
    main()
