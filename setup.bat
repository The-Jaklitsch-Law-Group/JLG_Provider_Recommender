@echo off
REM Setup script for JLG Provider Recommender using uv (Windows batch version)
REM This script sets up the development environment using uv for fast, reliable dependency management

echo 🚀 Setting up JLG Provider Recommender with uv
echo ================================================

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo ❌ uv is not installed. Please install it first:
    echo.
    echo On Windows ^(PowerShell^):
    echo powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo Or via pip:
    echo pip install uv
    echo.
    exit /b 1
)

for /f "tokens=*" %%i in ('uv --version') do set UV_VERSION=%%i
echo ✅ uv is installed: %UV_VERSION%

REM Create virtual environment
echo.
echo 🔧 Creating virtual environment...
uv venv --python 3.11

REM Install dependencies
echo.
echo 📦 Installing dependencies...
uv pip install -e .

echo 📚 Installing development dependencies...
uv pip install -e ".[dev]"

echo.
echo 🧪 Running setup validation...

REM Quick validation
uv run python -c "import streamlit, pandas, numpy, geopy; print('✅ Core dependencies imported successfully')"
if errorlevel 1 (
    echo ❌ Environment setup failed - dependency issues
    exit /b 1
)

echo ✅ Environment setup successful!

echo.
echo 🎉 Setup complete! Your development environment is ready.
echo.
echo To activate the virtual environment:
echo   .venv\Scripts\activate
echo.
echo Or use uv to run commands directly:
echo   uv run streamlit run app.py
echo   uv run python run_tests.py
echo   uv run streamlit run data_dashboard.py
echo.
echo Next steps:
echo 1. Activate the environment
echo 2. Run: streamlit run app.py
echo 3. Open your browser to the provided URL
echo.
echo For development:
echo - Run tests: uv run python run_tests.py
echo - Format code: uv run black .
echo - Type check: uv run mypy .
echo - Lint code: uv run flake8 .
