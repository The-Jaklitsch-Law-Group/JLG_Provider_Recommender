@echo off
REM JLG Provider Recommender - Data Refresh Script (Windows)
REM This script updates the cleaned data files when source data changes

echo 🔄 JLG Provider Recommender - Data Refresh
echo ==========================================

REM Check if we're in the right directory
if not exist "src\data\preparation.py" (
    echo ❌ Error: Run this script from the project root directory
    exit /b 1
)

REM Check for source data files
echo 📂 Checking source data files...
if not exist "data\Referrals_App_Inbound.xlsx" (
    echo ❌ Error: Inbound referrals Excel file not found
    exit /b 1
)

if not exist "data\Referrals_App_Outbound.xlsx" if not exist "data\Referrals_App_Outbound.parquet" (
    echo ❌ Error: Outbound referrals data file not found
    exit /b 1
)

echo ✅ Source data files found

REM Backup existing cleaned files if they exist
if exist "data\cleaned_inbound_referrals.parquet" (
    echo 💾 Backing up existing cleaned files...
    if not exist "data\backups" mkdir "data\backups"

    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set timestamp=%datetime:~0,8%_%datetime:~8,6%

    if exist "data\cleaned_inbound_referrals.parquet" (
        copy "data\cleaned_inbound_referrals.parquet" "data\backups\cleaned_inbound_referrals_%timestamp%.parquet" >nul
    )

    if exist "data\cleaned_outbound_referrals.parquet" (
        copy "data\cleaned_outbound_referrals.parquet" "data\backups\cleaned_outbound_referrals_%timestamp%.parquet" >nul
    )

    echo ✅ Backup completed to data\backups\
)

REM Run data preparation
echo 🚀 Running data preparation...

REM Try to find Python executable
where python >nul 2>&1
if %errorlevel% == 0 (
    python src\data\preparation.py
) else (
    where python3 >nul 2>&1
    if %errorlevel% == 0 (
        python3 src\data\preparation.py
    ) else (
        REM Try virtual environment
        if exist ".venv\Scripts\python.exe" (
            .venv\Scripts\python.exe src\data\preparation.py
        ) else (
            echo ❌ Error: Python not found in PATH or virtual environment
            exit /b 1
        )
    )
)

REM Check if preparation was successful
if %errorlevel% == 0 (
    echo.
    echo ✅ Data preparation completed successfully!
    echo.
    echo 📊 File Summary:
    echo ----------------------------------------
    if exist "data\cleaned_*.parquet" (
        dir "data\cleaned_*.parquet" /B
    ) else (
        echo ❌ No cleaned files found
    )
    echo.
    echo 📋 Report available at: data\data_preparation_report.txt
    echo 📝 Detailed log at: data\data_preparation.log
    echo.
    echo 🎉 Ready to use! The application will automatically use the optimized data.
) else (
    echo ❌ Data preparation failed. Check the error messages above.
    exit /b 1
)

pause
