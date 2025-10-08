"""
Optimized Data Ingestion Module for JLG Provider Recommender

This module provides a streamlined, high-performance data ingestion system that:
- Prioritizes cleaned Parquet files for optimal performance (10x faster than Excel)
- Provides centralized data loading with consistent error handling
- Implements smart caching strategies with Streamlit's cache system
- Minimizes redundant processing through format prioritization
- Offers unified data validation and quality checks
- Supports the complete data workflow from raw Excel to processed Parquet files

Data Flow:
    Raw Excel → Jupyter Notebook Processing → Cleaned Parquet → Application Usage

Performance Strategy:
    1. Try cleaned Parquet files first (fastest, ~10x faster than Excel)
    2. Fallback to raw Excel files if needed
    3. Cache all operations for 1 hour
    4. Use enum-based data source management for type safety

Key Improvements in v2.0:
    - Added ALL_REFERRALS data source for comprehensive analysis
    - Fixed provider data aggregation to always create unique providers
    - Enhanced error handling and logging throughout
    - Added data integrity validation methods
    - Improved documentation and type hints
    - Better separation of raw vs. processed data handling
    - More robust column mapping for different data sources
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Enumeration of available data sources with clear purpose definitions."""

    # Individual datasets split by referral direction
    INBOUND_REFERRALS = "inbound"  # Referrals TO the law firm
    OUTBOUND_REFERRALS = "outbound"  # Referrals FROM the law firm to providers

    # Combined datasets for comprehensive analysis
    ALL_REFERRALS = "all_referrals"  # Combined inbound + outbound referrals

    # Provider-specific data (aggregated from outbound referrals)
    PROVIDER_DATA = "provider"  # Unique providers with referral counts
    
    # Preferred providers contact list
    PREFERRED_PROVIDERS = "preferred_providers"  # Firm's preferred provider contacts


class DataFormat(Enum):
    """Enumeration of supported data formats with performance characteristics."""

    PARQUET = ".parquet"  # Fastest: Columnar format, ~10x faster than Excel
    EXCEL = ".xlsx"  # Slowest: Legacy format, but most common input
    CSV = ".csv"  # Medium: Text format, good for debugging


class DataIngestionManager:
    """
    Centralized data ingestion manager with optimized loading strategies.

    This manager handles the complete data pipeline from raw Excel files to
    optimized Parquet files, with intelligent format selection and caching.

    Key Features:
    - Automatic format prioritization (Parquet > Excel > CSV)
    - Streamlit cache integration with 1-hour TTL
    - Graceful fallbacks when preferred formats aren't available
    - Source-specific post-processing only when needed
    - Built-in data validation and quality checks

    Usage:
        manager = DataIngestionManager()
        df = manager.load_data(DataSource.OUTBOUND_REFERRALS)
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the data ingestion manager.

        Args:
            data_dir: Base directory containing raw/ and processed/ subdirectories
        """
        self.data_dir = Path(data_dir)
        self.cache_ttl = 3600  # 1 hour cache for optimal performance
        self._file_registry = self._build_file_registry()

    def _build_file_registry(self) -> Dict[DataSource, Dict[str, Path]]:
        """
        Build a registry of available data files with format priorities.

        File Priority Order:
        1. cleaned_*.parquet (fastest, preprocessed)
        2. raw Excel files (slowest, but authoritative source)

        Returns:
            Registry mapping data sources to available file paths
        """
        processed_dir = self.data_dir / "processed"
        raw_dir = self.data_dir / "raw"

        registry = {
            DataSource.INBOUND_REFERRALS: {
                "cleaned": processed_dir / "cleaned_inbound_referrals.parquet",
                # prefer CSV raw exports for S3/raw
                "raw_combined": raw_dir / "Referrals_App_Full_Contacts.csv",
            },
            DataSource.OUTBOUND_REFERRALS: {
                "cleaned": processed_dir / "cleaned_outbound_referrals.parquet",
                "raw_combined": raw_dir / "Referrals_App_Full_Contacts.csv",
            },
            DataSource.ALL_REFERRALS: {
                "cleaned": processed_dir / "cleaned_all_referrals.parquet",
                "raw_combined": raw_dir / "Referrals_App_Full_Contacts.csv",
            },
            DataSource.PROVIDER_DATA: {
                # Provider data is derived from outbound referrals
                "cleaned": processed_dir / "cleaned_outbound_referrals.parquet",
                "raw_combined": raw_dir / "Referrals_App_Full_Contacts.csv",
            },
            DataSource.PREFERRED_PROVIDERS: {
                "cleaned": processed_dir / "cleaned_preferred_providers.parquet",
                "raw": raw_dir / "Referral_App_Preferred_Providers.csv",
            },
        }
        return registry

    def _get_best_available_file(self, source: DataSource) -> Tuple[Optional[Path], str]:
        """
        Get the best available file for a data source with performance priority.

        Strategy:
        1. Try cleaned Parquet files first (10x faster, preprocessed)
        2. Fallback to raw Excel files (slower, but authoritative)

        Args:
            source: The data source to find files for

        Returns:
            Tuple of (file_path, file_type) or (None, "none") if no files found
        """
        files = self._file_registry[source]

        # Priority order: cleaned parquet > raw excel
        for file_type, file_path in files.items():
            if file_path.exists():
                return file_path, file_type

        return None, "none"

    @st.cache_data(ttl=3600, show_spinner=False)
    def _load_dataframe(_self, file_path: Path, file_type: str) -> pd.DataFrame:
        """
        Load DataFrame with optimized format handling and error recovery.

        Args:
            file_path: Path to the data file
            file_type: Type identifier for logging purposes

        Returns:
            Loaded DataFrame or empty DataFrame if loading fails
        """
        try:
            file_suffix = file_path.suffix.lower()

            if file_suffix == DataFormat.PARQUET.value:
                df = pd.read_parquet(file_path)
                logger.info(f"Loaded {len(df)} records from Parquet: {file_path.name}")
            elif file_suffix in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path, engine="openpyxl")
                logger.info(f"Loaded {len(df)} records from Excel: {file_path.name}")
            elif file_suffix == DataFormat.CSV.value:
                df = pd.read_csv(file_path)
                logger.info(f"Loaded {len(df)} records from CSV: {file_path.name}")
            else:
                raise ValueError(f"Unsupported file format: {file_suffix}")

            return df

        except Exception as e:
            logger.error(f"Failed to load {file_path}: {str(e)}")
            return pd.DataFrame()

    def _post_process_data(self, df: pd.DataFrame, source: DataSource, file_type: str) -> pd.DataFrame:
        """
        Apply source-specific post-processing only when needed.

        Processing Strategy:
        - Skip post-processing for cleaned Parquet files (already processed)
        - Exception: PROVIDER_DATA always needs aggregation processing
        - Apply transformations only to raw Excel data that needs standardization
        - Ensure consistent column names and data types across all sources

        Args:
            df: Raw DataFrame to process
            source: Data source type for source-specific processing
            file_type: File type to determine if processing is needed

        Returns:
            Processed DataFrame with standardized schema
        """
        if df.empty:
            return df

        # Provider data always needs aggregation processing, even from cleaned files
        if source == DataSource.PROVIDER_DATA:
            return self._process_provider_data(df)

        # Skip post-processing if this is already cleaned data (except for provider data)
        if file_type == "cleaned" or self._is_cleaned_data(df):
            return df

        df = df.copy()

        # Apply source-specific transformations for raw data
        if source == DataSource.OUTBOUND_REFERRALS:
            df = self._process_outbound_referrals(df)
        elif source == DataSource.INBOUND_REFERRALS:
            df = self._process_inbound_referrals(df)
        elif source == DataSource.ALL_REFERRALS:
            df = self._process_all_referrals(df)

        return df

    def _is_cleaned_data(self, df: pd.DataFrame) -> bool:
        """
        Check if data appears to be from cleaned parquet files.

        Cleaned data characteristics:
        - Has standardized column names (Full Name, Work Address, etc.)
        - Contains referral_type column for type identification
        - Has proper data types and formatting
        """
        # Key indicators of cleaned data
        cleaned_indicators = {"Full Name", "Work Address", "Work Phone", "Latitude", "Longitude", "referral_type"}
        return len(cleaned_indicators.intersection(set(df.columns))) >= 4

    def _process_outbound_referrals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process raw outbound referrals data from Excel source.

        Maps raw Excel columns to standardized schema and handles data cleaning.
        """
        # Standard column mapping for raw Excel data
        if "Referred To Full Name" in df.columns:
            column_mapping = {
                "Referred To Full Name": "Full Name",
                "Referred To's Work Phone": "Work Phone",
                "Referred To's Work Address": "Work Address",
                "Referred To's Details: Latitude": "Latitude",
                "Referred To's Details: Longitude": "Longitude",
            }

            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]

        # Add referral type identifier
        df["referral_type"] = "outbound"

        # Standardize dates
        df = self._standardize_dates(df)
        return df

    def _process_inbound_referrals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process raw inbound referrals data from Excel source.

        Maps referral source information to provider format.
        """
        # Map referral source columns for inbound data
        if "Referred From Full Name" in df.columns:
            column_mapping = {
                "Referred From Full Name": "Full Name",
                "Referred From's Work Phone": "Work Phone",
                "Referred From's Work Address": "Work Address",
                "Referred From's Details: Latitude": "Latitude",
                "Referred From's Details: Longitude": "Longitude",
            }

            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]

        # Add referral type identifier
        df["referral_type"] = "inbound"

        # Standardize dates
        df = self._standardize_dates(df)
        return df

    def _process_all_referrals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process combined referrals data from raw Excel source.

        This processes the full dataset and separates inbound/outbound referrals.
        """
        # For all referrals, we need to process both inbound and outbound in one pass
        processed_rows = []

        for _, row in df.iterrows():
            # Process outbound referral if present
            if pd.notna(row.get("Referred To Full Name")):
                outbound_row = row.copy()
                outbound_row["Full Name"] = row.get("Referred To Full Name")
                outbound_row["Work Phone"] = row.get("Referred To's Work Phone")
                outbound_row["Work Address"] = row.get("Referred To's Work Address")
                outbound_row["Latitude"] = row.get("Referred To's Details: Latitude")
                outbound_row["Longitude"] = row.get("Referred To's Details: Longitude")
                outbound_row["referral_type"] = "outbound"
                processed_rows.append(outbound_row)

            # Process inbound referral if present
            if pd.notna(row.get("Referred From Full Name")):
                inbound_row = row.copy()
                inbound_row["Full Name"] = row.get("Referred From Full Name")
                inbound_row["Work Phone"] = row.get("Referred From's Work Phone")
                inbound_row["Work Address"] = row.get("Referred From's Work Address")
                inbound_row["Latitude"] = row.get("Referred From's Details: Latitude")
                inbound_row["Longitude"] = row.get("Referred From's Details: Longitude")
                inbound_row["referral_type"] = "inbound"
                processed_rows.append(inbound_row)

        if processed_rows:
            df = pd.DataFrame(processed_rows)
            df = self._standardize_dates(df)

        return df

    def _process_provider_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process provider data by aggregating referral information.

        Creates unique provider records with referral counts and latest contact info.
        This always aggregates data to create the provider view, even from cleaned data.
        """
        # If this already has aggregated referral counts, return as-is
        if "Referral Count" in df.columns and len(df["Full Name"].unique()) == len(df):
            return df

        # Make sure we have the required columns for aggregation
        if "Full Name" not in df.columns:
            return df

        # Aggregate to create unique providers with referral counts
        agg_dict = {
            "Project ID": "count",  # Count referrals per provider
        }

        # Add other columns that exist
        for col in ["Work Address", "Work Phone", "Latitude", "Longitude", "Referral Source"]:
            if col in df.columns:
                agg_dict[col] = "first"  # Take first non-null value

        try:
            provider_df = df.groupby("Full Name", as_index=False).agg(agg_dict)

            # Rename count column to Referral Count
            if "Project ID" in provider_df.columns:
                provider_df = provider_df.rename(columns={"Project ID": "Referral Count"})
            else:
                provider_df["Referral Count"] = 1

            # Clean up missing values in text columns
            text_cols = ["Work Address", "Work Phone", "Referral Source"]
            for col in text_cols:
                if col in provider_df.columns:
                    provider_df[col] = provider_df[col].astype(str).replace(["nan", "None", "NaN", ""], "").fillna("")

            # Ensure numeric columns are properly typed
            numeric_cols = ["Latitude", "Longitude", "Referral Count"]
            for col in numeric_cols:
                if col in provider_df.columns:
                    provider_df[col] = pd.to_numeric(provider_df[col], errors="coerce")

            return provider_df

        except Exception as e:
            logger.error(f"Error processing provider data: {e}")
            return df

    def _standardize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize date columns across all datasets.

        Handles multiple date column names and creates a unified 'Referral Date' column.
        Validates dates to ensure they fall within reasonable ranges.
        """
        date_columns = ["Create Date", "Date of Intake", "Sign Up Date"]

        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                # Filter out unrealistic dates (before 1990)
                df.loc[df[col] < pd.Timestamp("1990-01-01"), col] = pd.NaT

        # Create unified Referral Date column
        if "Referral Date" not in df.columns:
            # Use first available date column as Referral Date
            for col in date_columns:
                if col in df.columns:
                    df["Referral Date"] = df[col]
                    break

        return df

    def get_data_status(self) -> Dict[str, Dict[str, Union[bool, str]]]:
        """
        Get comprehensive status of all data sources.

        Returns information about file availability, types, and optimization status
        for all configured data sources.

        Returns:
            Dictionary mapping source names to their status information
        """
        status = {}

        for source in DataSource:
            file_path, file_type = self._get_best_available_file(source)
            status[source.value] = {
                "available": file_path is not None,
                "file_type": file_type,
                "path": str(file_path) if file_path else None,
                "optimized": file_type == "cleaned",
                "performance_tier": "fast" if file_type == "cleaned" else "slow",
            }

        return status

    def load_data(self, source: DataSource, show_status: bool = True) -> pd.DataFrame:
        """
        Public method to load data for a given DataSource.

        This is the compatibility entrypoint expected by the rest of the
        application. It chooses the best available file, loads it (with
        Streamlit caching) and applies any necessary post-processing.

        Args:
            source: DataSource enum value identifying which dataset to load
            show_status: If True, logs or displays the data source selection

        Returns:
            pd.DataFrame with the requested data (may be empty on failure)
        """
        file_path, file_type = self._get_best_available_file(source)

        if show_status:
            logger.debug(f"Loading data for {source.value}: file={file_path}, type={file_type}")

        if not file_path:
            logger.warning(f"No data file found for source: {source}")
            return pd.DataFrame()

        # Use the cached loader to read the dataframe
        df = self._load_dataframe(file_path, file_type)

        # Apply post-processing to standardize columns and produce provider view
        df = self._post_process_data(df, source, file_type)

        # If requesting provider data, ensure aggregation is applied
        if source == DataSource.PROVIDER_DATA:
            # If the cleaned provider file exists and is already aggregated, _process_provider_data will
            # return it unchanged; otherwise, aggregate from the underlying referrals
            df = self._process_provider_data(df)

        return df

    def refresh_file_registry(self):
        """
        Refresh the file registry to detect new files.

        Call this after adding new data files or running the preprocessing notebook.
        """
        self._file_registry = self._build_file_registry()
        logger.info("File registry refreshed - new files will be detected")

    def validate_data_integrity(self, source: DataSource) -> Dict[str, Union[bool, str, int, float, list]]:
        """
        Validate data integrity for a specific source.

        Performs basic data quality checks including:
        - Row count validation
        - Required column presence
        - Data type validation
        - Missing value analysis

        Args:
            source: Data source to validate

        Returns:
            Dictionary with validation results
        """
        df = self.load_data(source, show_status=False)

        if df.empty:
            return {
                "valid": False,
                "error": "No data loaded",
                "row_count": 0,
                "column_count": 0,
            }

        # Define required columns based on data source
        if source == DataSource.PROVIDER_DATA:
            required_cols = ["Full Name", "Referral Count"]
        else:
            required_cols = ["Full Name", "Project ID"]

        missing_cols = [col for col in required_cols if col not in df.columns]

        # Coordinate validation for provider data
        coord_issues = 0
        if "Latitude" in df.columns and "Longitude" in df.columns:
            invalid_coords = (
                pd.notna(df["Latitude"])
                & pd.notna(df["Longitude"])
                & ((df["Latitude"] < -90) | (df["Latitude"] > 90) | (df["Longitude"] < -180) | (df["Longitude"] > 180))
            )
            coord_issues = invalid_coords.sum()

        return {
            "valid": len(missing_cols) == 0,
            "row_count": len(df),
            "column_count": len(df.columns),
            "missing_required_columns": missing_cols,
            "duplicate_names": df["Full Name"].duplicated().sum() if "Full Name" in df.columns else 0,
            "invalid_coordinates": coord_issues,
            "missing_values_pct": round((df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100), 2)
            if not df.empty
            else 0,
        }


# ============================================================================
# Global Instance and Compatibility Functions
# ============================================================================

# Lazy-initialized global instance for use throughout the application
_data_manager: Optional[DataIngestionManager] = None


def get_data_manager() -> DataIngestionManager:
    """
    Return a singleton DataIngestionManager, creating it on first use.

    This laziness avoids import-time side-effects and makes module
    imports safer for long-running processes (like Streamlit) that
    may reload modules during development.
    """
    global _data_manager
    if _data_manager is None:
        _data_manager = DataIngestionManager()
    return _data_manager


# ============================================================================
# Backward Compatibility Functions
#
# These functions maintain compatibility with existing code while providing
# the benefits of the new optimized ingestion system.
# ============================================================================


@st.cache_data(ttl=3600, show_spinner=False)
def load_detailed_referrals(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load detailed referral data (outbound referrals).

    Maintained for backward compatibility. New code should use:
    data_manager.load_data(DataSource.OUTBOUND_REFERRALS)

    Args:
        filepath: Ignored - automatic file selection is used

    Returns:
        DataFrame with outbound referral data
    """
    return get_data_manager().load_data(DataSource.OUTBOUND_REFERRALS, show_status=False)


@st.cache_data(ttl=3600, show_spinner=False)
def load_inbound_referrals(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load inbound referral data.

    Maintained for backward compatibility. New code should use:
    data_manager.load_data(DataSource.INBOUND_REFERRALS)

    Args:
        filepath: Ignored - automatic file selection is used

    Returns:
        DataFrame with inbound referral data
    """
    return get_data_manager().load_data(DataSource.INBOUND_REFERRALS, show_status=False)


@st.cache_data(ttl=3600, show_spinner=False)
def load_provider_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load provider data with referral counts.

    Maintained for backward compatibility. New code should use:
    data_manager.load_data(DataSource.PROVIDER_DATA)

    Args:
        filepath: Ignored - automatic file selection is used

    Returns:
        DataFrame with unique providers and referral counts
    """
    return get_data_manager().load_data(DataSource.PROVIDER_DATA, show_status=False)


@st.cache_data(ttl=3600, show_spinner=False)
def load_all_referrals(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load combined referral data (inbound + outbound).

    New function providing access to the combined dataset.

    Args:
        filepath: Ignored - automatic file selection is used

    Returns:
        DataFrame with all referral data combined
    """
    return get_data_manager().load_data(DataSource.ALL_REFERRALS, show_status=False)


@st.cache_data(ttl=3600, show_spinner=False)
def load_preferred_providers(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load preferred providers contact data.

    Args:
        filepath: Ignored - automatic file selection is used

    Returns:
        DataFrame with preferred provider contact information
    """
    return get_data_manager().load_data(DataSource.PREFERRED_PROVIDERS, show_status=False)


# ============================================================================
# System Management Functions
# ============================================================================


def get_data_ingestion_status() -> Dict[str, Dict[str, Union[bool, str]]]:
    """
    Get comprehensive status of all data ingestion sources.

    Returns:
        Status dictionary with availability and optimization info for each source
    """
    return get_data_manager().get_data_status()


def refresh_data_cache():
    """
    Clear data cache and refresh file registry.

    Call this after:
    - Running the preprocessing notebook
    - Adding new data files
    - Data structure changes
    """
    st.cache_data.clear()
    get_data_manager().refresh_file_registry()
    logger.info("Data cache cleared and file registry refreshed")


def validate_all_data_sources() -> Dict[str, Dict[str, Union[bool, str, int, float, list]]]:
    """
    Validate data integrity for all available sources.

    Returns:
        Validation results for each data source
    """
    results = {}
    for source in DataSource:
        try:
            results[source.value] = get_data_manager().validate_data_integrity(source)
        except Exception as e:
            results[source.value] = {
                "valid": False,
                "error": str(e),
                "row_count": 0,
                "column_count": 0,
            }
    return results
