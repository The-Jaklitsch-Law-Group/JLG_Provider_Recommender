# Specialty Filtering Feature

## Overview

The specialty filtering feature allows users to search for providers by their medical specialty. This feature was added to support the growing diversity of provider types in the referral network, moving beyond the original assumption that all providers are chiropractors or physical therapists.

## User Interface

### Search Page (pages/1_🔎_Search.py)

In the "Advanced Filters" section, users will find a new **"Filter by Specialty"** multi-select widget that:

1. Automatically extracts all unique specialties from the provider database
2. Defaults to selecting ALL specialties (inclusive approach)
3. Allows users to narrow their search to specific specialties
4. Handles providers with multiple specialties (comma-separated values)

### Results Page (pages/2_📄_Results.py)

The specialty information is prominently displayed:

1. **Search Criteria Sidebar**: Shows selected specialties in the search summary
2. **Best Match Card**: Displays the specialty of the top-recommended provider (if available)
3. **Results Table**: Includes a "Specialty" column showing each provider's specialty/specialties

## Technical Implementation

### Data Schema

The specialty data comes from the preferred providers Excel file with the column:
- Source: `Contact's Details: Specialty`
- Mapped to: `Specialty`

### Key Functions

1. **`get_unique_specialties(provider_df)`** (src/app_logic.py)
   - Extracts unique specialty values from provider DataFrame
   - Handles comma-separated multiple specialties
   - Returns sorted list of unique specialty strings

2. **`filter_providers_by_specialty(df, selected_specialties)`** (src/app_logic.py)
   - Filters providers based on selected specialties
   - Matches if ANY of a provider's specialties is in the selected list
   - Returns filtered DataFrame

3. **`run_recommendation(..., selected_specialties=None)`** (src/app_logic.py)
   - Updated to accept optional `selected_specialties` parameter
   - Applies specialty filter BEFORE distance calculations and scoring
   - Default behavior (None) includes all providers

### Data Flow

1. User selects specialties in search form (or keeps default "all")
2. Selected specialties saved to session state
3. Specialty filter applied early in recommendation workflow:
   - Before referral count filter
   - Before distance calculations
   - Before scoring
4. Results include only providers matching selected specialties

## Edge Cases Handled

1. **Missing Specialty Data**: Providers without specialty information are excluded when specialty filter is active
2. **Multiple Specialties**: Providers with comma-separated specialties (e.g., "Chiropractic, Physical Therapy") match if ANY specialty is selected
3. **Whitespace Variations**: Leading/trailing whitespace is trimmed when parsing specialties
4. **No Specialty Column**: If Specialty column doesn't exist in data, filter is skipped gracefully
5. **Empty Selection**: Empty specialty list returns all providers (no filtering)

## Testing

Comprehensive test suite in `tests/test_specialty_filtering.py` covers:
- Unique specialty extraction
- Single and multiple specialty filtering
- Multi-specialty provider matching
- Edge cases (empty data, missing columns, null values)
- Whitespace handling
- DataFrame structure preservation

All 14 specialty filtering tests pass ✅

## Usage Examples

### Example 1: Search for Chiropractors Only
```python
selected_specialties = ["Chiropractic"]
best, results = run_recommendation(
    provider_df, 
    user_lat, 
    user_lon,
    min_referrals=0,
    max_radius_miles=25,
    alpha=0.5,
    beta=0.5,
    gamma=0.0,
    preferred_weight=0.0,
    selected_specialties=selected_specialties
)
```

### Example 2: Search for Multiple Specialties
```python
selected_specialties = ["Chiropractic", "Physical Therapy", "Neurology"]
# Provider with "Chiropractic, Physical Therapy" will match
```

### Example 3: No Specialty Filter (Default)
```python
# Pass None or omit parameter to include all providers
best, results = run_recommendation(
    provider_df, 
    user_lat, 
    user_lon,
    # ... other params
    selected_specialties=None  # or omit entirely
)
```

## Future Enhancements

Potential improvements for future iterations:

1. **Synonym Handling**: Map "PT" to "Physical Therapy", "Chiro" to "Chiropractic", etc.
2. **Specialty Categories**: Group related specialties (e.g., "Orthopedic Specialties")
3. **Fuzzy Matching**: Handle slight variations in specialty naming
4. **Preferred Specialty Order**: Allow users to rank specialty importance in scoring
5. **Specialty-Based Weighting**: Different scoring weights per specialty type
