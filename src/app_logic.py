import datetime as dt
from typing import Tuple, Optional

import pandas as pd
import streamlit as st

from src.data.ingestion import load_detailed_referrals, load_inbound_referrals
from src.utils.cleaning import (
    build_full_address,
    clean_address_data,
    validate_and_clean_coordinates,
    validate_provider_data,
)
from src.utils.providers import (
    calculate_inbound_referral_counts,
    calculate_time_based_referral_counts,
    load_and_validate_provider_data,
)
from src.utils.scoring import calculate_distances, recommend_provider

__all__ = [
    "load_application_data",
    "apply_time_filtering",
    "filter_providers_by_radius",
    "run_recommendation",
    "validate_provider_data",
]


@st.cache_data(ttl=3600)
def load_application_data():
    """Load and enrich provider + referral data for the application."""
    provider_df = load_and_validate_provider_data()

    if provider_df.empty:
        try:
            from src.data.ingestion import load_provider_data as _fallback_loader

            provider_df = _fallback_loader()
        except Exception:
            pass

    if not provider_df.empty:
        provider_df = validate_and_clean_coordinates(provider_df)
        provider_df = clean_address_data(provider_df)
        for col in ["Street", "City", "State", "Zip", "Full Address"]:
            if col in provider_df.columns:
                provider_df[col] = (
                    provider_df[col].astype(str).replace(["nan", "None", "NaN"], "").fillna("")
                )
        if "Full Address" not in provider_df.columns or provider_df["Full Address"].isna().any():
            provider_df = build_full_address(provider_df)
        if "Full Name" in provider_df.columns:
            provider_df = provider_df.drop_duplicates(subset=["Full Name"], keep="first")
        phone_candidates = [
            col
            for col in ["Work Phone Number", "Work Phone", "Phone Number", "Phone 1"]
            if col in provider_df.columns
        ]
        if phone_candidates:
            phone_source = phone_candidates[0]
            provider_df["Work Phone Number"] = provider_df[phone_source]
            if "Work Phone" not in provider_df.columns:
                provider_df["Work Phone"] = provider_df["Work Phone Number"]
            if "Phone Number" not in provider_df.columns:
                provider_df["Phone Number"] = provider_df["Work Phone Number"]

    detailed_referrals_df = load_detailed_referrals()
    inbound_referrals_df = load_inbound_referrals()

    if not provider_df.empty:
        if not inbound_referrals_df.empty:
            inbound_counts_df = calculate_inbound_referral_counts(inbound_referrals_df)
            if (
                not inbound_counts_df.empty
                and "Full Name" in provider_df.columns
                and "Full Name" in inbound_counts_df.columns
            ):
                provider_df = provider_df.merge(
                    inbound_counts_df[["Full Name", "Inbound Referral Count"]],
                    on="Full Name",
                    how="left",
                )
                provider_df["Inbound Referral Count"] = provider_df["Inbound Referral Count"].fillna(0)
            else:
                provider_df["Inbound Referral Count"] = 0
    # --- Preferred providers: include the preferred list and mark providers ---
    try:
        from src.data.ingestion import load_preferred_providers

        preferred_df = load_preferred_providers()
        if preferred_df is not None and not preferred_df.empty and "Full Name" in preferred_df.columns:
            pref_names = preferred_df[["Full Name"]].drop_duplicates()
            # Merge outer so preferred-only providers are included
            provider_df = provider_df.merge(pref_names, on="Full Name", how="outer", indicator=True)
            # Mark preferred where the merge shows presence in preferred list (boolean)
            provider_df["Preferred Provider"] = provider_df["_merge"].apply(lambda v: True if v in ("both", "right_only") else False)
            provider_df = provider_df.drop(columns=["_merge"])
        else:
            # No preferred list available or no Full Name column
            # Ensure the column exists as boolean; default to False when missing
            provider_df["Preferred Provider"] = provider_df.get("Preferred Provider", False)
    except Exception:
        provider_df["Preferred Provider"] = provider_df.get("Preferred Provider", False)

    # Ensure referral counts are numeric and fill missing with zero (important when preferred list added new rows)
    if "Referral Count" in provider_df.columns:
        provider_df["Referral Count"] = pd.to_numeric(provider_df["Referral Count"], errors="coerce").fillna(0)
    else:
        provider_df["Referral Count"] = 0

    # Ensure inbound referral count exists
    if "Inbound Referral Count" in provider_df.columns:
        provider_df["Inbound Referral Count"] = pd.to_numeric(provider_df["Inbound Referral Count"], errors="coerce").fillna(0)
    else:
        provider_df["Inbound Referral Count"] = 0

    return provider_df, detailed_referrals_df


def apply_time_filtering(provider_df, detailed_referrals_df, start_date, end_date):
    """Apply time-based filtering for outbound and inbound referrals."""
    working_df = provider_df.copy()
    if not detailed_referrals_df.empty:
        time_filtered_outbound = calculate_time_based_referral_counts(
            detailed_referrals_df, start_date, end_date
        )
        if not time_filtered_outbound.empty:
            working_df = working_df.drop(columns=["Referral Count"], errors="ignore").merge(
                time_filtered_outbound[["Full Name", "Referral Count"]], on="Full Name", how="left"
            )
            working_df["Referral Count"] = working_df["Referral Count"].fillna(0)

    inbound_referrals_df = load_inbound_referrals()
    if not inbound_referrals_df.empty:
        time_filtered_inbound = calculate_inbound_referral_counts(
            inbound_referrals_df, start_date, end_date
        )
        if not time_filtered_inbound.empty:
            working_df = working_df.drop(columns=["Inbound Referral Count"], errors="ignore").merge(
                time_filtered_inbound[["Full Name", "Inbound Referral Count"]], on="Full Name", how="left"
            )
            working_df["Inbound Referral Count"] = working_df["Inbound Referral Count"].fillna(0)
    return working_df


def filter_providers_by_radius(df: pd.DataFrame, max_radius_miles: float) -> pd.DataFrame:
    """Filter providers by maximum radius (miles)."""
    if df is None or df.empty or "Distance (Miles)" not in df.columns:
        return df
    return df[df["Distance (Miles)"] <= max_radius_miles].copy()


def run_recommendation(
    provider_df: pd.DataFrame,
    user_lat: float,
    user_lon: float,
    *,
    min_referrals: int,
    max_radius_miles: int,
    alpha: float,
    beta: float,
    gamma: float,
    preferred_weight: float = 0.1,
):
    """Run distance calculation, radius filter and composite recommendation."""
    working = provider_df[provider_df["Referral Count"] >= min_referrals].copy()
    if working.empty:
        return None, pd.DataFrame()
    working["Distance (Miles)"] = calculate_distances(user_lat, user_lon, working)
    working = filter_providers_by_radius(working, max_radius_miles)
    if working.empty:
        return None, pd.DataFrame()
    best, scored_df = recommend_provider(
        working,
        distance_weight=alpha,
        referral_weight=beta,
        inbound_weight=gamma,
        preferred_weight=preferred_weight,
        min_referrals=min_referrals,
    )
    if scored_df is not None and not scored_df.empty and "Full Name" in scored_df.columns:
        scored_df = scored_df.drop_duplicates(subset=["Full Name"], keep="first")
    return best, scored_df
