# JLG_Provider_Recommender

## How to Run the Streamlit App

1. **Activate the virtual environment** (if not already active):
   - On Windows (using Git Bash, Command Prompt, or PowerShell):
     ```bash
     source .venv/Scripts/activate
     ```
   - You should see your prompt change to show `(.venv)` at the beginning.

2. **Install dependencies** (if you haven't already):
   - This project uses [uv](https://github.com/astral-sh/uv) for fast Python dependency management.
   - To install all required packages:
     ```bash
     uv pip install pandas openpyxl streamlit geopy
     ```

3. **Run the Streamlit app**:
   ```bash
   streamlit run app.py
   ```

4. **Open the app in your browser**:
   - Streamlit will usually open a new tab automatically.
   - If not, look for a local URL in the terminal output (e.g., `http://localhost:8501`) and open it manually in your browser.

---

## What the App Does
- Lets users enter their address and recommends the best provider based on a blend of provider ranking and drive distance.
- Reads provider data from `data/Ranked_Contacts.xlsx`.
- Geocodes addresses using OpenStreetMap (Nominatim) via geopy.
- Calculates distances and blends with ranking for recommendations.
- Uses Streamlit's `session_state` to support multiple users and interactive workflows.

## Educational Notes
- **Streamlit** is a Python library for building interactive web apps easily. Any changes to `app.py` will automatically reload the app in your browser.
- **session_state** allows you to store variables across reruns, supporting multi-user and interactive workflows.
- **uv** is a fast Python package/dependency manager. It is used here to manage the virtual environment and dependencies efficiently.

---

## Troubleshooting
- If you see errors about missing packages, make sure your virtual environment is activated and run the `uv pip install ...` command above.
- If geocoding fails, check your address for typos or try a more complete address.
- If you have questions about the code, see the educational comments in `app.py` for explanations of each step.

