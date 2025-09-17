import io
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
from docx import Document
from geopy.distance import geodesic
from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

from .consolidated_functions import safe_numeric_conversion

# Import validation functions from centralized module
from .validation import validate_address_input


# --- Data Loading ---
@st.cache_data(ttl=3600)
# Data loading functions have been moved to src.data.ingestion for better performance
# and centralized management. These functions are now handled by DataIngestionManager.


def calculate_time_based_referral_counts(detailed_df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """Calculate referral counts for providers within a specific time period."""

    if detailed_df.empty:
        return pd.DataFrame()

    # Ensure we have a copy to work with
    df_copy = detailed_df.copy()

    # Check if date is in index or in a column
    if df_copy.index.name == "Date of Intake":
        # Date is in the index, reset it to a column
        df_copy = df_copy.reset_index()
        date_col = "Date of Intake"
    elif "Referral Date" in df_copy.columns:
        date_col = "Referral Date"
    elif "Date of Intake" in df_copy.columns:
        date_col = "Date of Intake"
    else:
        # No date column found, return the original dataframe without filtering
        date_col = None

    # Filter by date range
    if start_date and end_date and date_col:
        mask = (df_copy[date_col] >= pd.to_datetime(start_date)) & (df_copy[date_col] <= pd.to_datetime(end_date))
        filtered_df = df_copy[mask]
    else:
        filtered_df = df_copy

    if filtered_df.empty:
        return pd.DataFrame()

    # Group by provider and count referrals
    # Use the actual column names from our processed data
    provider_cols = [
        "Full Name",
        "Work Address",
        "Work Phone",
        "Latitude",
        "Longitude",
    ]

    # Only include columns that exist in the DataFrame
    available_cols = [col for col in provider_cols if col in filtered_df.columns]

    if not available_cols or "Full Name" not in available_cols:
        return pd.DataFrame()

    time_based_counts = (
        filtered_df.groupby(available_cols, as_index=False)
        .size()
        .rename(columns={"size": "Referral Count"})
        .sort_values(by="Referral Count", ascending=False)
    )

    return time_based_counts


def calculate_inbound_referral_counts(inbound_df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
    """Calculate inbound referral counts for each provider.

    Args:
        inbound_df (pd.DataFrame): Raw inbound referrals data
        start_date: Start date for filtering (optional)
        end_date: End date for filtering (optional)

    Returns:
        pd.DataFrame: Provider data with inbound referral counts
    """
    if inbound_df.empty:
        return pd.DataFrame()

    # Ensure we have a copy to work with
    df_copy = inbound_df.copy()

    # Check if date is in index or in a column
    if df_copy.index.name == "Date of Intake":
        # Date is in the index, reset it to a column
        df_copy = df_copy.reset_index()
        date_col = "Date of Intake"
    elif "Referral Date" in df_copy.columns:
        date_col = "Referral Date"
    elif "Date of Intake" in df_copy.columns:
        date_col = "Date of Intake"
    else:
        date_col = None

    # Filter by date range if provided
    if start_date and end_date and date_col:
        mask = (df_copy[date_col] >= pd.to_datetime(start_date)) & (df_copy[date_col] <= pd.to_datetime(end_date))
        filtered_df = df_copy[mask]
    else:
        filtered_df = df_copy

    if filtered_df.empty:
        return pd.DataFrame()

    # Check if this is raw data with original column names or processed data
    has_raw_columns = "Referred From Full Name" in filtered_df.columns

    if not has_raw_columns:
        # This is already processed data - just aggregate by provider
        provider_cols = ["Full Name"]

        # Add other available columns
        additional_cols = ["Street", "City", "State", "Zip", "Latitude", "Longitude", "Work Address", "Work Phone"]
        for col in additional_cols:
            if col in filtered_df.columns:
                provider_cols.append(col)

        available_cols = [col for col in provider_cols if col in filtered_df.columns]

        if not available_cols:
            return pd.DataFrame()

        inbound_counts = (
            filtered_df.groupby(available_cols, as_index=False)
            .size()
            .rename(columns={"size": "Inbound Referral Count"})
            .sort_values(by="Inbound Referral Count", ascending=False)
        )

        # Add Full Address if not present and components are available
        if "Full Address" not in inbound_counts.columns:
            if "Work Address" in inbound_counts.columns:
                inbound_counts["Full Address"] = inbound_counts["Work Address"]

        return inbound_counts

    # Process primary referral source
    primary_cols = {
        "Referred From Full Name": "Full Name",
        "Referred From Address 1 Line 1": "Street",
        "Referred From Address 1 City": "City",
        "Referred From Address 1 State": "State",
        "Referred From Address 1 Zip": "Zip",
        "Referred From's Details: Latitude": "Latitude",
        "Referred From's Details: Longitude": "Longitude",
    }

    # Create primary referrals dataframe
    primary_df = filtered_df.copy()
    for old_col, new_col in primary_cols.items():
        if old_col in primary_df.columns:
            primary_df[new_col] = primary_df[old_col]

    # Process secondary referral source if available
    secondary_cols = {
        "Secondary Referred From Full Name": "Full Name",
        "Secondary Referred From Address 1 Line 1": "Street",
        "Secondary Referred From Address 1 City": "City",
        "Secondary Referred From Address 1 State": "State",
        "Secondary Referred From Address 1 Zip": "Zip",
        "Secondary Referred From's Details: Latitude": "Latitude",
        "Secondary Referred From's Details: Longitude": "Longitude",
    }

    secondary_df = filtered_df.copy()
    for old_col, new_col in secondary_cols.items():
        if old_col in secondary_df.columns:
            secondary_df[new_col] = secondary_df[old_col]

    # Remove rows where secondary referral data is missing
    if "Secondary Referred From Full Name" in secondary_df.columns:
        secondary_df = secondary_df.dropna(subset=["Secondary Referred From Full Name"])
    else:
        secondary_df = pd.DataFrame()  # No secondary data available

    # Combine primary and secondary referrals
    provider_cols = ["Full Name", "Street", "City", "State", "Zip", "Latitude", "Longitude"]
    available_cols = [col for col in provider_cols if col in primary_df.columns]

    if not available_cols:
        return pd.DataFrame()

    # Count inbound referrals for each provider
    all_referrals = []

    # Add primary referrals
    primary_subset = primary_df[available_cols].dropna(subset=["Full Name"])
    if not primary_subset.empty:
        all_referrals.append(primary_subset)

    # Add secondary referrals if they exist
    if not secondary_df.empty:
        secondary_subset = secondary_df[available_cols].dropna(subset=["Full Name"])
        if not secondary_subset.empty:
            all_referrals.append(secondary_subset)

    if not all_referrals:
        return pd.DataFrame()

    # Combine all referrals
    combined_df = pd.concat(all_referrals, ignore_index=True)

    # Group by provider and count inbound referrals
    inbound_counts = (
        combined_df.groupby(available_cols, as_index=False)
        .size()
        .rename(columns={"size": "Inbound Referral Count"})
        .sort_values(by="Inbound Referral Count", ascending=False)
    )

    # Add Full Address if components are available
    if all(col in inbound_counts.columns for col in ["Street", "City", "State", "Zip"]):
        # Ensure all address columns are strings to prevent concatenation errors
        for col in ["Street", "City", "State", "Zip"]:
            inbound_counts[col] = inbound_counts[col].astype(str).replace(["nan", "None", "NaN"], "").fillna("")

        inbound_counts["Full Address"] = (
            inbound_counts["Street"].fillna("")
            + ", "
            + inbound_counts["City"].fillna("")
            + ", "
            + inbound_counts["State"].fillna("")
            + " "
            + inbound_counts["Zip"].fillna("")
        )
        inbound_counts["Full Address"] = (
            inbound_counts["Full Address"].str.replace(r",\s*,", ",", regex=True).str.replace(r",\s*$", "", regex=True)
        )

    return inbound_counts


def load_and_validate_provider_data(
    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Load provider data with optional time filtering and validation.
    Uses the optimized DataIngestionManager for consistent data loading.

    Args:
        start_date: Start date for filtering referrals
        end_date: End date for filtering referrals

    Returns:
        Validated provider dataframe
    """
    try:
        from ..data.ingestion import DataIngestionManager, DataSource

        manager = DataIngestionManager()

        # Load provider data using the optimized manager
        df = manager.load_data(DataSource.PROVIDER_DATA)

        # Note: Time filtering should be handled at the data preparation level
        # in the Jupyter notebook for better performance
        if start_date or end_date:
            st.warning(
                "Time filtering is not supported in this function. Please apply filters during data preparation."
            )

        # Validate data
        is_valid, issues = validate_provider_data(df)
        if not is_valid and isinstance(issues, list):
            st.warning(f"Data quality issues detected: {'; '.join(issues)}")

        # Clean and standardize coordinates
        if "Latitude" in df.columns:
            df["Latitude"] = df["Latitude"].apply(lambda x: safe_numeric_conversion(x, 0.0))
        if "Longitude" in df.columns:
            df["Longitude"] = df["Longitude"].apply(lambda x: safe_numeric_conversion(x, 0.0))

        # Remove providers with invalid coordinates
        if "Latitude" in df.columns and "Longitude" in df.columns:
            df = df[(df["Latitude"] != 0) & (df["Longitude"] != 0)]

        return df

    except Exception as e:
        st.error(f"Error loading provider data: {str(e)}")
        return pd.DataFrame()


def handle_streamlit_error(error: Exception, context: str = "operation"):
    """
    Handle errors gracefully in Streamlit with user-friendly messages.

    Args:
        error: The exception that occurred
        context: Context description for the error
    """
    error_type = type(error).__name__
    error_message = str(error)

    if "geocod" in error_message.lower():
        st.error(
            f"❌ **Geocoding Error**: Unable to find coordinates for the provided address. Please check the address format and try again."
        )
    elif "network" in error_message.lower() or "connection" in error_message.lower():
        st.error(f"❌ **Network Error**: Unable to connect to geocoding service. Please check your internet connection.")
    elif "timeout" in error_message.lower():
        st.error(f"❌ **Timeout Error**: The geocoding service is taking too long to respond. Please try again.")
    elif "file" in error_message.lower() or "not found" in error_message.lower():
        st.error(f"❌ **Data Error**: Required data files are missing. Please contact support.")
    else:
        st.error(f"❌ **Error during {context}**: {error_message}")

    # Log the full error details
    st.exception(error)


@st.cache_data(ttl=3600)
def validate_provider_data(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate provider data quality and return status with message."""

    if df.empty:
        return False, "❌ **Error**: No provider data available. Please check data files."

    issues = []
    info = []

    # Check essential columns (Referral Count is optional and can be calculated)
    required_cols = ["Full Name"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {', '.join(missing_cols)}")

    # Check for geographic data
    if "Latitude" in df.columns and "Longitude" in df.columns:
        missing_coords = (df["Latitude"].isna() | df["Longitude"].isna()).sum()
        if missing_coords > 0:
            issues.append(f"{missing_coords} providers missing geographic coordinates")
    else:
        missing_geo_cols = []
        if "Latitude" not in df.columns:
            missing_geo_cols.append("Latitude")
        if "Longitude" not in df.columns:
            missing_geo_cols.append("Longitude")
        if missing_geo_cols:
            info.append(f"Geographic columns missing: {', '.join(missing_geo_cols)} (may need geocoding)")

    # Check referral count data
    if "Referral Count" in df.columns:
        invalid_counts = df["Referral Count"].isna().sum()
        if invalid_counts > 0:
            issues.append(f"{invalid_counts} providers have invalid referral counts")

        zero_referrals = (df["Referral Count"] == 0).sum()
        if zero_referrals > 0:
            info.append(f"{zero_referrals} providers have zero referrals")

        avg_referrals = df["Referral Count"].mean()
        max_referrals = df["Referral Count"].max()
        info.append(f"Average referrals per provider: {avg_referrals:.1f}")
        info.append(f"Most referred provider has: {max_referrals} referrals")
    else:
        info.append("Referral Count column not found - will be calculated from detailed referral data")

    # Summary info
    total_providers = len(df)
    info.append(f"Total providers in database: {total_providers}")

    # Compile message
    message_parts = []
    if issues:
        message_parts.append("⚠️ **Data Quality Issues**: " + "; ".join(issues))
    if info:
        message_parts.append("ℹ️ **Data Summary**: " + "; ".join(info))

    is_valid = len(issues) == 0
    message = "\n\n".join(message_parts)

    return is_valid, message


_geocode_cache = {}


def geocode_address(addresses, _geocode):
    """Geocode a list of addresses, returning lists of latitudes and longitudes."""

    def _cached_geocode(addr):
        if addr not in _geocode_cache:
            try:
                location = _geocode(addr, timeout=10)
                if location:
                    _geocode_cache[addr] = (location.latitude, location.longitude)
                else:
                    _geocode_cache[addr] = (None, None)
            except GeocoderUnavailable as e:
                _geocode_cache[addr] = (None, None)
                print(f"GeocoderUnavailable for address '{addr}': {e}")
            except Exception as e:
                _geocode_cache[addr] = (None, None)
                print(f"Geocoding error for address '{addr}': {e}")
        return _geocode_cache[addr]

    results = pd.Series(addresses).map(_cached_geocode)
    lats, lons = zip(*results)
    return list(lats), list(lons)


@st.cache_data(ttl=60 * 60 * 24)
def cached_geocode_address(q: str):
    """Cached single-address geocode using Nominatim+RateLimiter.

    Returns a geopy Location or None. TTL 24 hours to reuse results.
    """
    try:
        from geopy.extra.rate_limiter import RateLimiter
        from geopy.geocoders import Nominatim

        geolocator_local = Nominatim(user_agent="provider_recommender")
        geocode_local = RateLimiter(geolocator_local.geocode, min_delay_seconds=2, max_retries=3)
        return geocode_local(q, timeout=10)
    except GeocoderUnavailable:
        return None
    except Exception:
        return None
