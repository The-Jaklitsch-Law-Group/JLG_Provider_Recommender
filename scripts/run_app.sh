#!/bin/bash
# Run the JLG Provider Recommender Streamlit App

echo "🏥 Starting JLG Provider Recommender..."
echo

# Navigate to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -f ".venv/bin/activate" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

echo "✅ Virtual environment found"
echo "🚀 Starting Streamlit app..."
echo
echo "The app will open in your browser at: http://localhost:8501"
echo "Press Ctrl+C to stop the app"
echo

# Activate virtual environment and run the app
source .venv/bin/activate
streamlit run app.py

echo
echo "App stopped."
