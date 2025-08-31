# Migration Guide: Upgrading to uv Virtual Environment

This guide helps you migrate from traditional pip/venv setup to the new uv-based environment management.

## Why Migrate to uv?

- **Faster**: 10-100x faster than pip for dependency resolution and installation
- **More Reliable**: Better dependency resolution and conflict detection
- **Modern**: Built for Python 3.8+ with modern package management features
- **Consistent**: Lock files ensure reproducible environments across machines
- **Unified**: Single tool for virtual environments, dependency management, and project configuration

## Migration Steps

### 1. Backup Your Current Environment (Optional)

If you want to preserve your current environment:

```bash
# Export current requirements
pip freeze > requirements_backup.txt
```

### 2. Install uv

**On Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**On macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Or via pip:**
```bash
pip install uv
```

### 3. Remove Old Virtual Environment

```bash
# Deactivate current environment if active
deactivate

# Remove old virtual environment directory
rm -rf venv/  # or whatever your venv directory was named
```

### 4. Set Up New uv Environment

#### Option A: Automated Setup (Recommended)

**On Windows:**
```bash
./setup.bat
```

**On macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

#### Option B: Manual Setup

```bash
# Create new virtual environment with Python 3.11
uv venv --python 3.11

# Install project dependencies
uv pip install -e .

# Install development dependencies
uv pip install -e ".[dev]"
```

### 5. Verify Migration

```bash
# Test core functionality
uv run python -c "import streamlit, pandas, numpy, geopy; print('✅ Migration successful!')"

# Run tests to ensure everything works
uv run python run_tests.py
```

### 6. Update Your Workflow

#### Old Commands → New Commands

| Old Command | New uv Command |
|-------------|----------------|
| `source venv/bin/activate` | `source .venv/bin/activate` or use `uv run` |
| `pip install package` | `uv add package` |
| `pip install -r requirements.txt` | `uv pip install -e .` |
| `python app.py` | `uv run python app.py` |
| `streamlit run app.py` | `uv run streamlit run app.py` |
| `pytest` | `uv run pytest` |

#### New Features Available

- **Lock files**: `uv.lock` ensures exact dependency versions
- **Fast installs**: Dependencies install much faster
- **Better resolution**: Improved dependency conflict detection
- **Project mode**: `uv add/remove` for dependency management

## Troubleshooting

### Common Issues

**Q: "uv command not found"**
A: Restart your terminal after installation, or add uv to your PATH manually.

**Q: "Python version not found"**
A: Install Python 3.11+ or use `uv python install 3.11` to let uv manage Python versions.

**Q: "Dependencies not resolving"**
A: Try `uv pip install --upgrade-strategy eager -e .` to force updates.

**Q: "Import errors after migration"**
A: Ensure you're using `uv run` or have activated the new `.venv` environment.

### Getting Help

If you encounter issues:

1. Check that uv is properly installed: `uv --version`
2. Verify Python version: `uv run python --version`
3. Check virtual environment: `uv venv list`
4. Re-run setup script if needed
5. Compare with `requirements_backup.txt` if specific packages are missing

## Benefits You'll See

After migration, you'll experience:

- **Faster dependency installation** (especially on first setup)
- **More reliable builds** across different machines
- **Better error messages** when dependencies conflict
- **Simplified commands** with `uv run`
- **Modern project configuration** with `pyproject.toml`

## Rollback Plan

If you need to rollback to the old setup:

1. Create traditional virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install from backup: `pip install -r requirements_backup.txt`

However, we recommend sticking with uv for the improved performance and reliability!

## Next Steps

- Use `uv add package-name` to add new dependencies
- Run `uv lock` after adding dependencies to update the lock file
- Use `uv run command` for any Python commands
- Explore `uv --help` for more advanced features

Welcome to modern Python dependency management! 🚀
