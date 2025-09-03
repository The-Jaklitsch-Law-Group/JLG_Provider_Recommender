@echo off
REM Run the JLG Provider Recommender Streamlit App
echo Starting JLG Provider Recommender...
echo.

REM Navigate to the project directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment and run the app
echo ✅ Virtual environment found
echo 🚀 Starting Streamlit app...
echo.
echo The app will open in your browser at: http://localhost:8501
echo Press Ctrl+C to stop the app
echo.

.venv\Scripts\streamlit run app.py

echo.
echo App stopped.
pause
