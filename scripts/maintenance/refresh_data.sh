#!/bin/bash
# JLG Provider Recommender - Data Refresh Script
# This script updates the cleaned data files when source data changes

echo "🔄 JLG Provider Recommender - Data Refresh"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "src/data/preparation.py" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

# Check for source data files
echo "📂 Checking source data files..."
inbound_found=false
outbound_found=false

# Check for inbound data in multiple locations
if [ -f "data/raw/Referrals_App_Inbound.xlsx" ]; then
    inbound_found=true
    echo "✅ Found inbound data: data/raw/Referrals_App_Inbound.xlsx"
elif [ -f "data/Referrals_App_Inbound.xlsx" ]; then
    inbound_found=true
    echo "✅ Found inbound data: data/Referrals_App_Inbound.xlsx"
elif [ -f "data/processed/cleaned_inbound_referrals.parquet" ]; then
    inbound_found=true
    echo "✅ Found processed inbound data: data/processed/cleaned_inbound_referrals.parquet"
else
    echo "⚠️  Warning: No inbound referrals data found (will proceed with outbound only)"
fi

# Check for outbound data in multiple locations
if [ -f "data/raw/Referrals_App_Outbound.xlsx" ]; then
    outbound_found=true
    echo "✅ Found outbound data: data/raw/Referrals_App_Outbound.xlsx"
elif [ -f "data/Referrals_App_Outbound.xlsx" ]; then
    outbound_found=true
    echo "✅ Found outbound data: data/Referrals_App_Outbound.xlsx"
elif [ -f "data/processed/Referrals_App_Outbound.parquet" ]; then
    outbound_found=true
    echo "✅ Found outbound data: data/processed/Referrals_App_Outbound.parquet"
elif [ -f "data/Referrals_App_Outbound.parquet" ]; then
    outbound_found=true
    echo "✅ Found outbound data: data/Referrals_App_Outbound.parquet"
else
    echo "❌ Error: No outbound referrals data found"
    echo "   Expected locations:"
    echo "   - data/raw/Referrals_App_Outbound.xlsx"
    echo "   - data/Referrals_App_Outbound.xlsx" 
    echo "   - data/processed/Referrals_App_Outbound.parquet"
    echo "   - data/Referrals_App_Outbound.parquet"
    exit 1
fi

if [ "$outbound_found" = true ]; then
    echo "✅ Required data files found"
fi

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
echo "🚀 Running optimized data preparation..."
if command -v python &> /dev/null; then
    python src/data/preparation.py
elif command -v python3 &> /dev/null; then
    python3 src/data/preparation.py
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
    ls -lh data/cleaned_*.parquet 2>/dev/null || echo "❌ No cleaned files found in data/"
    ls -lh data/processed/cleaned_*.parquet 2>/dev/null || echo "❌ No cleaned files found in data/processed/"
    echo ""
    echo "📋 Report available at: data/logs/data_preparation_report.txt"
    echo "📝 Detailed log at: data/logs/data_preparation.log"
    echo ""
    echo "🎉 Ready to use! The application will automatically use the optimized data."
else
    echo "❌ Data preparation failed. Check the error messages above."
    exit 1
fi
