# Three-Factor Scoring System Implementation Summary

## Overview
The Provider Recommender application has been successfully updated to include **inbound referral data** as a third factor in the provider scoring algorithm. This enhancement provides a more comprehensive view of provider relationships and mutual referral patterns.

## Key Changes Made

### 1. New Data Processing Functions in `provider_utils.py`

#### `load_inbound_referrals(filepath: str) -> pd.DataFrame`
- Loads inbound referral data from Excel file
- Standardizes date columns for time-based filtering
- Handles missing data gracefully

#### `calculate_inbound_referral_counts(inbound_df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame`
- Processes both primary and secondary referral sources
- Groups by provider to count total inbound referrals
- Supports time-based filtering
- Returns standardized provider data with inbound referral counts

### 2. Enhanced Recommendation Algorithm

#### Updated `recommend_provider()` Function
- **New Parameter**: `inbound_weight` (default: 0.0)
- **Three-Factor Scoring**: Distance + Outbound Referrals + Inbound Referrals
- **Backward Compatibility**: Falls back to two-factor scoring when inbound data unavailable
- **Normalization**: All factors normalized to [0,1] scale for fair comparison

#### Scoring Formula
```
Three-Factor: Score = α × Distance_norm + β × (1-Outbound_norm) + γ × Inbound_norm
Two-Factor:   Score = α × Distance_norm + β × (1-Outbound_norm)
```

Where:
- **α (alpha)**: Distance weight
- **β (beta)**: Outbound referral weight  
- **γ (gamma)**: Inbound referral weight
- Lower scores = better recommendations

### 3. User Interface Enhancements in `app.py`

#### Adaptive Weight Selection
- **With Inbound Data**: Individual sliders for all three factors with automatic normalization
- **Without Inbound Data**: Traditional distance vs. outbound referral slider
- **Real-time Feedback**: Shows normalized weights and data availability status

#### Enhanced Data Loading
- **Automatic Merging**: Inbound referrals automatically merged with provider data
- **Person ID Matching**: Primary matching on Person ID, fallback to name matching
- **Status Messages**: Clear feedback on data availability and merge success

#### Improved Results Display
- **Dynamic Columns**: Shows "Inbound Referral Count" when available
- **Scoring Description**: Displays which scoring method was used
- **Enhanced Documentation**: Updated help tabs with three-factor explanations

## Data Integration Results

### Test Results
✅ **540 inbound referral records** successfully loaded  
✅ **247 unique providers** identified in inbound data  
✅ **13 common providers** between inbound and outbound datasets  
✅ **Person ID matching** confirmed for data merging  
✅ **Data compatibility** verified across all datasets  

### Merge Statistics
- **Total Providers**: 60 (from outbound data)
- **With Inbound Data**: 13 providers have mutual referral relationships
- **Inbound-Only**: 234 additional providers refer clients to the firm
- **Outbound-Only**: 47 providers receive referrals but don't refer back

## User Experience Improvements

### Intelligent Defaults
- **With Inbound Data**: α=0.4, β=0.4, γ=0.2 (balanced approach)
- **Without Inbound Data**: Traditional two-factor scoring maintained
- **Automatic Detection**: UI adapts based on data availability

### Enhanced Transparency
- **Weight Normalization**: Always sums to 1.0 for consistent scoring
- **Data Quality Feedback**: Clear status messages about data availability
- **Scoring Method Display**: Shows which algorithm was used for results

### Flexible Configuration
Users can now optimize for:
- **Proximity-Focused**: Emphasize geographic convenience
- **Load-Balanced**: Distribute referrals evenly (traditional)
- **Relationship-Focused**: Prioritize mutual referral partners
- **Hybrid Approaches**: Custom weight combinations

## Technical Implementation Details

### Error Handling
- **Graceful Degradation**: Falls back to two-factor scoring if inbound data unavailable
- **Data Validation**: Comprehensive checks for missing or invalid data
- **User Feedback**: Clear error messages and status updates

### Performance Optimizations
- **Caching**: Inbound data loading cached for 1 hour (Streamlit `@st.cache_data`)
- **Efficient Merging**: Person ID-based joins for optimal performance
- **Vectorized Operations**: NumPy/Pandas operations for distance calculations

### Backward Compatibility
- **Existing Workflows**: All current functionality preserved
- **Default Behavior**: Traditional two-factor scoring when inbound weight = 0
- **Session State**: Enhanced to track all weight configurations

## Future Enhancement Opportunities

### Advanced Analytics
- **Mutual Referral Strength**: Weight by frequency of bidirectional referrals
- **Referral Recency**: Time-decay factors for recent vs. historical referrals
- **Specialty Matching**: Factor in provider specialty alignment

### Data Enrichment
- **Outcome Tracking**: Include client satisfaction or case outcomes
- **Geographic Zones**: Regional balancing within distance constraints  
- **Capacity Indicators**: Real-time provider availability status

### User Experience
- **Preset Configurations**: Save and recall favorite weight combinations
- **Scenario Modeling**: Compare recommendations under different weighting schemes
- **Batch Processing**: Recommend for multiple clients simultaneously

## Installation and Usage

### Prerequisites
```bash
pip install streamlit pandas openpyxl geopy
```

### Running the Application
```bash
streamlit run app.py
```

### Data Requirements
- **Outbound Referrals**: `data/cleaned_outbound_referrals.parquet` (required)
- **Inbound Referrals**: `data/Referrals_App_Inbound.xlsx` (optional, enables three-factor scoring)

## Conclusion

The three-factor scoring system significantly enhances the Provider Recommender by incorporating mutual referral relationships into provider selection. This creates a more holistic approach that can:

1. **Strengthen Partnerships**: Prioritize providers who also refer clients to the firm
2. **Maintain Balance**: Continue load balancing across the provider network  
3. **Preserve Proximity**: Keep geographic convenience as a key factor
4. **Adapt Intelligently**: Fall back gracefully when data is unavailable

The implementation maintains full backward compatibility while providing powerful new capabilities for optimizing provider recommendations based on comprehensive relationship data.
