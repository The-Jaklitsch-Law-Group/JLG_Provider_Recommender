"""Compatibility wrapper re-exporting the smaller utility modules.

This file preserves the original import locations used across the codebase
and tests. The actual implementations live in the smaller modules in this
package: cleaning, addressing, geocoding, scoring, and io_utils.
"""

from .addressing import validate_address, validate_address_input, validate_coordinates, validate_phone_number
from .cleaning import (
    build_full_address,
    clean_address_data,
    load_provider_data,
    safe_numeric_conversion,
    validate_and_clean_coordinates,
    validate_provider_data,
)
from .geocoding import cached_geocode_address, geocode_address_with_cache, handle_geocoding_error
from .io_utils import get_word_bytes, handle_streamlit_error, sanitize_filename
from .scoring import calculate_distances, recommend_provider

__all__ = [
    "load_provider_data",
    "clean_address_data",
    "build_full_address",
    "safe_numeric_conversion",
    "validate_address",
    "validate_address_input",
    "validate_coordinates",
    "geocode_address_with_cache",
    "cached_geocode_address",
    "handle_geocoding_error",
    "calculate_distances",
    "recommend_provider",
    "validate_provider_data",
    "validate_and_clean_coordinates",
    "validate_phone_number",
    "sanitize_filename",
    "handle_streamlit_error",
    "get_word_bytes",
]
