#!/usr/bin/env python3
"""
Repository Reorganization Script for JLG Provider Recommender

This script safely reorganizes the repository structure to improve organization
and maintainability while preserving all functionality.

Usage:
    python scripts/reorganize_repository.py [--dry-run]
"""

import argparse
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class RepositoryReorganizer:
    """Handles the safe reorganization of the repository structure."""

    def __init__(self, root_path: Path, dry_run: bool = False):
        self.root_path = root_path
        self.dry_run = dry_run
        self.moves_performed: List[Tuple[str, str]] = []

    def move_file(self, source: str, destination: str) -> bool:
        """Move a file from source to destination, creating directories as needed."""
        source_path = self.root_path / source
        dest_path = self.root_path / destination

        if not source_path.exists():
            logger.warning(f"Source file does not exist: {source_path}")
            return False

        # Create destination directory if it doesn't exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            logger.info(f"DRY RUN: Would move {source_path} -> {dest_path}")
        else:
            try:
                shutil.move(str(source_path), str(dest_path))
                logger.info(f"Moved: {source_path} -> {dest_path}")
                self.moves_performed.append((source, destination))
            except Exception as e:
                logger.error(f"Failed to move {source_path} -> {dest_path}: {e}")
                return False

        return True

    def copy_file(self, source: str, destination: str) -> bool:
        """Copy a file from source to destination."""
        source_path = self.root_path / source
        dest_path = self.root_path / destination

        if not source_path.exists():
            logger.warning(f"Source file does not exist: {source_path}")
            return False

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if self.dry_run:
            logger.info(f"DRY RUN: Would copy {source_path} -> {dest_path}")
        else:
            try:
                shutil.copy2(str(source_path), str(dest_path))
                logger.info(f"Copied: {source_path} -> {dest_path}")
            except Exception as e:
                logger.error(f"Failed to copy {source_path} -> {dest_path}: {e}")
                return False

        return True

    def reorganize_utilities(self):
        """Move utility files to src/utils/"""
        logger.info("Reorganizing utility modules...")

        # Move provider_utils.py -> src/utils/providers.py
        self.move_file("provider_utils.py", "src/utils/providers.py")

        # Move performance_utils.py -> src/utils/performance.py
        self.move_file("performance_utils.py", "src/utils/performance.py")

        # Move security_utils.py -> src/utils/security.py
        self.move_file("security_utils.py", "src/utils/security.py")

        # Move workflow_validation.py -> src/utils/validation.py
        self.move_file("workflow_validation.py", "src/utils/validation.py")

        # Create __init__.py for utils package
        self.create_init_file("src/utils/__init__.py")

    def reorganize_data_modules(self):
        """Move data processing files to src/data/"""
        logger.info("Reorganizing data processing modules...")

        # Move data_ingestion.py -> src/data/ingestion.py
        self.move_file("data_ingestion.py", "src/data/ingestion.py")

        # Choose the optimized version and rename it to preparation.py
        self.move_file("optimized_data_preparation.py", "src/data/preparation.py")

        # Move performance_benchmark.py -> src/data/benchmark.py (related to data processing)
        self.move_file("performance_benchmark.py", "src/data/benchmark.py")

        # Create __init__.py for data package
        self.create_init_file("src/data/__init__.py")

    def reorganize_data_files(self):
        """Move data files to appropriate subdirectories."""
        logger.info("Reorganizing data files...")

        # Move Excel files to raw data
        for excel_file in ["Referrals_App_Inbound.xlsx", "Referrals_App_Outbound.xlsx"]:
            self.move_file(f"data/{excel_file}", f"data/raw/{excel_file}")

        # Move processed files to processed directory
        for processed_file in [
            "cleaned_inbound_referrals.parquet",
            "cleaned_outbound_referrals.parquet",
            "Referrals_App_Outbound.parquet",
        ]:
            self.move_file(f"data/{processed_file}", f"data/processed/{processed_file}")

        # Move log files to logs directory
        self.move_file("data/data_preparation_report.txt", "data/logs/data_preparation_report.txt")
        self.move_file("data_preparation.log", "data/logs/data_preparation.log")

    def reorganize_scripts(self):
        """Reorganize scripts by purpose."""
        logger.info("Reorganizing scripts...")

        # Setup scripts
        setup_scripts = ["setup.sh", "setup.bat", "setup_dev_environment.py"]
        for script in setup_scripts:
            self.move_file(f"scripts/{script}", f"scripts/setup/{script}")

        # Maintenance scripts
        maintenance_scripts = ["refresh_data.sh", "refresh_data.bat", "regenerate_data.py", "cleanup_check.py"]
        for script in maintenance_scripts:
            self.move_file(f"scripts/{script}", f"scripts/maintenance/{script}")

        # Testing scripts
        testing_scripts = ["run_tests.py", "validate_improvements.py"]
        for script in testing_scripts:
            self.move_file(f"scripts/{script}", f"scripts/testing/{script}")

    def reorganize_tests(self):
        """Reorganize test files."""
        logger.info("Reorganizing tests...")

        # Move existing tests to unit tests
        self.move_file("tests/test_provider_utils.py", "tests/unit/test_providers.py")
        self.move_file("tests/test_integration.py", "tests/integration/test_integration.py")

        # Create __init__.py files
        self.create_init_file("tests/__init__.py")
        self.create_init_file("tests/unit/__init__.py")
        self.create_init_file("tests/integration/__init__.py")
        self.create_init_file("tests/fixtures/__init__.py")

    def create_init_file(self, path: str):
        """Create an __init__.py file."""
        init_path = self.root_path / path

        if self.dry_run:
            logger.info(f"DRY RUN: Would create {init_path}")
        else:
            try:
                init_path.parent.mkdir(parents=True, exist_ok=True)
                with open(init_path, "w") as f:
                    f.write('"""Package initialization file."""\n')
                logger.info(f"Created: {init_path}")
            except Exception as e:
                logger.error(f"Failed to create {init_path}: {e}")

    def cleanup_old_files(self):
        """Remove old files that are no longer needed."""
        logger.info("Cleaning up old files...")

        # Remove the original data_preparation.py (keeping optimized version)
        old_file = self.root_path / "data_preparation.py"
        if old_file.exists() and not self.dry_run:
            try:
                old_file.unlink()
                logger.info(f"Removed old file: {old_file}")
            except Exception as e:
                logger.error(f"Failed to remove {old_file}: {e}")

    def create_src_init(self):
        """Create main src package __init__.py."""
        self.create_init_file("src/__init__.py")

    def run_reorganization(self):
        """Execute the complete reorganization."""
        logger.info(f"Starting repository reorganization (dry_run={self.dry_run})...")

        try:
            # Create main src package
            self.create_src_init()

            # Reorganize by category
            self.reorganize_utilities()
            self.reorganize_data_modules()
            self.reorganize_data_files()
            self.reorganize_scripts()
            self.reorganize_tests()

            # Cleanup
            if not self.dry_run:
                self.cleanup_old_files()

            logger.info("Repository reorganization completed successfully!")

            if self.moves_performed:
                logger.info(f"Files moved: {len(self.moves_performed)}")
                for source, dest in self.moves_performed:
                    logger.info(f"  {source} -> {dest}")

        except Exception as e:
            logger.error(f"Reorganization failed: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Reorganize JLG Provider Recommender repository")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    # Get repository root (assume script is in scripts/ subdirectory)
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent

    logger.info(f"Repository root: {repo_root}")

    reorganizer = RepositoryReorganizer(repo_root, dry_run=args.dry_run)
    reorganizer.run_reorganization()


if __name__ == "__main__":
    main()
