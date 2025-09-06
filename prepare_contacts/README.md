# Unified Referral Data Cleaning Workflow

This directory contains the consolidated data cleaning and preparation workflow for JLG Provider Recommender referral data.

## Overview

The unified workflow processes both inbound and outbound referral datasets into a single, comprehensive parquet file that can be used for analysis, visualization, and machine learning applications.

## Files

### Core Scripts

- **`unified_referral_cleaning.py`** - Main cleaning script that processes both datasets
- **`analyze_unified_data.py`** - Example analysis script demonstrating data usage

### Legacy Scripts (Deprecated)

- **`clean_outbound_referrals.py`** - Original outbound-only cleaning script
- **`excel_to_parquet.py`** - Original Excel conversion script
- **`contact_cleaning.ipynb`** - Original notebook-based cleaning workflow

## Data Flow

```
Raw Data (Excel files)
├── data/raw/Referrals_App_Inbound.xlsx
└── data/raw/Referrals_App_Outbound.xlsx
          ↓
    Unified Cleaning Script
    (unified_referral_cleaning.py)
          ↓
Processed Data (Parquet files)
├── data/processed/unified_referrals.parquet (aggregated by provider)
├── data/processed/unified_referrals_detailed.parquet (individual referrals)
└── data/processed/provider_summary.xlsx (human-readable summary)
```

## Usage

### 1. Run the Unified Cleaning Script

```bash
python prepare_contacts/unified_referral_cleaning.py
```

This script:
- Reads both inbound and outbound Excel files
- Standardizes column names and data types
- Cleans and validates data (handles invalid coordinates, dates, etc.)
- Combines primary and secondary referrers from inbound data
- Aggregates referrals by provider
- Outputs unified parquet files

### 2. Analyze the Results

```bash
python prepare_contacts/analyze_unified_data.py
```

This script demonstrates:
- Loading the unified dataset
- Basic referral pattern analysis
- Geographic distribution analysis
- Time-based trending
- Bidirectional relationship identification
- Excel export for stakeholder review

## Output Files

### `unified_referrals.parquet` (Aggregated Data)

**Purpose**: Provider-level aggregated referral counts
**Structure**: One row per unique provider
**Columns**:
- `Person ID` - Unique provider identifier
- `Full Name` - Provider name (standardized)
- `Street`, `City`, `State`, `Zip` - Address components (standardized)
- `Latitude`, `Longitude` - Geocoordinates (cleaned)
- `Phone Number` - Contact phone (outbound data only)
- `Referral Count` - Total number of referrals for this provider
- `Referral Type` - "Inbound" (to JLG) or "Outbound" (from JLG)
- `Description` - Human-readable explanation of referral direction
- `Full Address` - Concatenated address for display

### `unified_referrals_detailed.parquet` (Individual Referrals)

**Purpose**: Individual referral records with timestamps
**Structure**: One row per referral transaction
**Columns**: Same as aggregated, plus:
- `Project ID` - Individual case identifier
- `Referral Date` - When the referral occurred

## Data Quality Features

### Text Standardization
- Provider names: Title case, trimmed whitespace
- Cities: Title case, trimmed whitespace
- States: Uppercase, trimmed whitespace
- Addresses: Consistent formatting

### Data Validation
- Invalid coordinates converted to NaN
- Date parsing with error handling
- Missing Person ID records filtered out
- Duplicate handling in aggregation

### Data Enrichment
- Unified referral date using fallback hierarchy (Create Date → Date of Intake)
- Full address concatenation for display
- Referral type classification (Inbound/Outbound)
- Descriptive labels for business users

## Key Insights from Unified Data

The unified dataset enables analysis of:

1. **Bidirectional Relationships**: Providers that both send and receive referrals
2. **Top Referral Sources**: Providers that most frequently refer cases to JLG
3. **Top Referral Targets**: Providers that JLG most frequently refers cases to
4. **Geographic Patterns**: Distribution of referral networks by location
5. **Temporal Trends**: Referral volume changes over time
6. **Network Analysis**: Complete view of JLG's referral ecosystem

## Migration from Legacy Workflow

If you were previously using the separate cleaning scripts:

1. **Replace** calls to `clean_outbound_referrals.py` with `unified_referral_cleaning.py`
2. **Update** data loading code to use `unified_referrals.parquet`
3. **Modify** analysis code to handle the `Referral Type` column for filtering
4. **Benefit** from the combined dataset for cross-referral analysis

## Example Analysis Snippets

```python
import pandas as pd

# Load unified data
df = pd.read_parquet('data/processed/unified_referrals.parquet')

# Find top inbound referral sources
inbound = df[df['Referral Type'] == 'Inbound']
top_sources = inbound.nlargest(10, 'Referral Count')

# Find bidirectional relationships
providers = df.groupby(['Full Name', 'City', 'State'])['Referral Type'].nunique()
bidirectional = providers[providers > 1]

# Geographic analysis
state_distribution = df.groupby(['State', 'Referral Type'])['Referral Count'].sum()
```

## Performance Notes

- Parquet format provides fast loading and small file sizes
- Unified structure reduces data pipeline complexity
- Aggregated and detailed views support different analysis needs
- Clean data types enable efficient downstream processing

## Future Enhancements

Potential improvements to consider:

- **Provider Matching**: More sophisticated duplicate detection across datasets
- **Geocoding**: Enhanced address standardization and coordinate validation
- **Categorization**: Provider type classification (chiropractor, physician, etc.)
- **Network Analysis**: Graph-based relationship modeling
- **Time Series**: Rolling aggregations and trend analysis
- **Data Quality Metrics**: Automated validation reporting
