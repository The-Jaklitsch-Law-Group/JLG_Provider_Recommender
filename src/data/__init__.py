"""Data processing package for JLG Provider Recommender."""

# Import main data functions for backward compatibility
from .ingestion import (
    get_data_ingestion_status,
    load_detailed_referrals,
    load_inbound_referrals,
    load_provider_data,
    load_preferred_providers,
    refresh_data_cache,
)
from .preparation import PreparationSummary, PreferredProvidersSummary, process_and_save_cleaned_referrals, process_referral_data, process_and_save_preferred_providers, process_preferred_providers

__all__ = [
    "get_data_ingestion_status",
    "load_detailed_referrals",
    "load_inbound_referrals",
    "load_provider_data",
    "load_preferred_providers",
    "refresh_data_cache",
    "PreparationSummary",
    "PreferredProvidersSummary",
    "process_and_save_cleaned_referrals",
    "process_referral_data",
    "process_and_save_preferred_providers",
    "process_preferred_providers",
]
