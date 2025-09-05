"""
Security and input validation utilities for the JLG Provider Recommender.

This module provides centralized security configuration, input validation,
and sanitization functions to ensure safe operation of the application.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import pandas as pd

# Configure logging for security events
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger("security")


class SecurityConfig:
    """Centralized security configuration and API key management."""

    @staticmethod
    def get_api_key(service_name: str) -> Optional[str]:
        """
        Safely retrieve API keys from environment variables.

        Args:
            service_name (str): Name of the service (e.g., 'NOMINATIM', 'MAPS')

        Returns:
            Optional[str]: API key if found, None otherwise

        Example:
            >>> api_key = SecurityConfig.get_api_key('NOMINATIM')
        """
        return os.getenv(f"{service_name.upper()}_API_KEY")

    @staticmethod
    def get_config_value(key: str, default: Any = None) -> Any:
        """
        Get configuration value from environment with default fallback.

        Args:
            key (str): Configuration key
            default (Any): Default value if key not found

        Returns:
            Any: Configuration value or default
        """
        return os.getenv(key, default)


class InputValidator:
    """Input validation and sanitization utilities."""

    # Address validation patterns
    US_STATE_PATTERN = re.compile(r"^[A-Z]{2}$")
    ZIP_CODE_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")
    PHONE_PATTERN = re.compile(r"^[\d\s\-\(\)\+\.]{10,}$")

    @staticmethod
    def validate_address_input(street: str, city: str, state: str, zipcode: str) -> tuple[bool, str]:
        """
        Comprehensive address validation with detailed error messages.

        Args:
            street (str): Street address
            city (str): City name
            state (str): State abbreviation (2 letters)
            zipcode (str): ZIP code (5 or 9 digits)

        Returns:
            tuple[bool, str]: (is_valid, error_message)

        Example:
            >>> is_valid, msg = InputValidator.validate_address_input(
            ...     "123 Main St", "Anytown", "CA", "12345"
            ... )
        """
        errors = []

        # Validate street
        if not street or len(street.strip()) < 3:
            errors.append("Street address must be at least 3 characters")
        elif len(street) > 100:
            errors.append("Street address too long (max 100 characters)")

        # Validate city
        if not city or len(city.strip()) < 2:
            errors.append("City must be at least 2 characters")
        elif len(city) > 50:
            errors.append("City name too long (max 50 characters)")
        elif not re.match(r"^[a-zA-Z\s\-\.]+$", city):
            errors.append("City contains invalid characters")

        # Validate state
        if not state:
            errors.append("State is required")
        elif not InputValidator.US_STATE_PATTERN.match(state.upper()):
            errors.append("State must be a valid 2-letter abbreviation (e.g., 'CA', 'NY')")

        # Validate ZIP code
        if not zipcode:
            errors.append("ZIP code is required")
        elif not InputValidator.ZIP_CODE_PATTERN.match(zipcode.strip()):
            errors.append("ZIP code must be 5 digits or 5+4 format (e.g., '12345' or '12345-6789')")

        is_valid = len(errors) == 0
        error_message = "; ".join(errors) if errors else ""

        return is_valid, error_message

    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 1000, allow_html: bool = False) -> str:
        """
        Sanitize text input to prevent injection attacks.

        Args:
            text (str): Input text to sanitize
            max_length (int): Maximum allowed length
            allow_html (bool): Whether to allow HTML tags

        Returns:
            str: Sanitized text

        Raises:
            ValueError: If input is too long or contains forbidden characters
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")

        # Length validation
        if len(text) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")

        # Basic sanitization
        sanitized = text.strip()

        # Remove or escape HTML if not allowed
        if not allow_html:
            # Remove HTML tags
            sanitized = re.sub(r"<[^>]+>", "", sanitized)

        # Remove potentially dangerous characters
        dangerous_chars = ["<script", "javascript:", "data:", "vbscript:"]
        for char in dangerous_chars:
            if char.lower() in sanitized.lower():
                security_logger.warning(f"Potentially dangerous input detected: {char}")
                sanitized = sanitized.replace(char, "")

        return sanitized

    @staticmethod
    def validate_coordinate(value: Any, coord_type: str = "latitude") -> tuple[bool, str]:
        """
        Validate geographic coordinates.

        Args:
            value (Any): Coordinate value to validate
            coord_type (str): Type of coordinate ("latitude" or "longitude")

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            coord = float(value)
        except (ValueError, TypeError):
            return False, f"Invalid {coord_type}: must be a number"

        if coord_type.lower() == "latitude":
            if not -90 <= coord <= 90:
                return False, f"Latitude must be between -90 and 90 degrees"
        elif coord_type.lower() == "longitude":
            if not -180 <= coord <= 180:
                return False, f"Longitude must be between -180 and 180 degrees"
        else:
            return False, f"Unknown coordinate type: {coord_type}"

        return True, ""

    @staticmethod
    def validate_dataframe_schema(df: pd.DataFrame, required_columns: List[str]) -> tuple[bool, str]:
        """
        Validate DataFrame has required columns and basic data integrity.

        Args:
            df (pd.DataFrame): DataFrame to validate
            required_columns (List[str]): List of required column names

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        if df.empty:
            return False, "DataFrame is empty"

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"

        # Check for completely empty columns
        empty_columns = [col for col in required_columns if df[col].isna().all()]
        if empty_columns:
            return False, f"Required columns are completely empty: {', '.join(empty_columns)}"

        return True, ""


class DataSanitizer:
    """Data sanitization utilities for provider and referral data."""

    @staticmethod
    def sanitize_provider_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Sanitize provider data for security and consistency.

        Args:
            df (pd.DataFrame): Raw provider data

        Returns:
            pd.DataFrame: Sanitized provider data
        """
        df_clean = df.copy()

        # Sanitize text columns
        text_columns = ["Full Name", "Street", "City", "Specialty"]
        for col in text_columns:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(
                    lambda x: InputValidator.sanitize_text_input(str(x), max_length=200) if pd.notna(x) else ""
                )

        # Validate and clean ZIP codes
        if "Zip" in df_clean.columns:
            df_clean["Zip"] = df_clean["Zip"].apply(DataSanitizer._clean_zip_code)

        # Validate coordinates
        for coord_col, coord_type in [("Latitude", "latitude"), ("Longitude", "longitude")]:
            if coord_col in df_clean.columns:
                df_clean[coord_col] = df_clean[coord_col].apply(
                    lambda x: DataSanitizer._validate_coordinate_value(x, coord_type)
                )

        return df_clean

    @staticmethod
    def _clean_zip_code(zip_code: Any) -> str:
        """Clean and validate ZIP code format."""
        if pd.isna(zip_code):
            return ""

        zip_str = str(zip_code).strip()

        # Remove non-digit characters except hyphens
        zip_clean = re.sub(r"[^\d\-]", "", zip_str)

        # Validate format
        if InputValidator.ZIP_CODE_PATTERN.match(zip_clean):
            return zip_clean
        else:
            return ""  # Return empty string for invalid ZIP codes

    @staticmethod
    def _validate_coordinate_value(coord: Any, coord_type: str) -> Optional[float]:
        """Validate and return coordinate value or None if invalid."""
        is_valid, _ = InputValidator.validate_coordinate(coord, coord_type)
        if is_valid:
            return float(coord)
        else:
            return None


# Export main classes and functions
__all__ = ["SecurityConfig", "InputValidator", "DataSanitizer"]
