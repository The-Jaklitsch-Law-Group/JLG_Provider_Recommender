#!/bin/bash

# Unified Referral Data Cleaning Script
# This script runs the unified cleaning process for JLG referral data

echo "=== JLG Unified Referral Data Cleaning ==="
echo "Starting unified data cleaning process..."
echo

# Change to project directory
cd "$(dirname "$0")/.."

# Run the unified cleaning script
echo "Step 1: Running unified referral cleaning..."
python prepare_contacts/unified_referral_cleaning.py

if [ $? -eq 0 ]; then
    echo "✅ Unified cleaning completed successfully"
    echo

    echo "Step 2: Running data analysis..."
    python prepare_contacts/analyze_unified_data.py

    if [ $? -eq 0 ]; then
        echo "✅ Analysis completed successfully"
        echo
        echo "=== PROCESS COMPLETE ==="
        echo "Output files created:"
        echo "  - data/processed/unified_referrals.parquet (aggregated data)"
        echo "  - data/processed/unified_referrals_detailed.parquet (detailed data)"
        echo "  - data/processed/provider_summary.xlsx (Excel summary)"
        echo
        echo "Ready for use in your applications!"
    else
        echo "❌ Analysis failed"
        exit 1
    fi
else
    echo "❌ Cleaning failed"
    exit 1
fi
