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
- **Branded, Professional Interface:** Firm logo and name are prominently displayed for trust and consistency.
- **Clear, Actionable Recommendations:** The app highlights the top recommended provider, including name, address (with Google Maps link), phone, email, and specialty.
- **Preferred Provider Priority:** The system always prioritizes the law firm's preferred providers.
- **Top 5 Comparison:** Users can review the top 5 providers by blended score for transparency.
- **Export Options:** Download recommendations as Word or PDF documents for easy sharing with clients.
- **Accessible UI:** Designed for non-technical users, with clear instructions, tooltips, and a "Start New Search" button.

---

## How It Works
1. **Input:** Staff enter the client's address and optionally select a provider specialty.
2. **Weight Selection:** Users choose how much to prioritize provider quality (rank) versus proximity (distance) using a simple slider.
3. **Geocoding:** The app converts addresses to geographic coordinates using OpenStreetMap (Nominatim).
4. **Distance Calculation:** The system calculates the distance from the client to each provider.
5. **Scoring:** Each provider receives a blended score based on normalized rank and distance, weighted by user preference. Preferred providers are always prioritized.
6. **Recommendation:** The provider with the lowest blended score is recommended. The top 5 are also displayed for comparison.
7. **Export:** Users can export the recommendation as a Word or PDF document.

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
|    as Word/PDF                |
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
- **Data Handling:** [pandas](https://pandas.pydata.org/)
- **Geocoding & Distance:** [geopy](https://geopy.readthedocs.io/)
- **Document Export:** [python-docx](https://python-docx.readthedocs.io/), [reportlab](https://www.reportlab.com/)
- **Environment:** [uv](https://github.com/astral-sh/uv) for fast, reproducible Python environments

### Setup & Usage
1. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```
2. **Run the app:**
   ```bash
   streamlit run app_polished.py
   ```
3. **Access the app:**
   Open the provided local URL in your browser.

### Data & Customization
- **Provider Data:** Loaded from `data/Ranked_Contacts.xlsx`. Update this file as your provider list changes.
- **Branding:** Place your logo (`jlg_logo.svg`) in the project root. Adjust firm name and colors in the app script as needed.
- **Fonts & Styles:** Further customize the look and feel via CSS injected in the Streamlit script.
- **API Integrations:** Add credentials to `.streamlit/secrets.toml` for secure API access.
- **Reproducibility:** The app uses a fixed random seed for any placeholder data, ensuring consistent recommendations.

### Best Practices & Suggestions
- **Documentation:** Maintain up-to-date docstrings and inline comments for maintainability.
- **Testing:** Add unit and integration tests for core logic (e.g., scoring, geocoding, data loading).
- **Security:** Use Streamlit secrets for API keys and sensitive data. Consider user authentication for sensitive workflows.
- **Accessibility:** Regularly review UI for clarity and usability, especially for non-technical users.

---