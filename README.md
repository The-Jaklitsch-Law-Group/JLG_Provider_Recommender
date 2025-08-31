# Provider Recommender for New Clients

---

## Contact
**Ben McCarty**  
*Data Operations Specialist*  
Jaklitsch Law Group  
Email: [benjamin@jaklitschlawgroup.com](mailto:benjamin@jaklitschlawgroup.com)

---

## Executive Summary
The Provider Recommender is a web-based tool designed to help personal injury law firm staff quickly and confidently recommend the best healthcare provider for new clients. By blending provider quality (rank) and proximity (distance), the app ensures that clients are matched with trusted, convenient providers—streamlining the referral process and supporting better client outcomes. The application is intuitive and accessible for all users, regardless of technical background.

---

## Key Features & Results
- **Guided, User-Friendly Workflow:** Enter a client address, select a specialty (optional), and choose the balance between provider quality and proximity.
- **Time-Based Filtering:** Calculate referral counts for specific time periods to support seasonal analysis and recent activity monitoring.
- **Advanced Input Validation:** Real-time address validation with helpful suggestions and error prevention.
- **Enhanced Error Handling:** User-friendly error messages for geocoding and data issues with specific guidance.
- **Comprehensive Algorithm Explanation:** Interactive tab explaining the scoring methodology and selection criteria.
- **Data Quality Dashboard:** Built-in monitoring for provider data completeness, geographic coverage, and system health.
- **Branded, Professional Interface:** Firm logo and name are prominently displayed for trust and consistency.
- **Clear, Actionable Recommendations:** The app highlights the top recommended provider, including name, address (with Google Maps link), phone, email, and specialty.
- **Preferred Provider Priority:** The system always prioritizes the law firm's preferred providers.
- **Top 5 Comparison:** Users can review the top 5 providers by blended score for transparency.
- **Export Option:** Download recommendations as a Word document for easy sharing with clients.
- **Accessible UI:** Designed for non-technical users, with clear instructions, an address validation warning, and a slider that shows the selected weighting value.
- **Performance Optimizations:** Distance calculations use NumPy vectorization and caching to deliver results quickly.
- **Comprehensive Testing Suite:** Unit and integration tests ensure reliability and catch regressions.

---

## How It Works
1. **Input:** Staff enter the client's address and optionally select a provider specialty.
2. **Weight Selection:** Users choose how much to prioritize provider quality (rank) versus proximity (distance) using a simple slider.
3. **Geocoding:** The app converts addresses to geographic coordinates using OpenStreetMap (Nominatim).
4. **Distance Calculation:** The system calculates the distance from the client to each provider.
5. **Scoring:** Each provider receives a blended score based on normalized rank and distance, weighted by user preference. Preferred providers are always prioritized.
6. **Recommendation:** The provider with the lowest blended score is recommended. The top 5 are also displayed for comparison.
7. **Export:** Users can export the recommendation as a Word document.

### Workflow Diagram

```
+-------------------------------+
| 1. User enters client address |
|    & selects specialty        |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 2. User sets quality vs.      |
|    proximity weight           |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 3. App geocodes client        |
|    address                    |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 4. App calculates distance    |
|    to each provider           |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 5. App blends provider rank   |
|    & distance using weights   |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 6. Preferred providers        |
|    prioritized                |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 7. Best provider recommended  |
|    (lowest score)             |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 8. Top 5 providers displayed  |
+---------------+---------------+
                |
                v
+---------------+---------------+
| 9. User exports recommendation|
|    as Word                    |
+-------------------------------+
```

*Workflow: From user input to provider recommendation and export.*

---

## Future Work
- **API Integration with Lead Docket:**  
  Implement API calls to retrieve and update provider and client data directly from Lead Docket, ensuring real-time accuracy and reducing manual data entry.
- **Dynamic Provider Ranking:**  
  Develop logic to determine provider rank programmatically using more detailed source data (e.g., client outcomes, feedback, referral volume, or other performance metrics) for a more objective and up-to-date ranking system.
- **Enhanced Data Validation:**  
  Add more robust validation and error handling for user input and provider data to further reduce the risk of incorrect recommendations.
- **Mobile Optimization:**  
  Further optimize the UI for mobile and tablet users.
- **Customizable Export Templates:**  
  Allow users to customize the format and content of exported Word/PDF documents.
- **Automated Testing & CI:**  
  Integrate automated testing and continuous integration to ensure code quality and reliability.

---

## For Developers
### Technology Stack
- **Frontend/UI:** [Streamlit](https://streamlit.io/)
- **Data Handling:** [pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Geocoding & Distance:** [geopy](https://geopy.readthedocs.io/)
- **Visualization:** [Plotly](https://plotly.com/python/) for interactive charts and maps
- **Document Export:** [python-docx](https://python-docx.readthedocs.io/)
- **Testing:** [pytest](https://pytest.org/) with coverage and mocking
- **Package Management:** [uv](https://github.com/astral-sh/uv) for fast, modern Python dependency management
- **Environment:** Python 3.11+ with virtual environment management via uv

### Quick Setup with uv (Recommended)

#### Prerequisites
First, install uv if you haven't already:

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

#### Automated Setup
Run the setup script for your platform:

**On Windows:**
```bash
# In Git Bash or WSL
./setup.sh
# Or in Command Prompt/PowerShell
setup.bat
```

**On macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

#### Manual Setup
If you prefer manual setup:

1. **Create and activate virtual environment:**
   ```bash
   uv venv --python 3.11
   source .venv/bin/activate  # On macOS/Linux
   # OR
   .venv\Scripts\activate     # On Windows
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -e .
   uv pip install -e ".[dev]"  # For development dependencies
   ```

### Running the Application

#### Using uv (Recommended)
```bash
# Run main application
uv run streamlit run app.py

# Run data quality dashboard
uv run streamlit run data_dashboard.py

# Run tests
uv run python run_tests.py

# Run tests with coverage
uv run pytest --cov=. --cov-report=html

# Quick test validation
uv run python run_tests.py --quick
```

#### Traditional Method
```bash
# Activate virtual environment first
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows

# Then run commands
streamlit run app.py
streamlit run data_dashboard.py
python run_tests.py
```

### Access the Application
Open your browser to the URL provided by Streamlit (typically `http://localhost:8501`)

### Data & Customization
- **Provider Data:** Loaded from `data/cleaned_outbound_referrals.parquet`. Update this file as your provider list changes.
- **Time-Based Data:** Detailed referral records in `data/detailed_referrals.parquet` enable time-period filtering.
- **Data Quality:** Monitor data completeness and quality using the built-in dashboard or standalone `data_dashboard.py`.
- **Testing:** Run `uv run python run_tests.py` to validate core functionality and data processing logic.
- **Branding:** Place your logo (`jlg_logo.svg`) in the project root. Adjust firm name and colors in the app script as needed.
- **Fonts & Styles:** Further customize the look and feel via CSS injected in the Streamlit script.
- **API Integrations:** Add credentials to `.streamlit/secrets.toml` for secure API access.
- **Reproducibility:** The app uses a fixed random seed for any placeholder data, ensuring consistent recommendations.

### Development Workflow
- **Environment Management:** Use `uv` for fast, reliable dependency installation and updates
- **Code Quality:** Pre-configured with black (formatting), flake8 (linting), and mypy (type checking)
- **Testing:** Comprehensive test suite with coverage reporting via pytest
- **Project Configuration:** Modern `pyproject.toml` setup with all tool configurations

### Best Practices & Suggestions
- **Documentation:** Maintain up-to-date docstrings and inline comments for maintainability.
- **Testing:** Use the comprehensive test suite (`uv run python run_tests.py`) to validate changes and catch regressions.
- **Data Quality:** Regularly monitor the data quality dashboard to ensure accurate recommendations.
- **Input Validation:** The app includes robust address validation - review error messages for data quality insights.
- **Security:** Use Streamlit secrets for API keys and sensitive data. Consider user authentication for sensitive workflows.
- **Accessibility:** Regularly review UI for clarity and usability, especially for non-technical users.
- **Performance:** Monitor the time-based filtering performance with large datasets and adjust caching as needed.
- **Dependencies:** Use `uv add package-name` to add new dependencies and `uv lock` to update the lock file.

---