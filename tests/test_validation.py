"""Test suite for validation utilities.

Tests verify address, coordinate, and phone number validation functions.
"""
import pytest

from src.utils.validation import validate_address_input, validate_coordinates, validate_phone_number


class TestValidateAddressInput:
    """Tests for address component validation."""

    def test_valid_complete_address(self):
        """Test validation of a complete, valid address."""
        valid, msg = validate_address_input(street="123 Main Street", city="Baltimore", state="MD", zipcode="21201")
        assert valid is True, "Complete address should be valid"
        assert msg == "Valid address"

    def test_missing_street(self):
        """Test that missing street address fails validation."""
        valid, msg = validate_address_input(street="", city="Baltimore", state="MD", zipcode="21201")
        assert valid is False, "Missing street should fail validation"
        assert "Street address is required" in msg

    def test_missing_city(self):
        """Test that missing city fails validation."""
        valid, msg = validate_address_input(street="123 Main St", city="", state="MD", zipcode="21201")
        assert valid is False, "Missing city should fail validation"
        assert "City is required" in msg

    def test_missing_state(self):
        """Test that missing state fails validation."""
        valid, msg = validate_address_input(street="123 Main St", city="Baltimore", state="", zipcode="21201")
        assert valid is False, "Missing state should fail validation"
        assert "State is required" in msg

    def test_missing_zipcode(self):
        """Test that missing ZIP code fails validation."""
        valid, msg = validate_address_input(street="123 Main St", city="Baltimore", state="MD", zipcode="")
        assert valid is False, "Missing ZIP code should fail validation"
        assert "ZIP code is required" in msg

    def test_invalid_zipcode_format(self):
        """Test that invalid ZIP code format fails validation."""
        valid, msg = validate_address_input(street="123 Main St", city="Baltimore", state="MD", zipcode="ABCDE")
        assert valid is False, "Invalid ZIP format should fail validation"
        assert "ZIP code must be in format" in msg

    def test_valid_zipcode_plus_four(self):
        """Test that ZIP+4 format is valid."""
        valid, msg = validate_address_input(street="123 Main St", city="Baltimore", state="MD", zipcode="21201-1234")
        assert valid is True, "ZIP+4 format should be valid"


class TestValidateCoordinates:
    """Tests for coordinate validation."""

    def test_valid_coordinates(self):
        """Test validation of valid coordinates."""
        valid, msg = validate_coordinates(39.2904, -76.6122)
        assert valid is True, "Valid coordinates should pass"
        assert msg == "Valid coordinates"

    def test_latitude_out_of_range_high(self):
        """Test that latitude > 90 fails validation."""
        valid, msg = validate_coordinates(91.0, -76.0)
        assert valid is False, "Latitude > 90 should fail"
        assert "Latitude must be between -90 and 90" in msg

    def test_latitude_out_of_range_low(self):
        """Test that latitude < -90 fails validation."""
        valid, msg = validate_coordinates(-91.0, -76.0)
        assert valid is False, "Latitude < -90 should fail"
        assert "Latitude must be between -90 and 90" in msg

    def test_longitude_out_of_range_high(self):
        """Test that longitude > 180 fails validation."""
        valid, msg = validate_coordinates(39.0, 181.0)
        assert valid is False, "Longitude > 180 should fail"
        assert "Longitude must be between -180 and 180" in msg

    def test_longitude_out_of_range_low(self):
        """Test that longitude < -180 fails validation."""
        valid, msg = validate_coordinates(39.0, -181.0)
        assert valid is False, "Longitude < -180 should fail"
        assert "Longitude must be between -180 and 180" in msg

    def test_non_numeric_coordinates(self):
        """Test that non-numeric coordinates fail validation."""
        valid, msg = validate_coordinates("not_a_number", -76.0)  # type: ignore
        assert valid is False, "Non-numeric coordinates should fail"
        assert "Coordinates must be numeric" in msg

    def test_boundary_values(self):
        """Test validation at coordinate boundaries."""
        # Test all boundary values
        assert validate_coordinates(90.0, 180.0)[0] is True
        assert validate_coordinates(-90.0, -180.0)[0] is True
        assert validate_coordinates(0.0, 0.0)[0] is True


class TestValidatePhoneNumber:
    """Tests for phone number validation."""

    def test_valid_10_digit_phone(self):
        """Test validation of 10-digit phone number."""
        valid, msg = validate_phone_number("3015551234")
        assert valid is True, "10-digit phone should be valid"
        assert "Valid phone number" in msg

    def test_valid_phone_with_formatting(self):
        """Test validation of formatted phone number."""
        valid, msg = validate_phone_number("(301) 555-1234")
        assert valid is True, "Formatted phone should be valid"
        assert "Valid phone number" in msg

    def test_valid_11_digit_phone(self):
        """Test validation of 11-digit phone number starting with 1."""
        valid, msg = validate_phone_number("13015551234")
        assert valid is True, "11-digit phone starting with 1 should be valid"
        assert "Valid phone number" in msg

    def test_valid_phone_with_dashes(self):
        """Test validation of phone with dashes."""
        valid, msg = validate_phone_number("301-555-1234")
        assert valid is True, "Phone with dashes should be valid"

    def test_invalid_phone_too_short(self):
        """Test that phone with too few digits fails validation."""
        valid, msg = validate_phone_number("555123")
        assert valid is False, "Too few digits should fail"
        assert "Phone number must be 10 digits" in msg

    def test_invalid_phone_too_long(self):
        """Test that phone with too many digits fails validation."""
        valid, msg = validate_phone_number("12345678901234")
        assert valid is False, "Too many digits should fail"

    def test_empty_phone_is_valid(self):
        """Test that empty phone number is considered valid (optional)."""
        valid, msg = validate_phone_number("")
        assert valid is True, "Empty phone should be valid (optional field)"
        assert "optional" in msg.lower()

    def test_phone_with_spaces(self):
        """Test validation of phone with spaces."""
        valid, msg = validate_phone_number("301 555 1234")
        assert valid is True, "Phone with spaces should be valid"
