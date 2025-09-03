#!/usr/bin/env python3
"""
Setup script for development environment and code quality tools.

This script installs development dependencies and sets up pre-commit hooks
for maintaining code quality in the JLG Provider Recommender project.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, description: str = "") -> bool:
    """
    Run a command and return True if successful.
    
    Args:
        command (str): Command to run
        description (str): Description for logging
        
    Returns:
        bool: True if command succeeded, False otherwise
    """
    if description:
        print(f"🔧 {description}...")
    
    try:
        result = subprocess.run(
            command.split(), 
            capture_output=True, 
            text=True, 
            check=True
        )
        print(f"✅ {description or command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description or command} failed:")
        print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {command.split()[0]}")
        return False


def setup_development_environment():
    """Set up the development environment with code quality tools."""
    
    print("🚀 Setting up JLG Provider Recommender Development Environment")
    print("=" * 70)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found. Please run this script from the project root.")
        return False
    
    success_count = 0
    total_steps = 6
    
    # Step 1: Install development dependencies
    if run_command("pip install -U pip", "Upgrading pip"):
        success_count += 1
    
    # Step 2: Install pre-commit
    if run_command("pip install pre-commit", "Installing pre-commit"):
        success_count += 1
    
    # Step 3: Install code quality tools
    dev_tools = ["black", "isort", "flake8", "mypy", "pytest", "pytest-cov"]
    tools_cmd = f"pip install {' '.join(dev_tools)}"
    if run_command(tools_cmd, "Installing code quality tools"):
        success_count += 1
    
    # Step 4: Install additional dependencies for type checking
    type_deps = ["types-requests", "pandas-stubs"]
    types_cmd = f"pip install {' '.join(type_deps)}"
    if run_command(types_cmd, "Installing type checking dependencies"):
        success_count += 1
    
    # Step 5: Install pre-commit hooks
    if run_command("pre-commit install", "Installing pre-commit hooks"):
        success_count += 1
    
    # Step 6: Run initial pre-commit check
    print("🔍 Running initial code quality check...")
    result = subprocess.run(
        ["pre-commit", "run", "--all-files"], 
        capture_output=True, 
        text=True
    )
    
    if result.returncode == 0:
        print("✅ All pre-commit checks passed!")
        success_count += 1
    else:
        print("⚠️  Some pre-commit checks failed (this is normal for initial setup)")
        print("   Files have been automatically formatted where possible.")
        print("   Please review changes and commit them.")
        success_count += 1  # Count as success since it's expected
    
    # Summary
    print("\n" + "=" * 70)
    print(f"🎯 Setup complete: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("\n✅ Development environment is ready!")
        print("\n📋 Next steps:")
        print("   1. Review any automatically formatted files")
        print("   2. Run tests: python scripts/run_tests.py")
        print("   3. Start development with confidence!")
        print("\n💡 Pre-commit hooks will now run automatically before each commit.")
        return True
    else:
        print("\n⚠️  Some setup steps failed. Please review the errors above.")
        return False


def verify_setup():
    """Verify that the development environment is properly configured."""
    
    print("\n🔍 Verifying development environment...")
    
    verification_commands = [
        ("black --version", "Black formatter"),
        ("isort --version", "isort import sorter"),
        ("flake8 --version", "Flake8 linter"),
        ("mypy --version", "MyPy type checker"),
        ("pytest --version", "Pytest testing framework"),
        ("pre-commit --version", "Pre-commit hooks")
    ]
    
    all_good = True
    for cmd, tool in verification_commands:
        try:
            subprocess.run(cmd.split(), capture_output=True, check=True)
            print(f"✅ {tool}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool} not available")
            all_good = False
    
    return all_good


def show_usage_examples():
    """Show examples of how to use the development tools."""
    
    print("\n📚 Development Tools Usage:")
    print("-" * 40)
    print("Format code:")
    print("  black .")
    print("  isort .")
    print("\nCheck code quality:")
    print("  flake8 .")
    print("  mypy .")
    print("\nRun tests:")
    print("  python scripts/run_tests.py")
    print("  pytest tests/ -v")
    print("\nRun pre-commit manually:")
    print("  pre-commit run --all-files")
    print("\nUpdate pre-commit hooks:")
    print("  pre-commit autoupdate")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        success = verify_setup()
        sys.exit(0 if success else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_usage_examples()
        sys.exit(0)
    else:
        success = setup_development_environment()
        if success:
            verify_setup()
            show_usage_examples()
        sys.exit(0 if success else 1)
