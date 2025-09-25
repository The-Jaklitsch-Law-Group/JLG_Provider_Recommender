"""Data processing package for JLG Provider Recommender."""

# Import main data functions for backward compatibility
from .ingestion import (
    get_data_ingestion_status,
    load_detailed_referrals,
    load_inbound_referrals,
    load_provider_data,
    refresh_data_cache,
)
from .preparation import PreparationSummary, process_and_save_cleaned_referrals

__all__ = [
    "get_data_ingestion_status",
    "load_detailed_referrals",
    "load_inbound_referrals",
    "load_provider_data",
    "refresh_data_cache",
    "PreparationSummary",
    "process_and_save_cleaned_referrals",
]
