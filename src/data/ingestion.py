"""
Optimized Data Ingestion Module for JLG Provider Recommender

This module provides a streamlined, high-performance data ingestion system that:
- Prioritizes cleaned Parquet files for optimal performance
- Provides centralized data loading with consistent error handling
- Implements smart caching strategies
- Minimizes redundant processing
- Offers unified data validation and quality checks
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Enumeration of available data sources."""

    INBOUND_REFERRALS = "inbound"
    OUTBOUND_REFERRALS = "outbound"
    PROVIDER_DATA = "provider"


class DataFormat(Enum):
    """Enumeration of supported data formats."""

    PARQUET = ".parquet"
    EXCEL = ".xlsx"
    CSV = ".csv"


class DataIngestionManager:
    """Centralized data ingestion manager with optimized loading strategies."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.cache_ttl = 3600  # 1 hour cache
        self._file_registry = self._build_file_registry()

    def _build_file_registry(self) -> Dict[DataSource, Dict[str, Path]]:
        """Build a registry of available data files with priorities."""
        registry = {
            DataSource.INBOUND_REFERRALS: {
                "cleaned": self.data_dir / "processed" / "cleaned_inbound_referrals.parquet",
                "original_excel": self.data_dir / "raw" / "Referrals_App_Inbound.xlsx",
                "original_parquet": self.data_dir / "processed" / "Referrals_App_Inbound.parquet",
            },
            DataSource.OUTBOUND_REFERRALS: {
                "cleaned": self.data_dir / "processed" / "cleaned_outbound_referrals.parquet",
                "original_excel": self.data_dir / "raw" / "Referrals_App_Outbound.xlsx",
                "original_parquet": self.data_dir / "processed" / "Referrals_App_Outbound.parquet",
            },
            DataSource.PROVIDER_DATA: {
                "cleaned": self.data_dir / "processed" / "cleaned_outbound_referrals.parquet",
                "original_excel": self.data_dir / "raw" / "Referrals_App_Outbound.xlsx",
                "original_parquet": self.data_dir / "processed" / "Referrals_App_Outbound.parquet",
            },
        }
        return registry

    def _get_best_available_file(self, source: DataSource) -> Tuple[Optional[Path], str]:
        """Get the best available file for a data source with performance priority."""
        files = self._file_registry[source]

        # Priority order: cleaned parquet > original parquet > excel
        for file_type, file_path in files.items():
            if file_path.exists():
                return file_path, file_type

        return None, "none"

    @st.cache_data(ttl=3600, show_spinner=False)
    def _load_dataframe(_self, file_path: Path, file_type: str) -> pd.DataFrame:
        """Load DataFrame with optimized format handling."""
        try:
            if file_path.suffix.lower() == DataFormat.PARQUET.value:
                df = pd.read_parquet(file_path)
            elif file_path.suffix.lower() in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == DataFormat.CSV.value:
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

            logger.info(f"Loaded {len(df)} records from {file_path.name}")
            return df

        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return pd.DataFrame()

    def load_data(self, source: DataSource, show_status: bool = True) -> pd.DataFrame:
        """Load data for specified source with automatic format optimization."""
        file_path, file_type = self._get_best_available_file(source)

        if file_path is None:
            if show_status:
                st.error(f"❌ No data files found for {source.value}")
            return pd.DataFrame()

        # Load the data
        df = self._load_dataframe(file_path, file_type)

        if df.empty:
            if show_status:
                st.warning(f"⚠️ No data loaded from {file_path.name}")
            return df

        # Show status based on file type used
        if show_status:
            if file_type == "cleaned":
                st.success(f"🚀 Using optimized {source.value} data ({len(df)} records)")
            elif file_type.startswith("original"):
                st.info(f"📊 Using {file_type.replace('original_', '')} {source.value} data ({len(df)} records)")

        # Apply source-specific post-processing
        df = self._post_process_data(df, source)

        return df

    def _post_process_data(self, df: pd.DataFrame, source: DataSource) -> pd.DataFrame:
        """Apply source-specific post-processing only if not using cleaned data."""
        if df.empty:
            return df

        # Skip post-processing if this is already cleaned data (has standardized columns)
        if self._is_cleaned_data(df):
            return df

        df = df.copy()

        if source == DataSource.OUTBOUND_REFERRALS:
            df = self._process_outbound_referrals(df)
        elif source == DataSource.INBOUND_REFERRALS:
            df = self._process_inbound_referrals(df)
        elif source == DataSource.PROVIDER_DATA:
            df = self._process_provider_data(df)

        return df

    def _is_cleaned_data(self, df: pd.DataFrame) -> bool:
        """Check if data appears to be from cleaned parquet files."""
        # Cleaned data should have standardized columns
        standard_cols = {"Full Name", "Street", "City", "State", "Zip", "Referral Date"}
        return len(standard_cols.intersection(set(df.columns))) >= 4

    def _process_outbound_referrals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw outbound referrals data."""
        if "Dr/Facility Referred To Person Id" in df.columns:
            # Map outbound referral columns to standard format
            column_mapping = {
                "Dr/Facility Referred To Full Name": "Full Name",
                "Dr/Facility Referred To Address 1 Line 1": "Street",
                "Dr/Facility Referred To Address 1 City": "City",
                "Dr/Facility Referred To Address 1 State": "State",
                "Dr/Facility Referred To Address 1 Zip": "Zip",
                "Dr/Facility Referred To's Details: Latitude": "Latitude",
                "Dr/Facility Referred To's Details: Longitude": "Longitude",
                "Dr/Facility Referred To Phone 1": "Phone Number",
            }

            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = df[old_col]

        # Standardize dates
        df = self._standardize_dates(df)
        return df

    def _process_inbound_referrals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw inbound referrals data."""
        # Standardize dates
        df = self._standardize_dates(df)
        return df

    def _process_provider_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process provider data for recommendations by aggregating from outbound referrals."""
        # The provider data source should aggregate outbound referrals to create unique providers

        # If this is already processed provider data, return as-is
        if "Referral Count" in df.columns:
            return df

        # Aggregate outbound referrals to create provider dataset
        provider_columns = {
            "Full Name": "first",
            "Work Address": "first",
            "Work Phone": "first",
            "Latitude": "first",
            "Longitude": "first",
        }

        # Group by provider name and aggregate
        if "Full Name" in df.columns:
            provider_df = df.groupby("Full Name", as_index=False).agg(
                {
                    **{col: method for col, method in provider_columns.items() if col in df.columns},
                    "Project ID": "count",  # Count referrals for each provider
                }
            )

            # Rename the count column to Referral Count
            if "Project ID" in provider_df.columns:
                provider_df = provider_df.rename(columns={"Project ID": "Referral Count"})
            else:
                provider_df["Referral Count"] = 1

            # Clean address columns
            address_cols = ["Work Address", "Work Phone"]
            for col in address_cols:
                if col in provider_df.columns:
                    provider_df[col] = provider_df[col].astype(str).replace(["nan", "None", "NaN"], "").fillna("")

            return provider_df

        return df

    def _standardize_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize date columns across datasets."""
        date_columns = ["Create Date", "Date of Intake", "Sign Up Date"]

        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                # Filter out invalid dates
                df.loc[df[col] < pd.Timestamp("1990-01-01"), col] = pd.NaT

        # Fill missing Sign Up Date with Create Date
        if "Sign Up Date" in df.columns and "Create Date" in df.columns:
            df["Sign Up Date"] = df["Sign Up Date"].fillna(df["Create Date"])

        # Create unified Referral Date
        if "Referral Date" not in df.columns:
            for col in date_columns:
                if col in df.columns:
                    df["Referral Date"] = df[col]
                    break

        return df

    def get_data_status(self) -> Dict[str, Dict[str, Union[bool, str]]]:
        """Get status of all data sources."""
        status = {}

        for source in DataSource:
            file_path, file_type = self._get_best_available_file(source)
            status[source.value] = {
                "available": file_path is not None,
                "file_type": file_type,
                "path": str(file_path) if file_path else None,
                "optimized": file_type == "cleaned",
            }

        return status

    def refresh_file_registry(self):
        """Refresh the file registry to detect new files."""
        self._file_registry = self._build_file_registry()


# Global instance for use throughout the application
data_manager = DataIngestionManager()


# Compatibility functions for existing code
@st.cache_data(ttl=3600, show_spinner=False)
def load_detailed_referrals(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load detailed referral data - optimized version."""
    return data_manager.load_data(DataSource.OUTBOUND_REFERRALS)


@st.cache_data(ttl=3600, show_spinner=False)
def load_inbound_referrals(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load inbound referral data - optimized version."""
    return data_manager.load_data(DataSource.INBOUND_REFERRALS)


@st.cache_data(ttl=3600, show_spinner=False)
def load_provider_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load provider data - optimized version."""
    return data_manager.load_data(DataSource.PROVIDER_DATA)


def get_data_ingestion_status() -> Dict[str, Dict[str, Union[bool, str]]]:
    """Get status of all data ingestion sources."""
    return data_manager.get_data_status()


def refresh_data_cache():
    """Clear data cache to force reload."""
    st.cache_data.clear()
    data_manager.refresh_file_registry()
