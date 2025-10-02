"""Test suite for data cleaning utilities.

Tests verify address cleaning, state mapping, and data normalization functions.
"""
import pandas as pd
import pytest

from src.utils.cleaning import STATE_MAPPING, build_full_address, clean_address_data, safe_numeric_conversion


class TestCleanAddressData:
    """Tests for address data cleaning."""

    def test_clean_address_components(self):
        """Test cleaning of address component strings."""
        df = pd.DataFrame(
            {
                "Street": ["  123 Main St  ", "456 Oak Ave"],
                "City": ["Baltimore  ", "  Washington"],
                "State": ["MARYLAND", "VA"],  # Use full state name to test mapping
                "Zip": ["21201", "  20001  "],
            }
        )

        result = clean_address_data(df)

        assert result["Street"].iloc[0] == "123 Main St", "Should strip whitespace"
        assert result["City"].iloc[0] == "Baltimore", "Should strip trailing space"
        assert result["State"].iloc[0] == "MD", "Should uppercase and map state name to abbreviation"
        assert result["Zip"].iloc[0] == "21201", "ZIP should be cleaned"

    def test_state_mapping(self):
        """Test state name to abbreviation mapping."""
        df = pd.DataFrame({"State": ["MARYLAND", "maryland", "Virginia", "DC"]})

        result = clean_address_data(df)

        assert result["State"].iloc[0] == "MD", "MARYLAND should map to MD"
        assert result["State"].iloc[1] == "MD", "Case insensitive mapping"
        assert result["State"].iloc[2] == "VA", "Virginia should map to VA"
        assert result["State"].iloc[3] == "DC", "DC should remain DC"

    def test_state_abbreviation_passthrough(self):
        """Test that existing abbreviations pass through unchanged."""
        df = pd.DataFrame({"State": ["MD", "VA", "NY"]})

        result = clean_address_data(df)

        assert result["State"].iloc[0] == "MD"
        assert result["State"].iloc[1] == "VA"
        assert result["State"].iloc[2] == "NY"

    def test_nan_handling(self):
        """Test handling of NaN and None values."""
        df = pd.DataFrame(
            {
                "Street": ["123 Main", "nan"],  # String "nan" gets replaced
                "City": ["None", "Baltimore"],  # String "None" gets replaced
                "State": ["MD", "NaN"],  # String "NaN" gets replaced
                "Zip": ["", "21201"],  # Empty string gets replaced
            }
        )

        result = clean_address_data(df)

        # The function replaces the strings "nan", "None", "NaN", "" with pd.NA, then fillna("")
        assert result["Street"].iloc[1] == "", "String 'nan' should become empty string"
        assert result["City"].iloc[0] == "", "String 'None' should become empty string"
        assert result["State"].iloc[1] == "", "String 'NaN' should become empty string"
        assert result["Zip"].iloc[0] == "", "Empty string should remain empty"

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=["Street", "City", "State", "Zip"])

        result = clean_address_data(df)

        assert len(result) == 0
        assert list(result.columns) == ["Street", "City", "State", "Zip"]


class TestBuildFullAddress:
    """Tests for building full addresses from components."""

    def test_build_complete_address(self):
        """Test building address from all components."""
        df = pd.DataFrame({"Street": ["123 Main St"], "City": ["Baltimore"], "State": ["MD"], "Zip": ["21201"]})

        result = build_full_address(df)

        assert "Full Address" in result.columns
        assert result["Full Address"].iloc[0] == "123 Main St, Baltimore, MD, 21201"

    def test_partial_address_components(self):
        """Test building address with some missing components."""
        df = pd.DataFrame({"Street": ["123 Main St"], "City": ["Baltimore"], "State": [""], "Zip": [""]})

        result = build_full_address(df)

        assert result["Full Address"].iloc[0] == "123 Main St, Baltimore"

    def test_existing_full_address_preserved(self):
        """Test that existing non-empty Full Address is preserved."""
        df = pd.DataFrame(
            {
                "Full Address": ["Complete Address"],
                "Street": ["123 Main St"],
                "City": ["Baltimore"],
                "State": ["MD"],
                "Zip": ["21201"],
            }
        )

        result = build_full_address(df)

        assert result["Full Address"].iloc[0] == "Complete Address"

    def test_empty_full_address_gets_constructed(self):
        """Test that empty Full Address gets constructed from components."""
        df = pd.DataFrame(
            {"Full Address": [""], "Street": ["123 Main St"], "City": ["Baltimore"], "State": ["MD"], "Zip": ["21201"]}
        )

        result = build_full_address(df)

        assert result["Full Address"].iloc[0] == "123 Main St, Baltimore, MD, 21201"

    def test_work_address_fallback(self):
        """Test fallback to Work Address when Full Address is empty."""
        df = pd.DataFrame(
            {
                "Full Address": [""],
                "Work Address": ["456 Office Blvd, DC"],
                "Street": [""],
                "City": [""],
                "State": [""],
                "Zip": [""],
            }
        )

        result = build_full_address(df)

        assert result["Full Address"].iloc[0] == "456 Office Blvd, DC"

    def test_no_duplicate_commas(self):
        """Test that duplicate commas are removed."""
        df = pd.DataFrame(
            {
                "Street": ["123 Main St"],
                "City": [""],  # Empty city creates potential for duplicate commas
                "State": ["MD"],
                "Zip": ["21201"],
            }
        )

        result = build_full_address(df)

        # Should not have ,, in the result
        assert ",," not in result["Full Address"].iloc[0]

    def test_no_trailing_comma(self):
        """Test that trailing commas are removed."""
        df = pd.DataFrame({"Street": ["123 Main St"], "City": ["Baltimore"], "State": [""], "Zip": [""]})

        result = build_full_address(df)

        # Should not end with comma
        assert not result["Full Address"].iloc[0].endswith(",")


class TestSafeNumericConversion:
    """Tests for safe numeric conversion utility."""

    def test_convert_string_number(self):
        """Test conversion of numeric string."""
        result = safe_numeric_conversion("123.45")
        assert result == 123.45

    def test_convert_integer(self):
        """Test conversion of integer."""
        result = safe_numeric_conversion(42)
        assert result == 42.0

    def test_convert_float(self):
        """Test conversion of float."""
        result = safe_numeric_conversion(3.14159)
        assert result == 3.14159

    def test_convert_nan_returns_default(self):
        """Test that NaN returns default value."""
        result = safe_numeric_conversion(pd.NA, default=0.0)
        assert result == 0.0

    def test_convert_none_returns_default(self):
        """Test that None returns default value."""
        result = safe_numeric_conversion(None, default=-1.0)
        assert result == -1.0

    def test_convert_invalid_string_returns_default(self):
        """Test that invalid string returns default value."""
        result = safe_numeric_conversion("not_a_number", default=99.9)
        assert result == 99.9

    def test_negative_numbers(self):
        """Test conversion of negative numbers."""
        assert safe_numeric_conversion("-123.45") == -123.45
        assert safe_numeric_conversion(-42) == -42.0

    def test_zero(self):
        """Test conversion of zero."""
        assert safe_numeric_conversion("0") == 0.0
        assert safe_numeric_conversion(0) == 0.0


class TestStateMappingCompleteness:
    """Tests to verify STATE_MAPPING completeness."""

    def test_all_50_states_mapped(self):
        """Test that all 50 US states are in the mapping."""
        # Should have 50 states + DC
        assert len(STATE_MAPPING) == 51, "Should have 50 states plus DC"

    def test_dc_included(self):
        """Test that District of Columbia is included."""
        assert "DISTRICT OF COLUMBIA" in STATE_MAPPING
        assert STATE_MAPPING["DISTRICT OF COLUMBIA"] == "DC"

    def test_all_abbreviations_are_two_letters(self):
        """Test that all state abbreviations are exactly 2 letters."""
        for abbrev in STATE_MAPPING.values():
            assert len(abbrev) == 2, f"{abbrev} should be 2 letters"
            assert abbrev.isupper(), f"{abbrev} should be uppercase"

    def test_common_states(self):
        """Test that common states are correctly mapped."""
        assert STATE_MAPPING["MARYLAND"] == "MD"
        assert STATE_MAPPING["VIRGINIA"] == "VA"
        assert STATE_MAPPING["NEW YORK"] == "NY"
        assert STATE_MAPPING["CALIFORNIA"] == "CA"
        assert STATE_MAPPING["TEXAS"] == "TX"
        assert STATE_MAPPING["FLORIDA"] == "FL"
