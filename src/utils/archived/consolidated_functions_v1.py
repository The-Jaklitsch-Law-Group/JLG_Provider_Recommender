# flake8: noqa
"""Archived snapshot of the original consolidated utilities.

This file contains a formatted, read-only snapshot of the original
`consolidated_functions.py` used during refactoring. The active, refactored
implementations live in `src/utils/` and this module is not imported by the
application. It is intentionally excluded from linting in project config.

This archived file provides a human-readable reference only and is kept small
to avoid linter/tool noise.
"""

from typing import Any, List, Optional, Tuple

# Minimal illustrative helpers preserved from the original snapshot.

STATE_MAPPING = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
    "DISTRICT OF COLUMBIA": "DC",
}


def validate_address(address: str) -> Tuple[bool, str]:
    """Lightweight address validation used for archival reference.

    This function performs very basic checks (non-empty, contains number,
    length) and returns a boolean and short message. Use production geocoding
    utilities in `src/utils/` for real validation.
    """
    if not address or not address.strip():
        return False, "Address cannot be empty"
    address = address.strip()
    if len(address) < 10:
        return False, "Address appears too short."
    has_number = any(char.isdigit() for char in address)
    if not has_number:
        return False, "Address should include a street number"
    return True, ""


def sanitize_filename(name: str) -> str:
    """Return a filesystem-safe filename fragment."""
    import re

    return re.sub(r"[^A-Za-z0-9_]", "", name.replace(" ", "_"))


__all__ = ["STATE_MAPPING", "validate_address", "sanitize_filename"]
