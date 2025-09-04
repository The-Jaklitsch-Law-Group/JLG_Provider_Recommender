import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Geopy imports with error handling
try:
    from geopy.extra.rate_limiter import RateLimiter
    from geopy.geocoders import Nominatim

    GEOPY_AVAILABLE = True
except ImportError:
    st.error("geopy package is required. Please install it with: pip install geopy")
    GEOPY_AVAILABLE = False

from provider_utils import (  # Import new enhanced functions
    calculate_distances,
    calculate_time_based_referral_counts,
    geocode_address_with_cache,
    get_word_bytes,
    handle_streamlit_error,
    load_and_validate_provider_data,
    load_detailed_referrals,
    load_provider_data,
    recommend_provider,
    sanitize_filename,
    validate_address,
    validate_address_input,
    validate_and_clean_coordinates,
    validate_provider_data,
)

# --- Helper Functions ---


# --- Enhanced Data Loading with Validation ---
@st.cache_data(ttl=3600)
def load_application_data():
    """Load and validate provider data for the application."""
    try:
        # Try the enhanced loading function first
        provider_df = load_and_validate_provider_data()

        if provider_df.empty:
            # Fallback to original loading method
            provider_df = load_provider_data(filepath="data/cleaned_outbound_referrals.parquet")
            provider_df = validate_and_clean_coordinates(provider_df)

        # Try to load detailed referrals with better error handling
        detailed_referrals_df = pd.DataFrame()
        
        # Try detailed referrals file first
        detailed_referrals_filepath = "data/detailed_referrals.parquet"
        if Path(detailed_referrals_filepath).exists():
            detailed_referrals_df = load_detailed_referrals(filepath=detailed_referrals_filepath)
        
        # If detailed referrals not available or empty, try alternative file
        if detailed_referrals_df.empty:
            alt_filepath = "data/Referrals_App_Outbound.parquet"
            if Path(alt_filepath).exists():
                detailed_referrals_df = load_detailed_referrals(filepath=alt_filepath)
            else:
                st.info("Time-based filtering not available: No detailed referral data found.")

        return provider_df, detailed_referrals_df

    except Exception as e:
        st.error(f"Failed to load provider data: {e}")
        return pd.DataFrame(), pd.DataFrame()


# Load data using enhanced function
with st.spinner("Loading provider data..."):
    provider_df, detailed_referrals_df = load_application_data()

# Validate provider data quality and show feedback
if not provider_df.empty:
    data_valid, data_message = validate_provider_data(provider_df)
    if data_message:
        if data_valid:
            with st.expander("📊 Data Quality Summary", expanded=False):
                st.success(data_message)
        else:
            st.error(data_message)
else:
    st.warning("⚠️ No provider data available. Please check data files in the 'data/' directory.")

# --- Set random seed for reproducibility ---
np.random.seed(42)  # Ensures consistent placeholder data and recommendations across runs

# --- Streamlit Page Config ---
st.set_page_config(page_title="Provider Recommender", page_icon=":hospital:", layout="wide")

# --- Company Logo and Title at Top ---
st.image("assets/JaklitschLaw_NewLogo_withDogsRed.jpg", width=100)
st.markdown("<h1>Medical Provider Recommender for New Clients</h1>", unsafe_allow_html=True)


with st.expander(label="**INSTRUCTIONS** (*Click here to collapse.*)", expanded=True, icon="🧑‍🏫"):
    st.write(
        """
            1. Enter the client's address in the sidebar to the left.
            2. Choose how to balance provider proximity and referral count.
            3. Specify the minimum number of outbound referrals (minimum 1)
            4. Set the time period for calculating the outbound referral counts (e.g, last 30 days)
            5. Click ***Find Best Provider*** to get a recommendation.
                * By default, the app prioritizes the closests providers,
                  then prefers providers with fewer recent referrals.
            6. The final result is contact information to direct the client
               to the best provider.
            """
    )

# --- Sidebar Logo and Title ---
st.sidebar.markdown(
    "<h2 style='font-weight: bold; margin-bottom: 0.5em;'>Search Parameters</h2>",
    unsafe_allow_html=True,
)

# --- User Input Form ---
# This form collects the client's address and preferences.

with st.sidebar:
    with st.form(key="input_form", clear_on_submit=True):
        street = st.text_input(
            "Street Address",
            value=st.session_state.get("street", ""),
            help="e.g., 123 Main St",
            placeholder="Enter full street address",
        )
        city = st.text_input("City", value=st.session_state.get("city", ""), help="e.g., Baltimore")
        state = st.text_input("State", value=st.session_state.get("state", ""), help="e.g., MD")
        zipcode = st.text_input("Zip Code", value=st.session_state.get("zipcode", ""), help="5-digit ZIP")

        # Real-time address validation feedback
        if street or city or state or zipcode:
            full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
            if len(full_address.strip()) > 5:  # Basic check to avoid validating very short inputs
                is_valid, validation_message = validate_address(full_address)
                if is_valid:
                    if validation_message:  # Has suggestions but is valid
                        st.info(f"✅ Address looks good. {validation_message}")
                    else:
                        st.success("✅ Address format validated.")
                else:
                    st.warning(f"⚠️ {validation_message}")

        st.markdown("---")  # Visual separator

        # --- More accessible weight control ---
        blend = st.select_slider(
            "Prioritize Distance or Referral Count?",
            options=[
                "Only Distance",
                "Mostly Distance",
                "Balanced",
                "Mostly Referral Count",
                "Only Referral Count",
            ],
            value=st.session_state.get("blend", "Mostly Distance"),
            help="Choose how much to prioritize proximity (distance) vs. referral count.",
        )
        blend_map = {
            "Only Distance": (1.0, 0.0),
            "Mostly Distance": (0.75, 0.25),
            "Balanced": (0.5, 0.5),
            "Mostly Referral Count": (0.25, 0.75),
            "Only Referral Count": (0.0, 1.0),
        }
        alpha, beta = blend_map[blend]
        st.markdown(f"**Proximity (distance) weight:** {alpha:.2f}  |  **Referral Count weight:** {beta:.2f}")

        # --- Referral Count Filter ---
        min_referrals = st.number_input(
            "Minimum Inbound Referral Count",
            min_value=0,
            value=st.session_state.get("min_referrals", 1),
            help="Only show providers with at least this many referrals. Lower values show more providers, higher values show only established providers.",
        )

        # --- Time Period Filter
        time_period = st.date_input(
            "Time Period for Referral Count",
            value=[dt.date.today() - dt.timedelta(days=365), dt.date.today()],
            max_value=dt.date.today() + dt.timedelta(days=1),
            help="Calculate referral counts only for this time period. Defaults to last 12 months.",
        )

        use_time_filter = st.checkbox(
            "Enable time-based filtering",
            value=False,
            help="When enabled, referral counts will be calculated only for the selected time period.",
        )

        submit = st.form_submit_button("Find Best Provider")

        # Real-time address validation
        if street or city or state or zipcode:
            addr_valid, addr_message = validate_address_input(street or "", city or "", state or "", zipcode or "")
            if addr_message:
                if addr_valid:
                    st.info(addr_message)
                else:
                    st.warning(addr_message)

    if submit:
        # Validate address before processing
        addr_valid, addr_message = validate_address_input(street or "", city or "", state or "", zipcode or "")

        if not addr_valid:
            st.error("Please correct the address issues before proceeding.")
            st.markdown(addr_message)
        else:
            # Save input values to session_state
            st.session_state["street"] = street
            st.session_state["city"] = city
            st.session_state["state"] = state
            st.session_state["zipcode"] = zipcode

            st.session_state["blend"] = blend
            st.session_state["alpha"] = alpha
            st.session_state["min_referrals"] = min_referrals
            st.session_state["time_period"] = time_period
            st.session_state["use_time_filter"] = use_time_filter


# --- Tabs for Main Content ---
tabs = st.tabs(["Find Provider", "How Selection Works", "Data Quality"])


with tabs[0]:
    # --- Geocoding Setup ---
    if GEOPY_AVAILABLE:
        geolocator = Nominatim(user_agent="provider_recommender")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2, max_retries=3)
    else:
        st.error("Geocoding services are not available. Please install the geopy package.")
        st.stop()

    # --- Content for Results ---
    # Always show results if present in session state
    best = st.session_state.get("last_best")
    scored_df = st.session_state.get("last_scored_df")
    params = st.session_state.get("last_params", {})
    show_results = best is not None and scored_df is not None

    def process_address_and_recommend():
        """Helper function to process address geocoding and provider recommendation."""
        user_full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
        user_lat, user_lon = None, None

        # Enhanced geocoding with better error handling
        with st.spinner("🔍 Finding your location..."):
            try:
                # First, validate the complete address
                is_valid, validation_msg = validate_address(user_full_address)
                if not is_valid:
                    st.error(f"Address validation failed: {validation_msg}")
                    return None, None

                # Try geocoding with the improved function
                coords = geocode_address_with_cache(user_full_address)

                if coords:
                    user_lat, user_lon = coords
                    st.session_state["user_lat"] = user_lat
                    st.session_state["user_lon"] = user_lon
                    st.success(f"✅ Successfully located: {user_full_address}")
                else:
                    # Try fallback strategies
                    if street:
                        street_simple = street.split(",")[0].split(" Apt")[0].split(" Suite")[0]
                        coords = geocode_address_with_cache(f"{street_simple}, {city}, {state}")

                    if not coords and city and state:
                        coords = geocode_address_with_cache(f"{city}, {state}")

                    if not coords and zipcode:
                        coords = geocode_address_with_cache(zipcode)

                    if coords:
                        user_lat, user_lon = coords
                        st.session_state["user_lat"] = user_lat
                        st.session_state["user_lon"] = user_lon
                        st.warning("⚠️ Used approximate location based on available address components.")
                    else:
                        st.error("❌ Could not find coordinates for the provided address. Please verify and try again.")
                        return None, None

            except Exception as e:
                handle_streamlit_error(e, "geocoding address")
                return None, None

        if user_lat is not None and user_lon is not None:
            # Use time-based filtering if enabled
            if use_time_filter and not detailed_referrals_df.empty and len(time_period) == 2:
                start_date, end_date = time_period
                time_filtered_df = calculate_time_based_referral_counts(detailed_referrals_df, start_date, end_date)
                if not time_filtered_df.empty:
                    # Use time-filtered data
                    working_df = time_filtered_df
                    st.info(f"Using referral counts from {start_date} to {end_date}")
                else:
                    # Fall back to regular data if no results in time period
                    working_df = provider_df
                    st.warning(f"No referrals found in selected time period. Using all-time data.")
            else:
                # Use regular aggregated data
                working_df = provider_df

            filtered_df = working_df[working_df["Referral Count"] >= min_referrals].copy()
            filtered_df["Distance (Miles)"] = calculate_distances(user_lat, user_lon, filtered_df)
            best, scored_df = recommend_provider(
                filtered_df,
                distance_weight=alpha,
                referral_weight=beta,
                min_referrals=min_referrals,
            )

            # Store results and params in session state
            st.session_state["last_best"] = best
            st.session_state["last_scored_df"] = scored_df
            st.session_state["last_params"] = {
                "alpha": alpha,
                "beta": beta,
                "min_referrals": min_referrals,
            }

            return best, scored_df

        return None, None

    if submit and st.session_state.get("street"):
        best, scored_df = process_address_and_recommend()
        show_results = best is not None and isinstance(scored_df, pd.DataFrame)

    # --- Display results if available ---
    if show_results and best is not None and isinstance(scored_df, pd.DataFrame):
        # Use params from session state if available
        alpha_disp = params.get("alpha", alpha)
        beta_disp = params.get("beta", beta)

        # --- Highlighted Recommended Provider ---
        st.markdown(
            "<h3 style='color: #2E86C1;'>🏆 Recommended Provider</h3>",
            unsafe_allow_html=True,
        )

        # Safely handle provider name display
        try:
            provider_name = best["Full Name"] if "Full Name" in best.index else "Unknown Provider"
            st.markdown(
                f"<h4>{provider_name}</h4>",
                unsafe_allow_html=True,
            )
        except (KeyError, TypeError, AttributeError) as e:
            st.error(f"Error displaying provider name: {e}")
            st.markdown("<h4>Provider information unavailable</h4>", unsafe_allow_html=True)

        # Safely handle address URL creation
        try:
            if "Full Address" in best.index and pd.notna(best["Full Address"]) and best["Full Address"]:
                address_for_url = str(best["Full Address"]).replace(" ", "+")
                maps_url = f"https://www.google.com/maps/search/?api=1&query={address_for_url}"
                st.markdown(
                    f"🏥 <b>Address:</b> <a href='{maps_url}' target='_blank'>{best['Full Address']}</a>",
                    unsafe_allow_html=True,
                )
            else:
                # Try to construct address from components
                address_parts = []
                for col in ["Street", "City", "State", "Zip"]:
                    if col in best.index and pd.notna(best[col]) and best[col]:
                        address_parts.append(str(best[col]))

                if address_parts:
                    full_address = " ".join(address_parts)
                    st.markdown(
                        f"🏥 <b>Address:</b> {full_address}",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown("🏥 <b>Address:</b> Address information unavailable", unsafe_allow_html=True)
        except (KeyError, TypeError, AttributeError) as e:
            st.error(f"Error displaying provider address: {e}")
            st.markdown("🏥 <b>Address:</b> Address information unavailable", unsafe_allow_html=True)

        # Safely handle phone number display
        try:
            if "Phone Number" in best.index and pd.notna(best["Phone Number"]) and best["Phone Number"]:
                st.markdown(f"📞 <b>Phone:</b> {best['Phone Number']}", unsafe_allow_html=True)
        except (KeyError, TypeError, AttributeError):
            # Phone number not available or accessible
            pass

        st.write(f"*Providers sorted by: **{blend}***")
        mandatory_cols = [
            "Full Name",
            "Full Address",
            "Distance (Miles)",
            "Referral Count",
            "Score",
        ]

        # Check which columns actually exist
        available_cols = [col for col in mandatory_cols if col in scored_df.columns]

        if available_cols:
            st.dataframe(
                scored_df[available_cols].sort_values(
                    by="Score" if "Score" in available_cols else available_cols[0], ignore_index=True
                ),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.error("Unable to display results: required columns not found in data.")

        # --- Export Button ---
        try:
            provider_name = sanitize_filename(
                str(best["Full Name"]) if "Full Name" in best.index else "Unknown_Provider"
            )
            base_filename = f"Provider_{provider_name}"
            word_bytes = get_word_bytes(best)
            st.download_button(
                label="Export as Word Document",
                data=word_bytes,
                file_name=f"{base_filename}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except (KeyError, TypeError, AttributeError) as e:
            st.error(f"Error creating export: {e}")

        # --- Rationale for Selection ---
        with st.expander("Why was this provider selected?", expanded=False):
            try:
                rationale = []

                # Distance information
                if "Distance (Miles)" in best.index and pd.notna(best["Distance (Miles)"]):
                    rationale.append(f"* **Distance** from the address is **{best['Distance (Miles)']:.2f} miles**.")
                else:
                    rationale.append("* **Distance** information not available.")

                rationale.append("")

                # Referral count information
                if "Referral Count" in best.index and pd.notna(best["Referral Count"]):
                    rationale.append(
                        f"* This provider has **{best['Referral Count']}** recent referrals from our office (fewer are better for load balancing)."
                    )
                else:
                    rationale.append("* Referral count information not available.")

                rationale.append("")
                min_referrals_disp = params.get("min_referrals", min_referrals)
                rationale.append(
                    f"* Only providers with **{min_referrals_disp} or more referrals** were considered in this search."
                )
                rationale.append("")
                rationale.append(
                    f"The final score is a blend of normalized distance and referral count, using your chosen weights: **Distance weight = {alpha_disp:.2f}**, **Referral weight = {beta_disp:.2f}**."
                )
                rationale.append("The provider with the lowest blended score was recommended.")
                st.markdown("<br>".join(rationale), unsafe_allow_html=True)
            except (KeyError, TypeError, AttributeError) as e:
                st.error(f"Error displaying rationale: {e}")
                st.markdown("Rationale information unavailable.", unsafe_allow_html=True)
    elif submit:
        st.warning(
            f"No providers met the requirements (minimum {min_referrals} referrals). Please check the address, lower the minimum referral count, or try again."
        )

with tabs[1]:
    st.markdown("### How Provider Selection Works")

    st.markdown(
        """
    Our provider recommendation system uses a sophisticated algorithm that balances two key factors:
    **geographic proximity** and **referral load balancing** to ensure optimal client care and fair distribution.
    """
    )

    # Algorithm Steps
    st.markdown("#### 🔄 Algorithm Steps")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown(
            """
        **1. Address Geocoding**
        - Converts client address to latitude/longitude coordinates
        - Uses OpenStreetMap's Nominatim service
        - Implements fallback strategies for partial addresses

        **2. Distance Calculation**
        - Uses Haversine formula for accurate geographic distances
        - Accounts for Earth's curvature
        - Results in miles for easy interpretation

        **3. Data Normalization**
        - Distance: Min-max normalization to [0,1] scale
        - Referral Count: Min-max normalization to [0,1] scale
        - Ensures fair comparison between different metrics
        """
        )

    with col2:
        st.markdown(
            """
        **4. Weighted Scoring**
        - Combines normalized distance and referral count
        - Formula: `Score = α × Distance + β × Referral_Count`
        - Lower scores indicate better recommendations

        **5. Ranking & Selection**
        - Sorts providers by composite score (ascending)
        - Applies deterministic tie-breaking rules
        - Returns top recommendation with rationale

        **6. Load Balancing**
        - Prefers providers with fewer recent referrals
        - Helps distribute workload evenly across network
        - Maintains quality while optimizing capacity
        """
        )

    # Scoring Formula Explanation
    st.markdown("#### 📊 Scoring Formula")
    st.latex(
        r"Score = \alpha \times \frac{Distance - Distance_{min}}{Distance_{max} - Distance_{min}} + \beta \times \frac{Referrals - Referrals_{min}}{Referrals_{max} - Referrals_{min}}"
    )

    st.markdown(
        """
    Where:
    - **α (alpha)**: Distance weight (0.0 to 1.0)
    - **β (beta)**: Referral count weight (0.0 to 1.0)
    - **α + β = 1.0** for balanced weighting
    """
    )

    # Weight Selection Guide
    st.markdown("#### ⚖️ Weight Selection Guide")

    weight_guide = {
        "Only Distance (α=1.0, β=0.0)": "Prioritizes closest providers only. Best for urgent care or mobility-limited clients.",
        "Mostly Distance (α=0.75, β=0.25)": "Strong preference for proximity with slight load balancing. Good default choice.",
        "Balanced (α=0.5, β=0.5)": "Equal consideration of distance and load balancing. Optimal for most situations.",
        "Mostly Referral Count (α=0.25, β=0.75)": "Prioritizes load balancing with location consideration. Good for specialty care.",
        "Only Referral Count (α=0.0, β=1.0)": "Focuses purely on distributing referrals evenly across providers.",
    }

    for weight_type, description in weight_guide.items():
        st.markdown(f"**{weight_type}**: {description}")

    # Quality Assurance
    st.markdown("#### ✅ Quality Assurance Features")

    qa_col1, qa_col2 = st.columns([1, 1])

    with qa_col1:
        st.markdown(
            """
        **Data Validation**
        - Minimum referral thresholds ensure provider experience
        - Geographic coordinate validation
        - Address standardization and cleaning
        """
        )

    with qa_col2:
        st.markdown(
            """
        **Consistent Results**
        - Deterministic tie-breaking for reproducible outcomes
        - Cached geocoding for performance and consistency
        - Session state preservation during user interaction
        """
        )

    # Technical Implementation
    with st.expander("🔧 Technical Implementation Details", expanded=False):
        st.markdown(
            """
        **Geocoding Service**: OpenStreetMap Nominatim API
        - Free, reliable geocoding service
        - Rate-limited to respect service terms
        - 24-hour caching for performance optimization

        **Distance Calculation**: Haversine Formula
        ```python
        # Simplified version of our distance calculation
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 3958.8  # Earth's radius in miles
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * arcsin(sqrt(a))
            return R * c
        ```

        **Performance Optimizations**:
        - Vectorized distance calculations using NumPy
        - Streamlit caching for data loading and geocoding
        - Efficient pandas operations for data processing

        **Data Pipeline**:
        1. Raw referral data from Lead Docket exports
        2. Data cleaning and provider aggregation
        3. Geocoding and coordinate enrichment
        4. Runtime filtering and scoring
        """
        )

    st.markdown("---")
    st.markdown("*For technical questions or suggestions, contact the Data Operations team.*")

with tabs[2]:
    st.markdown("### 📊 Data Quality Monitoring")

    st.markdown(
        """
    Monitor the quality and completeness of provider data used in recommendations.
    Use this dashboard to identify data issues and track system health.
    """
    )

    st.info("💡 **Tip**: Run the standalone data dashboard for detailed analytics: `streamlit run data_dashboard.py`")

    # Quick data quality summary
    try:
        from data_dashboard import display_data_quality_dashboard

        if st.button("🚀 Launch Full Data Dashboard", help="Open comprehensive data quality dashboard"):
            st.markdown(
                """
            To launch the full data quality dashboard, run this command in your terminal:

            ```bash
            streamlit run data_dashboard.py
            ```

            The dashboard provides:
            - Geographic coverage maps
            - Referral trend analysis
            - Data completeness metrics
            - Quality issue identification
            - Performance monitoring
            """
            )

        # Show basic quality summary inline
        st.markdown("#### Quick Quality Check")

        if not provider_df.empty:
            data_valid, data_message = validate_provider_data(provider_df)

            if data_valid:
                st.success("✅ Provider data quality is good!")
            else:
                st.warning("⚠️ Provider data has some quality issues.")

            # Show key metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                total_providers = len(provider_df)
                st.metric("Total Providers", total_providers)

            with col2:
                if "Referral Count" in provider_df.columns:
                    avg_referrals = provider_df["Referral Count"].mean()
                    st.metric("Avg Referrals per Provider", f"{avg_referrals:.1f}")

            with col3:
                if "Latitude" in provider_df.columns and "Longitude" in provider_df.columns:
                    valid_coords = provider_df.dropna(subset=["Latitude", "Longitude"])
                    coord_completeness = len(valid_coords) / len(provider_df) * 100
                    st.metric("Coordinate Completeness", f"{coord_completeness:.1f}%")

            # Show recent issues if any
            with st.expander("📋 Data Quality Details", expanded=False):
                st.markdown(data_message)
        else:
            st.error("❌ No provider data available. Please check data files.")

    except ImportError:
        st.warning("Data dashboard module not available. Install plotly for full dashboard functionality.")
