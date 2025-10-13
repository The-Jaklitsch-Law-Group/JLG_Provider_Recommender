# Test Suite Documentation

This directory contains the optimized test suite for the JLG Provider Recommender application.

## Overview

The test suite validates critical functionality including:
- **Data preparation and cleaning pipeline**
- **Provider recommendation scoring algorithm**
- **Radius-based filtering**
- **Geocoding fallback behavior**
- **Input validation (addresses, coordinates, phone numbers)**
- **Distance calculations (haversine formula)**
- **Data cleaning utilities**

## Test Files

### `conftest.py`
Pytest configuration that ensures the project root is on `sys.path` for proper imports.

### `test_data_preparation.py`
Tests the data cleaning and preparation pipeline from raw Excel to cleaned Parquet files.

**Coverage:**
- ✅ Splitting raw data into inbound/outbound referrals
- ✅ Phone number formatting
- ✅ Coordinate parsing and validation
- ✅ Stale file replacement
- ✅ Empty data handling

**Key Tests:**
- `test_process_and_save_cleaned_referrals` - Full pipeline test with realistic data
- `test_process_handles_empty_excel` - Edge case for empty input

### `test_scoring.py`
Tests the core recommendation scoring algorithm in `src/utils/scoring.py`.

**Coverage:**
- ✅ Basic scoring functionality
- ✅ Distance-weighted scoring
- ✅ Outbound referral count weighting (higher = better)
- ✅ Inbound referral count weighting (higher = better)
- ✅ Minimum referral threshold filtering
- ✅ Empty DataFrame handling
- ✅ Score ordering (higher is better)

**Key Tests:**
- `test_recommend_provider_basic` - Validates core scoring with distance priority
- `test_higher_referrals_favored` - Confirms high outbound referrals get higher (better) scores
- `test_inbound_referrals_favored` - Confirms high inbound referrals get higher (better) scores
- `test_min_referrals_filter` - Tests filtering by minimum referral threshold
- `test_empty_dataframe` - Edge case for empty input
- `test_all_filtered_by_min_referrals` - Edge case when all providers filtered out

### `test_radius_filter.py`
Tests radius-based provider filtering functionality.

**Coverage:**
- ✅ Filtering providers within specified radius
- ✅ Distance unit handling (km to miles conversion)
- ✅ Empty DataFrame handling
- ✅ All providers beyond radius edge case

**Key Tests:**
- `test_filter_providers_by_radius_50km` - Tests 50km radius filtering
- `test_filter_providers_by_radius_20km` - Tests 20km radius filtering
- `test_filter_providers_empty_dataframe` - Empty input handling
- `test_filter_providers_all_beyond_radius` - Edge case when no providers in range

### `test_geocode_fallback.py`
Tests geocoding fallback behavior when geopy is not installed.

**Coverage:**
- ✅ Fallback function existence and callability
- ✅ None return value when geopy unavailable
- ✅ GEOPY_AVAILABLE flag setting

**Key Tests:**
- `test_geocode_fallback_returns_none_when_geopy_missing` - Validates fallback behavior (skipped if geopy installed)
- `test_geopy_available_flag` - Checks flag is properly set

### `test_validation.py`
Tests input validation utilities in `src/utils/validation.py`.

**Coverage:**
- ✅ Address validation (street, city, state, zipcode)
- ✅ Coordinate validation (latitude/longitude ranges)
- ✅ Phone number validation (multiple formats)
- ✅ Zipcode format validation (5-digit and ZIP+4)
- ✅ Edge cases (missing fields, invalid formats, boundary values)

**Key Tests:**
- `test_valid_complete_address` - Full valid address
- `test_missing_street/city/state/zipcode` - Missing component detection
- `test_invalid_zipcode_format` - Zipcode format validation
- `test_latitude/longitude_out_of_range` - Coordinate range checking
- `test_valid_phone_with_formatting` - Multiple phone formats (dashes, parentheses, spaces)
- `test_invalid_phone_too_short/long` - Phone number length validation

### `test_distance_calculation.py`
Tests haversine distance calculation in `src/app_logic.py`.

**Coverage:**
- ✅ Accurate distance calculations for known city pairs
- ✅ Same-location distance (should be ~0)
- ✅ Cross-country distances
- ✅ Invalid coordinate handling (returns None)
- ✅ Mathematical properties (symmetry)
- ✅ Edge cases (empty dataframes, mixed valid/invalid, negative coordinates)

**Key Tests:**
- `test_distance_to_same_location` - Same point distance ~0 miles
- `test_known_distance_nyc_to_philadelphia` - Validates ~80 mile distance
- `test_known_distance_baltimore_to_dc` - Validates ~35 mile distance
- `test_cross_country_distance` - NYC to LA (~2,400 miles)
- `test_invalid_coordinates_return_none` - NaN/None coordinate handling
- `test_distance_calculation_is_symmetric` - d(A,B) = d(B,A)

### `test_cleaning.py`
Tests data cleaning utilities in `src/utils/cleaning.py`.

**Coverage:**
- ✅ Address component cleaning (strip, uppercase state)
- ✅ State name to abbreviation mapping (all 50 states + DC)
- ✅ NaN/None/empty string handling
- ✅ Full address construction from components
- ✅ Work address fallback
- ✅ Safe numeric conversion with defaults
- ✅ Comma handling in addresses

**Key Tests:**
- `test_clean_address_components` - String normalization
- `test_state_mapping` - Full state name → abbreviation
- `test_nan_handling` - String "nan"/"None"/"NaN" replacement
- `test_build_complete_address` - Address string construction
- `test_work_address_fallback` - Uses work address when primary missing
- `test_safe_numeric_conversion` - String to number with defaults
- `test_all_50_states_mapped` - STATE_MAPPING completeness check

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run a specific test file
```bash
pytest tests/test_scoring.py -v
```

### Run a specific test
```bash
pytest tests/test_scoring.py::test_recommend_provider_basic -v
```

### Run with coverage report
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run in quiet mode (faster)
```bash
pytest tests/ -q
```

## Test Optimization Changes (2025-10-02)

### Removed Files
- ❌ `test_providers_wrappers.py` - Removed (tested wrapper functions with no business logic)
- ❌ `verify_scoring_change.py` - Removed (verification script, not a test)

### Optimizations Made

1. **Added pytest fixtures** for reusable test data
2. **Improved test names** for better clarity
3. **Added docstrings** explaining what each test validates
4. **Consolidated assertions** for better readability
5. **Added edge case tests** for empty data and filtering scenarios
6. **Removed redundant tests** that didn't add value
7. **Optimized test data** - removed unnecessary fields from fixtures

### Test Count
- **Before:** 12 tests (11 passed, 1 skipped)
- **After:** 14 tests (13 passed, 1 skipped)
- **Coverage improved** with new edge case tests

## Key Testing Principles

1. **Test behavior, not implementation** - Focus on what the code does, not how it does it
2. **Fixtures for reusability** - Share test data across multiple tests
3. **Clear test names** - Names should describe what is being tested
4. **Edge cases matter** - Test empty inputs, boundary conditions, and error paths
5. **Keep tests fast** - Use minimal data needed to validate behavior

## Continuous Integration

Tests run automatically on:
- Every commit to dev/main branches
- Pull requests
- Pre-commit hooks (optional)

## Future Improvements

Potential areas for additional test coverage:
- Integration tests with real Streamlit sessions
- Performance benchmarks for large datasets
- Mock tests for external geocoding APIs
- Data validation edge cases
- Concurrent user session handling
