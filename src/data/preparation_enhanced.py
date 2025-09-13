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
        self, df: pd.DataFrame, column_mapping: Dict[str, str], filter_conditions: Optional[List[Callable]] = None
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

    def load_and_validate_source_data(self, filepath: str) -> pd.DataFrame:
        """Load and validate the source Excel file."""
        logger.info(f"Loading source data from: {filepath}")

        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {filepath}")

        # Load the Excel file
        df_all = pd.read_excel(file_path)
        logger.info(f"Loaded {len(df_all)} records from source file")

        # Convert date columns with consistency
        logger.info("Converting date columns...")
        df_all["Date of Intake"] = pd.to_datetime(df_all["Date of Intake"], unit="D", origin="1899-12-30")
        df_all["Create Date"] = pd.to_datetime(df_all["Create Date"], unit="D", origin="1899-12-30")

        # Fill missing dates
        df_all["Date of Intake"] = df_all["Date of Intake"].fillna(df_all["Create Date"])

        # Validate column existence
        logger.info("Validating data structure...")
        for config_name, config in self.processor.referral_configs.items():
            required_cols = list(config["columns"].keys())
            is_valid = self.validator.validate_column_existence(df_all, config_name, required_cols)
            if not is_valid:
                raise ValueError(f"Validation failed for {config_name}")

        return df_all

    def create_combined_dataset(
        self, referral_results: Dict[str, pd.DataFrame]
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Create combined dataset with referral type indicators."""
        logger.info("Creating combined dataset...")

        # Combine inbound referrals (primary + secondary)
        df_inbound_combined = pd.concat(
            [referral_results["primary_inbound"], referral_results["secondary_inbound"]], ignore_index=False
        )
        df_inbound_combined["referral_type"] = "inbound"

        # Add referral type indicator to outbound
        df_outbound = referral_results["outbound"].copy()
        df_outbound["referral_type"] = "outbound"

        # For outbound, add a referral source column since they don't have one
        df_outbound["Referral Source"] = "Outbound Referral"

        # Combine all referrals into a single dataset
        df_all_referrals = pd.concat([df_inbound_combined, df_outbound], ignore_index=False)

        # Validate the combined dataset
        self.validator.validate_data_quality(df_all_referrals, "Combined All Referrals")

        return df_all_referrals, df_inbound_combined, df_outbound

    def save_datasets(
        self, df_all_referrals: pd.DataFrame, df_inbound_combined: pd.DataFrame, df_outbound: pd.DataFrame
    ) -> Dict[str, str]:
        """Save all processed datasets."""
        logger.info("Saving processed datasets...")

        processed_dir = self.data_dir / "processed"

        # Define file paths
        files = {
            "inbound": processed_dir / "cleaned_inbound_referrals.parquet",
            "outbound": processed_dir / "cleaned_outbound_referrals.parquet",
            "combined": processed_dir / "cleaned_all_referrals.parquet",
        }

        # Save individual datasets for backward compatibility
        df_inbound_combined.to_parquet(files["inbound"], compression="snappy", index=True)
        df_outbound.to_parquet(files["outbound"], compression="snappy", index=True)

        # Save the combined dataset (recommended for future use)
        df_all_referrals.to_parquet(files["combined"], compression="snappy", index=True)

        # Validate output schemas
        self.validator.validate_output_schema(df_inbound_combined, "Inbound Referrals")
        self.validator.validate_output_schema(df_outbound, "Outbound Referrals")
        self.validator.validate_output_schema(df_all_referrals, "Combined Referrals")

        logger.info("✅ All datasets saved successfully!")

        return {key: str(path) for key, path in files.items()}

    def run_integration_tests(self, file_paths: Dict[str, str]) -> Dict[str, Any]:
        """Run integration tests to verify data compatibility."""
        logger.info("Running integration tests...")

        test_results = {"success": True, "tests": {}, "errors": []}

        try:
            # Test loading the cleaned data
            test_inbound = pd.read_parquet(file_paths["inbound"])
            test_outbound = pd.read_parquet(file_paths["outbound"])
            test_combined = pd.read_parquet(file_paths["combined"])

            test_results["tests"]["file_loading"] = {
                "inbound_records": len(test_inbound),
                "outbound_records": len(test_outbound),
                "combined_records": len(test_combined),
                "inbound_columns": list(test_inbound.columns),
                "outbound_columns": list(test_outbound.columns),
                "combined_columns": list(test_combined.columns),
            }

            # Test data quality
            missing_coords = test_combined[["Latitude", "Longitude"]].isna().any(axis=1).sum()
            missing_contact = test_combined[["Full Name", "Work Address"]].isna().any(axis=1).sum()

            test_results["tests"]["data_quality"] = {
                "missing_coordinates": int(missing_coords),
                "missing_contact_info": int(missing_contact),
                "date_index_type": str(type(test_combined.index)),
                "latitude_dtype": str(test_combined["Latitude"].dtype),
                "longitude_dtype": str(test_combined["Longitude"].dtype),
            }

            # Test main app compatibility (optional)
            try:
                from src.data.ingestion import DataIngestionManager, DataSource

                data_manager = DataIngestionManager(data_dir=str(self.data_dir))

                inbound_data = data_manager.load_data(DataSource.INBOUND_REFERRALS, show_status=False)
                outbound_data = data_manager.load_data(DataSource.OUTBOUND_REFERRALS, show_status=False)
                provider_data = data_manager.load_data(DataSource.PROVIDER_DATA, show_status=False)

                test_results["tests"]["main_app_compatibility"] = {
                    "inbound_loaded": len(inbound_data),
                    "outbound_loaded": len(outbound_data),
                    "provider_loaded": len(provider_data),
                    "compatible": True,
                }

            except ImportError:
                test_results["tests"]["main_app_compatibility"] = {
                    "compatible": "skipped",
                    "reason": "Main app modules not available",
                }

            logger.info("✅ Integration tests passed!")

        except Exception as e:
            test_results["success"] = False
            test_results["errors"].append(str(e))
            logger.error(f"❌ Integration tests failed: {e}")

        return test_results

    def get_processing_summary(self, df_all_referrals: pd.DataFrame) -> Dict[str, Any]:
        """Generate processing summary statistics."""
        referral_counts = df_all_referrals["referral_type"].value_counts()
        geocoded = df_all_referrals[["Latitude", "Longitude"]].notna().all(axis=1)

        # Find bidirectional providers
        inbound_providers = set(df_all_referrals[df_all_referrals["referral_type"] == "inbound"]["Full Name"])
        outbound_providers = set(df_all_referrals[df_all_referrals["referral_type"] == "outbound"]["Full Name"])
        bidirectional = inbound_providers & outbound_providers

        return {
            "total_records": len(df_all_referrals),
            "unique_providers": df_all_referrals["Full Name"].nunique(),
            "referral_distribution": referral_counts.to_dict(),
            "geocoding_coverage": {
                "total_geocoded": int(geocoded.sum()),
                "geocoding_percentage": float(geocoded.mean() * 100),
            },
            "bidirectional_providers": {
                "count": len(bidirectional),
                "examples": list(bidirectional)[:5] if bidirectional else [],
            },
            "date_range": {
                "start": df_all_referrals.index.min().strftime("%Y-%m-%d"),
                "end": df_all_referrals.index.max().strftime("%Y-%m-%d"),
            },
            "data_quality": {
                "complete_contact_info": int(
                    df_all_referrals[["Full Name", "Work Address", "Work Phone"]].notna().all(axis=1).sum()
                ),
                "missing_addresses": int(df_all_referrals["Work Address"].isna().sum()),
                "missing_phones": int(df_all_referrals["Work Phone"].isna().sum()),
            },
        }

    def process_referrals(self, source_filepath: str) -> Dict[str, Any]:
        """
        Main entry point for processing referrals.

        Args:
            source_filepath: Path to the source Excel file

        Returns:
            Dictionary containing processing results and summary
        """
        start_time = datetime.now()
        logger.info(f"Starting referral data processing...")

        try:
            # Step 1: Load and validate source data
            df_all = self.load_and_validate_source_data(source_filepath)

            # Step 2: Process all referral types
            referral_results = self.processor.process_all_referrals(df_all)

            # Step 3: Create combined dataset
            df_all_referrals, df_inbound_combined, df_outbound = self.create_combined_dataset(referral_results)

            # Step 4: Save datasets
            file_paths = self.save_datasets(df_all_referrals, df_inbound_combined, df_outbound)

            # Step 5: Run integration tests
            test_results = self.run_integration_tests(file_paths)

            # Step 6: Generate summary
            summary = self.get_processing_summary(df_all_referrals)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "processing_time_seconds": processing_time,
                "source_file": source_filepath,
                "output_files": file_paths,
                "summary": summary,
                "test_results": test_results,
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"✅ Referral processing completed successfully in {processing_time:.2f} seconds")
            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Referral processing failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "processing_time_seconds": processing_time,
                "source_file": source_filepath,
                "timestamp": datetime.now().isoformat(),
            }


# Convenience function for direct usage
def process_referral_data(source_filepath: str, data_dir: str = "data") -> Dict[str, Any]:
    """
    Convenience function to process referral data.

    Args:
        source_filepath: Path to the source Excel file
        data_dir: Directory containing data files

    Returns:
        Dictionary containing processing results
    """
    manager = DataPreparationManager(data_dir=data_dir)
    return manager.process_referrals(source_filepath)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        source_file = sys.argv[1]
        data_directory = sys.argv[2] if len(sys.argv) > 2 else "data"

        result = process_referral_data(source_file, data_directory)

        if result["success"]:
            print("✅ Data processing completed successfully!")
            print(f"📊 Processed {result['summary']['total_records']} total records")
            print(f"📁 Output files saved to: {result['output_files']}")
        else:
            print(f"❌ Data processing failed: {result['error']}")
    else:
        print("Usage: python preparation.py <source_file> [data_directory]")
        print("Example: python preparation.py data/raw/Referrals_App_Full_Contacts.xlsx data")
