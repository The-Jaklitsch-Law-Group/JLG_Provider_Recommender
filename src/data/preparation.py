"""
Data Preparation Module for JLG Provider Recommender

This module provides comprehensive data cleaning and preparation functionality
extracted from the contact cleaning notebook. It can be triggered by the Streamlit
app to process and clean referral data.

Key Features:
- Configuration-driven data processing
- Comprehensive data quality validation
- Schema validation for main application compatibility
- Support for both individual and combined datasets
- Detailed logging and error handling

Usage:
    from src.data.preparation import DataPreparationManager

    processor = DataPreparationManager()
    result = processor.process_referrals('data/raw/Referrals_App_Full_Contacts.xlsx')
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class DataCleaningFunctions:
    """Collection of data cleaning functions."""

    @staticmethod
    def clean_phone_number(phone_number: str) -> str:
        """
        Clean phone number by removing spaces, parentheses, and dashes.
        Format to (XXX) XXX-XXXX if 10 digits.
        """
        if pd.isna(phone_number):
            return phone_number

        phone_number = phone_number.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

        if len(phone_number) == 10 and phone_number.isdigit():
            return f"({phone_number[:3]}) {phone_number[3:6]}-{phone_number[6:]}"
        else:
            return phone_number

    @staticmethod
    def clean_address(address: str) -> str:
        """Clean address by removing redundant commas and extra spaces."""
        if pd.isna(address):
            return address

        address = address.replace(", ,", ",").replace("  ", " ").strip()
        return address

    @staticmethod
    def clean_geocode(value) -> float:
        """Clean geocode values by handling various input types and validating coordinate ranges."""
        if pd.isna(value):
            return np.nan

        # Convert to string safely
        value_str = str(value).replace("--", "-")

        try:
            result = float(value_str)
            # Validate coordinate ranges (latitude: -90 to 90, longitude: -180 to 180)
            return result if -180 <= result <= 180 else np.nan
        except (ValueError, TypeError):
            return np.nan


class DataValidator:
    """Data validation and quality checking functions."""

    @staticmethod
    def validate_data_quality(df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """Validate data quality and return metrics."""
        quality_metrics = {
            "total_records": len(df),
            "missing_names": df.get("Full Name", pd.Series()).isna().sum(),
            "missing_addresses": df.get("Work Address", pd.Series()).isna().sum(),
            "missing_phones": df.get("Work Phone", pd.Series()).isna().sum(),
            "invalid_geocodes": 0,
        }

        # Check geocode validity
        if "Latitude" in df.columns and "Longitude" in df.columns:
            invalid_lat = (df["Latitude"].notna()) & ((df["Latitude"] < -90) | (df["Latitude"] > 90))
            invalid_lng = (df["Longitude"].notna()) & ((df["Longitude"] < -180) | (df["Longitude"] > 180))
            quality_metrics["invalid_geocodes"] = (invalid_lat | invalid_lng).sum()

        # Log quality metrics
        logger.info(f"{data_type} - Quality Metrics: {quality_metrics}")

        return quality_metrics

    @staticmethod
    def validate_column_existence(df: pd.DataFrame, config_name: str, required_columns: list) -> bool:
        """Validate that all required columns exist in the dataset."""
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"❌ Missing columns for {config_name}: {missing_cols}")
            return False
        logger.info(f"✅ All required columns found for {config_name}")
        return True

    @staticmethod
    def validate_output_schema(df: pd.DataFrame, data_type: str) -> bool:
        """Validate that output matches expected schema for main application."""
        # Expected columns based on the main application's provider loading functions
        expected_base_cols = ["Full Name", "Work Phone", "Work Address", "Latitude", "Longitude"]

        missing_cols = [col for col in expected_base_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"❌ Missing expected columns in {data_type}: {missing_cols}")
            return False

        # Check data types
        if "Latitude" in df.columns:
            non_numeric_lat = df["Latitude"].notna() & ~pd.to_numeric(df["Latitude"], errors="coerce").notna()
            if non_numeric_lat.any():
                logger.warning(f"⚠️ Non-numeric latitude values found in {data_type}: {non_numeric_lat.sum()}")

        if "Longitude" in df.columns:
            non_numeric_lng = df["Longitude"].notna() & ~pd.to_numeric(df["Longitude"], errors="coerce").notna()
            if non_numeric_lng.any():
                logger.warning(f"⚠️ Non-numeric longitude values found in {data_type}: {non_numeric_lng.sum()}")

        logger.info(f"✅ Output schema validation passed for {data_type}")
        return True


class ReferralDataProcessor:
    """Main data processing class."""

    def __init__(self):
        self.cleaner = DataCleaningFunctions()
        self.validator = DataValidator()
        self.referral_configs = self._get_referral_configs()

    def _get_referral_configs(self) -> Dict:
        """Get referral processing configurations."""
        return {
            "primary_inbound": {
                "columns": {
                    "Project ID": "Project ID",
                    "Date of Intake": "Date of Intake",
                    "Referral Source": "Referral Source",
                    "Referred From Full Name": "Full Name",
                    "Referred From's Work Phone": "Work Phone",
                    "Referred From's Work Address": "Work Address",
                    "Referred From's Details: Latitude": "Latitude",
                    "Referred From's Details: Longitude": "Longitude",
                },
                "filters": [
                    lambda df: df["Referral Source"] == "Referral - Doctor's Office",
                    lambda df: df["Full Name"].notna(),
                    lambda df: df["Work Address"].notna(),
                ],
            },
            "secondary_inbound": {
                "columns": {
                    "Project ID": "Project ID",
                    "Date of Intake": "Date of Intake",
                    "Secondary Referral Source": "Referral Source",
                    "Secondary Referred From Full Name": "Full Name",
                    "Secondary Referred From's Work Phone": "Work Phone",
                    "Secondary Referred From's Work Address": "Work Address",
                    "Secondary Referred From's Details: Latitude": "Latitude",
                    "Secondary Referred From's Details: Longitude": "Longitude",
                },
                "filters": [
                    lambda df: df["Referral Source"] == "Referral - Doctor's Office",
                    lambda df: df["Full Name"].notna(),
                    lambda df: df["Work Address"].notna(),
                ],
            },
            "outbound": {
                "columns": {
                    "Project ID": "Project ID",
                    "Date of Intake": "Date of Intake",
                    "Dr/Facility Referred To Full Name": "Full Name",
                    "Dr/Facility Referred To's Work Phone": "Work Phone",
                    "Dr/Facility Referred To's Work Address": "Work Address",
                    "Dr/Facility Referred To's Details: Latitude": "Latitude",
                    "Dr/Facility Referred To's Details: Longitude": "Longitude",
                },
                "filters": [lambda df: df["Full Name"].notna()],
            },
        }

    def clean_referral_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all cleaning functions to a standardized referral dataframe."""
        df = df.copy()

        # Clean columns if they exist
        if "Work Phone" in df.columns:
            df["Work Phone"] = df["Work Phone"].apply(self.cleaner.clean_phone_number)
        if "Work Address" in df.columns:
            df["Work Address"] = df["Work Address"].apply(self.cleaner.clean_address)
        if "Latitude" in df.columns:
            df["Latitude"] = df["Latitude"].apply(self.cleaner.clean_geocode)
        if "Longitude" in df.columns:
            df["Longitude"] = df["Longitude"].apply(self.cleaner.clean_geocode)

        # Sort and set index
        if "Date of Intake" in df.columns and "Full Name" in df.columns:
            df = df.sort_values(by=["Date of Intake", "Full Name"], ascending=True)
            df = df.set_index("Date of Intake")

        return df

    def process_referral_data(
        self, df: pd.DataFrame, column_mapping: Dict[str, str], filter_conditions: List[Callable] = None
    ) -> pd.DataFrame:
        """Generic function to process referral data with column mapping."""
        # Select and rename columns
        processed_df = df[list(column_mapping.keys())].copy()
        processed_df = processed_df.rename(columns=column_mapping)

        # Apply filters if provided
        if filter_conditions:
            for condition in filter_conditions:
                processed_df = processed_df[condition(processed_df)].reset_index(drop=True)

        # Clean the data
        processed_df = self.clean_referral_dataframe(processed_df)

        return processed_df

    def process_all_referrals(self, df_all: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Process all referral types using configuration."""
        results = {}
        for referral_type, config in self.referral_configs.items():
            logger.info(f"Processing {referral_type} referrals...")
            results[referral_type] = self.process_referral_data(df_all, config["columns"], config.get("filters"))
            # Validate data quality
            self.validator.validate_data_quality(results[referral_type], referral_type)
        return results


class DataPreparationManager:
    """Main data preparation manager class."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.processor = ReferralDataProcessor()
        self.validator = DataValidator()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        processed_dir = self.data_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "info"):
        """Unified logging."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"

        if level == "info":
            logger.info(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)

        self.processing_log.append(formatted_message)

    def prepare_inbound_data(self) -> Optional[pd.DataFrame]:
        """Prepare inbound referrals with optimized processing."""
        start_time = datetime.now()
        input_file = self.data_dir / "raw" / "Referrals_App_Inbound.xlsx"

        if not input_file.exists():
            self.log(f"Input file not found: {input_file}", "error")
            return None

        self.log("Processing inbound referrals...")

        try:
            # Load with optimized settings
            df = pd.read_excel(input_file, dtype={"Zip": str})
            initial_size = len(df)
            initial_memory = df.memory_usage(deep=True).sum() / 1024

            # Efficient date processing
            date_cols = ["Create Date", "Date of Intake", "Sign Up Date"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Fill missing Sign Up Date efficiently
            if "Sign Up Date" in df.columns and "Create Date" in df.columns:
                filled_count = df["Sign Up Date"].isnull().sum()
                df["Sign Up Date"] = df["Sign Up Date"].fillna(df["Create Date"])
                self.log(f"Filled {filled_count} missing Sign Up Date values")

            # Create referral date
            df["Referral Date"] = df.get("Create Date", df.get("Date of Intake", df.get("Sign Up Date")))

            # Optimize address data
            df = self._optimize_address_data(df, "inbound")

            # Optimize data types
            df = self._optimize_data_types(df)

            # Performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            final_memory = df.memory_usage(deep=True).sum() / 1024

            self.performance_metrics["inbound"] = {
                "records": initial_size,
                "processing_time": processing_time,
                "memory_before": initial_memory,
                "memory_after": final_memory,
                "memory_reduction": (initial_memory - final_memory) / initial_memory * 100,
            }

            self.log(f"Inbound processing completed: {initial_size} records in {processing_time:.2f}s")
            return df

        except Exception as e:
            self.log(f"Error processing inbound data: {e}", "error")
            return None

    def prepare_outbound_data(self) -> Optional[pd.DataFrame]:
        """Prepare outbound referrals with optimized processing."""
        start_time = datetime.now()

        # Try parquet first, then Excel
        input_files = [
            self.data_dir / "processed" / "Referrals_App_Outbound.parquet",
            self.data_dir / "raw" / "Referrals_App_Outbound.xlsx",
        ]

        input_file = None
        for file_path in input_files:
            if file_path.exists():
                input_file = file_path
                break

        if not input_file:
            self.log("No outbound referrals file found", "error")
            return None

        self.log(f"Processing outbound referrals from {input_file.name}...")

        try:
            # Load with format-specific optimizations
            if input_file.suffix == ".parquet":
                df = pd.read_parquet(input_file)
            else:
                df = pd.read_excel(input_file, dtype={"Dr/Facility Referred To Address 1 Zip": str})

            initial_size = len(df)
            initial_memory = df.memory_usage(deep=True).sum() / 1024

            # Standardize column names efficiently
            column_mapping = {
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

            # Rename existing columns in batch
            existing_renames = {old: new for old, new in column_mapping.items() if old in df.columns}
            if existing_renames:
                df = df.rename(columns=existing_renames)

            # Efficient date processing
            date_cols = ["Create Date", "Date of Intake", "Sign Up Date"]
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")

            # Fill missing Sign Up Date efficiently
            if "Sign Up Date" in df.columns and "Create Date" in df.columns:
                filled_count = df["Sign Up Date"].isnull().sum()
                df["Sign Up Date"] = df["Sign Up Date"].fillna(df["Create Date"])
                self.log(f"Filled {filled_count} missing Sign Up Date values")

            # Create referral date
            df["Referral Date"] = df.get("Create Date", df.get("Date of Intake", df.get("Sign Up Date")))

            # Optimize address and coordinate data
            df = self._optimize_address_data(df, "outbound")
            df = self._optimize_coordinates(df)

            # Optimize data types
            df = self._optimize_data_types(df)

            # Performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            final_memory = df.memory_usage(deep=True).sum() / 1024

            self.performance_metrics["outbound"] = {
                "records": initial_size,
                "processing_time": processing_time,
                "memory_before": initial_memory,
                "memory_after": final_memory,
                "memory_reduction": (initial_memory - final_memory) / initial_memory * 100,
            }

            self.log(f"Outbound processing completed: {initial_size} records in {processing_time:.2f}s")
            return df

        except Exception as e:
            self.log(f"Error processing outbound data: {e}", "error")
            return None

    def _optimize_address_data(self, df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
        """Optimize address data with minimal memory overhead."""
        address_cols = ["Street", "City", "State", "Zip"]

        # Efficiently clean address columns
        for col in address_cols:
            if col in df.columns:
                # Use categorical for repeated values
                if df[col].nunique() / len(df) < 0.5:  # If less than 50% unique values
                    df[col] = df[col].astype(str).astype("category")
                else:
                    df[col] = df[col].astype(str)

                # Clean null representations efficiently
                df[col] = df[col].cat.add_categories("") if df[col].dtype.name == "category" else df[col]
                df[col] = df[col].replace(["nan", "None", "NaN", "null", "NULL", "<NA>"], "")
                df[col] = df[col].fillna("")

        # Create Full Address efficiently
        if all(col in df.columns for col in address_cols):
            # Vectorized address creation
            address_parts = []
            for col in address_cols:
                if col in df.columns:
                    address_parts.append(df[col].astype(str))

            if address_parts:
                df["Full Address"] = address_parts[0]
                for part in address_parts[1:]:
                    mask = part != ""
                    df.loc[mask, "Full Address"] += ", " + part[mask]

                # Clean up extra commas efficiently
                df["Full Address"] = df["Full Address"].str.replace(r",\s*,", ",", regex=True)
                df["Full Address"] = df["Full Address"].str.replace(r",\s*$", "", regex=True)
                df["Full Address"] = df["Full Address"].str.replace(r"^,\s*", "", regex=True)

        valid_addresses = (df.get("Full Address", pd.Series()).str.len() > 0).sum()
        self.log(f"Created {valid_addresses} full addresses for {dataset_type}")

        return df

    def _optimize_coordinates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize coordinate data with robust error handling."""
        # Find all coordinate columns (including variations)
        coord_patterns = {"latitude": ["latitude", "lat"], "longitude": ["longitude", "lng", "lon"]}

        # Map all coordinate columns to standard names
        for coord_type, patterns in coord_patterns.items():
            for col in df.columns:
                if any(pattern in col.lower() for pattern in patterns):
                    # Convert to numeric, handling invalid values
                    try:
                        # Handle string coordinates that might have invalid formats
                        if df[col].dtype == "object" or df[col].dtype.name == "category":
                            # Clean coordinate strings
                            cleaned_coords = df[col].astype(str).str.replace(r"[^-0-9.]", "", regex=True)
                            # Replace empty strings with NaN
                            cleaned_coords = cleaned_coords.replace("", np.nan)
                            df[col] = pd.to_numeric(cleaned_coords, errors="coerce")
                        else:
                            df[col] = pd.to_numeric(df[col], errors="coerce")

                        # Validate coordinate ranges
                        if coord_type == "latitude":
                            df.loc[(df[col] < -90) | (df[col] > 90), col] = np.nan
                        else:  # longitude
                            df.loc[(df[col] < -180) | (df[col] > 180), col] = np.nan

                        # Convert to float32 for efficiency
                        df[col] = df[col].astype("float32")

                    except Exception as e:
                        self.log(f"Warning: Could not process coordinate column {col}: {e}", "warning")
                        df[col] = np.nan

        # Count valid coordinate pairs
        lat_cols = [col for col in df.columns if "latitude" in col.lower() or "lat" in col.lower()]
        lon_cols = [
            col for col in df.columns if "longitude" in col.lower() or "lng" in col.lower() or "lon" in col.lower()
        ]

        if lat_cols and lon_cols:
            # Use the first latitude and longitude columns for validation count
            lat_col, lon_col = lat_cols[0], lon_cols[0]
            valid_coords = (df[lat_col].notna() & df[lon_col].notna()).sum()
            self.log(f"Validated {valid_coords} coordinate pairs")

        return df

    def _optimize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types for Parquet compatibility and memory efficiency."""
        # Handle categorical columns first - convert back to string for Parquet compatibility
        for col in df.columns:
            if df[col].dtype.name == "category":
                df[col] = df[col].astype(str)

        # Convert object columns to appropriate types
        for col in df.columns:
            if df[col].dtype == "object":
                # Check if it should be categorical (for memory efficiency)
                unique_ratio = df[col].nunique() / len(df) if len(df) > 0 else 1
                if unique_ratio < 0.1 and df[col].nunique() > 1:
                    # High repetition - keep as string for Parquet compatibility
                    df[col] = df[col].astype(str)
                else:
                    df[col] = df[col].astype(str)

        # Optimize numeric columns
        for col in df.select_dtypes(include=[np.number]).columns:
            if "latitude" in col.lower() or "longitude" in col.lower():
                # Coordinates already handled in _optimize_coordinates
                continue
            elif df[col].dtype == "int64":
                # Check if we can use smaller int type
                col_min, col_max = df[col].min(), df[col].max()
                if pd.isna(col_min) or pd.isna(col_max):
                    continue

                if col_min >= 0 and col_max <= 65535:
                    df[col] = df[col].astype("uint16")
                elif col_min >= -32768 and col_max <= 32767:
                    df[col] = df[col].astype("int16")
                else:
                    df[col] = df[col].astype("int32")
            elif df[col].dtype == "float64":
                # Convert to float32 for memory efficiency
                df[col] = df[col].astype("float32")

        return df

    def save_optimized_data(self, inbound_df: Optional[pd.DataFrame], outbound_df: Optional[pd.DataFrame]):
        """Save data with optimal compression and validation."""
        self.log("Saving optimized data...")

        compression_settings = {"compression": "snappy", "index": False, "engine": "pyarrow"}

        if inbound_df is not None and not inbound_df.empty:
            output_file = self.data_dir / "processed" / "cleaned_inbound_referrals.parquet"
            inbound_df.to_parquet(output_file, **compression_settings)
            file_size = output_file.stat().st_size / 1024
            self.log(f"Saved inbound data: {len(inbound_df)} records, {file_size:.1f} KB")

        if outbound_df is not None and not outbound_df.empty:
            output_file = self.data_dir / "processed" / "cleaned_outbound_referrals.parquet"
            outbound_df.to_parquet(output_file, **compression_settings)
            file_size = output_file.stat().st_size / 1024
            self.log(f"Saved outbound data: {len(outbound_df)} records, {file_size:.1f} KB")

    def generate_performance_report(self):
        """Generate concise performance report."""
        report_lines = [
            "=" * 60,
            "JLG PROVIDER RECOMMENDER - OPTIMIZED DATA PREPARATION",
            f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
        ]

        # Add processing log
        report_lines.extend(self.processing_log)

        # Add performance summary
        if self.performance_metrics:
            report_lines.extend(["", "PERFORMANCE SUMMARY:", "-" * 30])

            for dataset, metrics in self.performance_metrics.items():
                report_lines.extend(
                    [
                        f"",
                        f"{dataset.upper()}:",
                        f"  Records: {metrics['records']:,}",
                        f"  Processing Time: {metrics['processing_time']:.2f}s",
                        f"  Memory Reduction: {metrics['memory_reduction']:.1f}%",
                    ]
                )

        # Save report
        report_file = self.data_dir / "data_preparation_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        self.log(f"Performance report saved: {report_file}")

    def run(self):
        """Execute optimized data preparation pipeline."""
        self.log("Starting optimized data preparation...")
        start_time = datetime.now()

        try:
            # Process both datasets
            inbound_df = self.prepare_inbound_data()
            outbound_df = self.prepare_outbound_data()

            # Save optimized data
            self.save_optimized_data(inbound_df, outbound_df)

            # Generate performance report
            self.generate_performance_report()

            total_time = (datetime.now() - start_time).total_seconds()
            self.log(f"Optimization completed in {total_time:.2f} seconds")

        except Exception as e:
            self.log(f"Critical error in data preparation: {e}", "error")
            raise


def main():
    """Main entry point for optimized data preparation."""
    processor = StreamlinedDataPreparation()
    processor.run()


if __name__ == "__main__":
    main()
