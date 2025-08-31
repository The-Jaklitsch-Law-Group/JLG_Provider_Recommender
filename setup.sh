#!/usr/bin/env bash
# Setup script for JLG Provider Recommender using uv
# This script sets up the development environment using uv for fast, reliable dependency management

set -e  # Exit on any error

echo "🚀 Setting up JLG Provider Recommender with uv"
echo "================================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo ""
    echo "On macOS/Linux:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "On Windows (PowerShell):"
    echo "powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\""
    echo ""
    echo "Or via pip:"
    echo "pip install uv"
    echo ""
    exit 1
fi

echo "✅ uv is installed: $(uv --version)"

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
uv venv --python 3.11

# Activate virtual environment (instructions vary by shell)
echo ""
echo "📦 Installing dependencies..."

# Install production dependencies
uv pip install -e .

# Install development dependencies
echo "📚 Installing development dependencies..."
uv pip install -e ".[dev]"

echo ""
echo "🧪 Running setup validation..."

# Quick validation
if uv run python -c "import streamlit, pandas, numpy, geopy; print('✅ Core dependencies imported successfully')"; then
    echo "✅ Environment setup successful!"
else
    echo "❌ Environment setup failed - dependency issues"
    exit 1
fi

echo ""
echo "🎉 Setup complete! Your development environment is ready."
echo ""
echo "To activate the virtual environment:"
echo "  source .venv/bin/activate  # On macOS/Linux"
echo "  .venv\\Scripts\\activate     # On Windows"
echo ""
echo "Or use uv to run commands directly:"
echo "  uv run streamlit run app.py"
echo "  uv run python run_tests.py"
echo "  uv run streamlit run data_dashboard.py"
echo ""
echo "Next steps:"
echo "1. Activate the environment"
echo "2. Run: streamlit run app.py"
echo "3. Open your browser to the provided URL"
echo ""
echo "For development:"
echo "- Run tests: uv run python run_tests.py"
echo "- Format code: uv run black ."
echo "- Type check: uv run mypy ."
echo "- Lint code: uv run flake8 ."
