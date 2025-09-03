#!/usr/bin/env python3
"""Test runner script for the Provider Recommender application."""

import os
import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run all tests with coverage reporting."""

    # Get the project root directory (parent of scripts directory)
    project_root = Path(__file__).parent.parent.absolute()

    # Change to project directory
    os.chdir(project_root)

    print("🧪 Running Provider Recommender Tests")
    print("=" * 50)

    # Check if pytest is available
    try:
        import pytest
        import pytest_cov

        print("✅ pytest and pytest-cov are available")
    except ImportError as e:
        print(f"❌ Missing test dependencies: {e}")
        print("Install with: pip install -r requirements.txt")
        return 1

    # Run tests with coverage
    test_commands = [
        # Run unit tests
        [
            "python",
            "-m",
            "pytest",
            "tests/test_provider_utils.py",
            "-v",
            "--tb=short",
            "--cov=provider_utils",
            "--cov-report=term-missing",
        ],
        # Run integration tests
        ["python", "-m", "pytest", "tests/test_integration.py", "-v", "--tb=short"],
    ]

    all_passed = True

    for i, cmd in enumerate(test_commands, 1):
        print(f"\n🔄 Running test suite {i}/{len(test_commands)}")
        print(f"Command: {' '.join(cmd)}")
        print("-" * 40)

        try:
            result = subprocess.run(cmd, check=True, capture_output=False)
            print(f"✅ Test suite {i} passed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Test suite {i} failed with exit code {e.returncode}")
            all_passed = False
        except FileNotFoundError:
            print(f"❌ Could not run pytest. Make sure it's installed.")
            all_passed = False

    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed. Check output above.")
        return 1


def run_quick_validation():
    """Run a quick validation of core functions without full test suite."""

    print("🔍 Running quick validation...")

    try:
        # Test imports
        from provider_utils import calculate_distances, recommend_provider, sanitize_filename, validate_address_input

        print("✅ Core imports successful")

        # Test basic functions
        assert sanitize_filename("Test Name") == "Test_Name"
        print("✅ sanitize_filename works")

        valid, msg = validate_address_input("123 Main St", "Baltimore", "MD", "21201")
        assert valid == True
        print("✅ validate_address_input works")

        # Test with sample data
        import numpy as np
        import pandas as pd

        sample_df = pd.DataFrame(
            {
                "Full Name": ["Dr. Test"],
                "Distance (Miles)": [5.0],
                "Referral Count": [10],
                "Latitude": [39.29],
                "Longitude": [-76.61],
            }
        )

        best, scored = recommend_provider(sample_df)
        assert best is not None
        print("✅ recommend_provider works")

        print("🎉 Quick validation passed!")
        return True

    except Exception as e:
        print(f"❌ Quick validation failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = run_quick_validation()
        sys.exit(0 if success else 1)
    else:
        sys.exit(run_tests())
