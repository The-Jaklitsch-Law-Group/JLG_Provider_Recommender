@echo off
REM Unified Referral Data Cleaning Script (Windows)
REM This script runs the unified cleaning process for JLG referral data

echo === JLG Unified Referral Data Cleaning ===
echo Starting unified data cleaning process...
echo.

REM Change to project directory
cd /d "%~dp0\.."

REM Run the unified cleaning script
echo Step 1: Running unified referral cleaning...
python prepare_contacts/unified_referral_cleaning.py

if %errorlevel% equ 0 (
    echo ✅ Unified cleaning completed successfully
    echo.

    echo Step 2: Running data analysis...
    python prepare_contacts/analyze_unified_data.py

    if %errorlevel% equ 0 (
        echo ✅ Analysis completed successfully
        echo.
        echo === PROCESS COMPLETE ===
        echo Output files created:
        echo   - data/processed/unified_referrals.parquet ^(aggregated data^)
        echo   - data/processed/unified_referrals_detailed.parquet ^(detailed data^)
        echo   - data/processed/provider_summary.xlsx ^(Excel summary^)
        echo.
        echo Ready for use in your applications!
    ) else (
        echo ❌ Analysis failed
        exit /b 1
    )
) else (
    echo ❌ Cleaning failed
    exit /b 1
)

pause
