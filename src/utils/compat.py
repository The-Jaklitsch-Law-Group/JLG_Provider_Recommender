"""Data path compatibility module for the reorganized structure."""

from pathlib import Path


# Update data file paths for the new structure
def get_data_file_path(filename: str, subfolder: str = "") -> Path:
    """Get the correct path for data files in the new structure."""
    repo_root = Path(__file__).parent.parent

    if subfolder:
        return repo_root / "data" / subfolder / filename
    else:
        # Try to determine the correct subfolder based on file type
        if filename.endswith(".xlsx"):
            return repo_root / "data" / "raw" / filename
        elif filename.endswith(".parquet"):
            return repo_root / "data" / "processed" / filename
        elif filename.endswith((".log", ".txt")):
            return repo_root / "data" / "logs" / filename
        else:
            return repo_root / "data" / filename


def update_data_paths():
    """Update data file paths in existing modules that haven't been moved."""
    pass
