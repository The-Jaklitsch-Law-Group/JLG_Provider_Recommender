#!/bin/bash
# JLG Provider Recommender - Data Refresh Script
# This script updates the cleaned data files when source data changes

echo "🔄 JLG Provider Recommender - Data Refresh"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "data_preparation.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Check for source data files
echo "📂 Checking source data files..."
if [ ! -f "data/Referrals_App_Inbound.xlsx" ]; then
    echo "❌ Error: Inbound referrals Excel file not found"
    exit 1
fi

if [ ! -f "data/Referrals_App_Outbound.xlsx" ] && [ ! -f "data/Referrals_App_Outbound.parquet" ]; then
    echo "❌ Error: Outbound referrals data file not found"
    exit 1
fi

echo "✅ Source data files found"

# Backup existing cleaned files if they exist
if [ -f "data/cleaned_inbound_referrals.parquet" ] || [ -f "data/processed/cleaned_outbound_referrals.parquet" ]; then
    echo "💾 Backing up existing cleaned files..."
    mkdir -p data/backups
    timestamp=$(date +"%Y%m%d_%H%M%S")

    if [ -f "data/cleaned_inbound_referrals.parquet" ]; then
        cp "data/cleaned_inbound_referrals.parquet" "data/backups/cleaned_inbound_referrals_${timestamp}.parquet"
    fi

    if [ -f "data/processed/cleaned_outbound_referrals.parquet" ]; then
        cp "data/processed/cleaned_outbound_referrals.parquet" "data/backups/cleaned_outbound_referrals_${timestamp}.parquet"
    fi

    echo "✅ Backup completed to data/backups/"
fi

# Run data preparation
echo "🚀 Running data preparation..."
if command -v python &> /dev/null; then
    python data_preparation.py
elif command -v python3 &> /dev/null; then
    python3 data_preparation.py
else
    echo "❌ Error: Python not found in PATH"
    exit 1
fi

# Check if preparation was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Data preparation completed successfully!"
    echo ""
    echo "📊 File Summary:"
    echo "----------------------------------------"
    ls -lh data/cleaned_*.parquet 2>/dev/null || echo "❌ No cleaned files found"
    echo ""
    echo "📋 Report available at: data/data_preparation_report.txt"
    echo "📝 Detailed log at: data/data_preparation.log"
    echo ""
    echo "🎉 Ready to use! The application will automatically use the optimized data."
else
    echo "❌ Data preparation failed. Check the error messages above."
    exit 1
fi
