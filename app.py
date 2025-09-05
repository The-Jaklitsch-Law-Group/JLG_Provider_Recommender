import datetime as dt
import traceback
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

# Import optimized data ingestion
from data_ingestion import (
    get_data_ingestion_status,
    load_detailed_referrals,
    load_inbound_referrals,
    load_provider_data,
    refresh_data_cache,
)
from provider_utils import (  # Import new enhanced functions
    calculate_distances,
    calculate_inbound_referral_counts,
    calculate_time_based_referral_counts,
    geocode_address_with_cache,
    get_word_bytes,
    handle_streamlit_error,
    load_and_validate_provider_data,
    recommend_provider,
    sanitize_filename,
    validate_address,
    validate_address_input,
    validate_and_clean_coordinates,
    validate_provider_data,
)

# --- Helper Functions ---


# --- Helper Functions ---


def clean_address_data(df):
    """Clean and standardize address data, handling mixed types and missing values."""
    if df.empty:
        return df

    df = df.copy()

    # List of potential address-related columns
    address_columns = [
        "Street",
        "City",
        "State",
        "Zip",
        "Full Address",
        "Address",
        "Address Line 1",
        "Address Line 2",
        "Zip Code",
        "Postal Code",
        "Province",
    ]

    # Clean each address column that exists
    for col in address_columns:
        if col in df.columns:
            # Convert to string and handle various null representations
            df[col] = df[col].astype(str)
            df[col] = df[col].replace({"nan": "", "None": "", "NaN": "", "null": "", "NULL": "", "<NA>": ""})
            df[col] = df[col].fillna("")

            # Strip whitespace
            df[col] = df[col].str.strip()

    return df


def build_full_address(df):
    """Build Full Address from components, handling missing values safely."""
    if df.empty:
        return df

    df = df.copy()

    # Ensure all address columns are strings and handle NaN values
    address_cols = ["Street", "City", "State", "Zip"]
    for col in address_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).replace(["nan", "None", "NaN"], "").fillna("")

    # Build Full Address from available components
    def safe_join_address(row):
        parts = []

        # Add street if available
        if "Street" in row.index and row["Street"].strip():
            parts.append(row["Street"].strip())

        # Add city if available
        if "City" in row.index and row["City"].strip():
            parts.append(row["City"].strip())

        # Add state if available
        if "State" in row.index and row["State"].strip():
            parts.append(row["State"].strip())

        # Add zip if available
        if "Zip" in row.index and row["Zip"].strip():
            parts.append(row["Zip"].strip())

        return ", ".join(parts) if parts else ""

    df["Full Address"] = df.apply(safe_join_address, axis=1)

    return df


# --- Enhanced Data Loading with Validation ---
@st.cache_data(ttl=3600)
def load_application_data():
    """Load and validate provider data for the application."""
    try:
        # Try the enhanced loading function first
        provider_df = load_and_validate_provider_data()

        if provider_df.empty:
            # Fallback to optimized loading method
            provider_df = load_provider_data()
            provider_df = validate_and_clean_coordinates(provider_df)

        # Clean and validate provider data - handle missing values
        if not provider_df.empty:
            # Clean address data to prevent string concatenation errors
            provider_df = clean_address_data(provider_df)

            # Ensure all address components are strings and handle nulls
            address_columns = ["Street", "City", "State", "Zip", "Full Address"]
            for col in address_columns:
                if col in provider_df.columns:
                    # Convert to string and replace NaN/None with empty string
                    provider_df[col] = provider_df[col].astype(str).replace(["nan", "None", "NaN"], "")
                    provider_df[col] = provider_df[col].fillna("")

            # Drop records with missing critical address information
            initial_count = len(provider_df)

            # If Full Address exists, use it; otherwise check individual components
            if "Full Address" in provider_df.columns:
                # Drop rows where Full Address is empty or just whitespace
                provider_df = provider_df[
                    (provider_df["Full Address"].str.strip() != "")
                    & (provider_df["Full Address"] != "nan")
                    & (provider_df["Full Address"] != "None")
                ]
            else:
                # Drop rows missing critical address components
                critical_cols = ["Street", "City", "State"]
                available_critical = [col for col in critical_cols if col in provider_df.columns]

                if available_critical:
                    # Create a mask for rows with at least some address info
                    mask = pd.Series(True, index=provider_df.index)
                    for col in available_critical:
                        mask &= (
                            (provider_df[col].str.strip() != "")
                            & (provider_df[col] != "nan")
                            & (provider_df[col] != "None")
                        )
                    provider_df = provider_df[mask]

            # Build Full Address if it doesn't exist or is incomplete
            if "Full Address" not in provider_df.columns or provider_df["Full Address"].isna().any():
                provider_df = build_full_address(provider_df)

            dropped_count = initial_count - len(provider_df)
            if dropped_count > 0:
                st.info(f"ℹ️ Dropped {dropped_count} providers with incomplete address information")

        # Load detailed referrals with optimized ingestion
        detailed_referrals_df = load_detailed_referrals()

        # Load inbound referrals data with optimized ingestion
        inbound_referrals_df = load_inbound_referrals()

        # Calculate inbound referral counts (time filtering will be applied later during recommendation)
        if not inbound_referrals_df.empty:
            inbound_counts_df = calculate_inbound_referral_counts(inbound_referrals_df)

            # Merge inbound referral counts with provider data
            if not inbound_counts_df.empty and not provider_df.empty:
                # Merge on Person ID first, then try Full Name
                if "Person ID" in provider_df.columns and "Person ID" in inbound_counts_df.columns:
                    provider_df = provider_df.merge(
                        inbound_counts_df[["Person ID", "Inbound Referral Count"]], on="Person ID", how="left"
                    )
                else:
                    # Fallback to name-based matching
                    provider_df = provider_df.merge(
                        inbound_counts_df[["Full Name", "Inbound Referral Count"]], on="Full Name", how="left"
                    )

                # Fill missing inbound referral counts with 0
                provider_df["Inbound Referral Count"] = provider_df["Inbound Referral Count"].fillna(0)

                st.success(f"✅ Merged inbound referral data for {len(inbound_counts_df)} providers")
            else:
                st.warning("⚠️ Could not merge inbound referral data - empty datasets")
        else:
            st.info("ℹ️ No inbound referral data available")

        return provider_df, detailed_referrals_df

    except Exception as e:
        st.error(f"Failed to load provider data: {e}")
        # Add more detailed error information for debugging
        st.error(f"Detailed error: {traceback.format_exc()}")
        return pd.DataFrame(), pd.DataFrame()


def apply_time_filtering(provider_df, detailed_referrals_df, start_date, end_date, use_time_filter):
    """Apply time filtering to both inbound and outbound referrals and return updated provider data."""

    if not use_time_filter or not start_date or not end_date:
        return provider_df

    working_df = provider_df.copy()

    # Apply time filtering to outbound referrals
    if not detailed_referrals_df.empty:
        time_filtered_outbound = calculate_time_based_referral_counts(detailed_referrals_df, start_date, end_date)
        if not time_filtered_outbound.empty:
            # Update outbound referral counts with time-filtered data
            # Merge on Person ID or Full Name
            if "Person ID" in working_df.columns and "Person ID" in time_filtered_outbound.columns:
                # Remove existing referral count and merge new time-filtered counts
                working_df = working_df.drop(columns=["Referral Count"], errors="ignore")
                working_df = working_df.merge(
                    time_filtered_outbound[["Person ID", "Referral Count"]], on="Person ID", how="left"
                )
            else:
                # Fallback to name-based matching
                working_df = working_df.drop(columns=["Referral Count"], errors="ignore")
                working_df = working_df.merge(
                    time_filtered_outbound[["Full Name", "Referral Count"]], on="Full Name", how="left"
                )

            # Fill missing outbound referral counts with 0
            working_df["Referral Count"] = working_df["Referral Count"].fillna(0)
            st.info(f"📊 Applied time filter to outbound referrals: {start_date} to {end_date}")
        else:
            st.warning("⚠️ No outbound referrals found in selected time period.")

    # Apply time filtering to inbound referrals if available
    inbound_referrals_df = load_inbound_referrals()
    if not inbound_referrals_df.empty:
        time_filtered_inbound = calculate_inbound_referral_counts(inbound_referrals_df, start_date, end_date)
        if not time_filtered_inbound.empty:
            # Update inbound referral counts with time-filtered data
            working_df = working_df.drop(columns=["Inbound Referral Count"], errors="ignore")
            if "Person ID" in working_df.columns and "Person ID" in time_filtered_inbound.columns:
                working_df = working_df.merge(
                    time_filtered_inbound[["Person ID", "Inbound Referral Count"]], on="Person ID", how="left"
                )
            else:
                working_df = working_df.merge(
                    time_filtered_inbound[["Full Name", "Inbound Referral Count"]], on="Full Name", how="left"
                )

            # Fill missing inbound referral counts with 0
            working_df["Inbound Referral Count"] = working_df["Inbound Referral Count"].fillna(0)
            st.info(f"📊 Applied time filter to inbound referrals: {start_date} to {end_date}")
        else:
            st.warning("⚠️ No inbound referrals found in selected time period.")

    return working_df


# Load data using enhanced function
with st.spinner("Loading provider data..."):
    # Load base data without time filtering initially
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
            4. Set the time period for calculating referral counts (defaults to rolling last year)
               * This applies to both inbound and outbound referrals
               * Enable/disable time-based filtering as needed
            5. Click ***Find Best Provider*** to get a recommendation.
                * By default, the app prioritizes the closest providers,
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

        # --- Weight control with three factors ---
        st.markdown("### 🎯 Scoring Weights")

        # Check if inbound referral data is available
        has_inbound_data = "Inbound Referral Count" in provider_df.columns if not provider_df.empty else False

        # Initialize variables
        distance_weight = outbound_weight = inbound_weight = 0.0
        alpha = beta = gamma = 0.0
        blend = "Balanced"  # Default value

        if has_inbound_data:
            st.info("✅ Inbound referral data available - three-factor scoring enabled")

            # Use individual sliders for three-factor scoring with proportional weights
            distance_weight = st.slider(
                "Distance Importance",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("distance_weight", 0.4),
                step=0.05,
                help="Relative importance of provider proximity (0.0 = not important, 1.0 = most important)",
            )

            outbound_weight = st.slider(
                "Outbound Referral Importance",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("outbound_weight", 0.4),
                step=0.05,
                help="Relative importance of load balancing (fewer recent referrals preferred)",
            )

            inbound_weight = st.slider(
                "Inbound Referral Importance",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("inbound_weight", 0.2),
                step=0.05,
                help="Relative importance of mutual referral relationships",
            )

            # Normalize weights to sum to 1.0
            total_weight = distance_weight + outbound_weight + inbound_weight
            if total_weight > 0:
                alpha = distance_weight / total_weight
                beta = outbound_weight / total_weight
                gamma = inbound_weight / total_weight
            else:
                # Default equal weights if all are zero
                alpha = beta = gamma = 1 / 3

            st.markdown(
                f"**Normalized weights:** Distance: {alpha:.2f} | "
                f"Outbound Referrals: {beta:.2f} | Inbound Referrals: {gamma:.2f} "
                f"(Total: {alpha + beta + gamma:.2f})"
            )

            # Show raw values for transparency
            st.caption(
                f"Raw importance values: Distance({distance_weight:.2f}) + "
                f"Outbound({outbound_weight:.2f}) + Inbound({inbound_weight:.2f}) = {total_weight:.2f}"
            )

        else:
            st.warning("⚠️ No inbound referral data - using two-factor scoring")

            # Use individual sliders for two-factor scoring with proportional weights
            distance_weight = st.slider(
                "Distance Importance",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("distance_weight", 0.6),
                step=0.05,
                help="Relative importance of provider proximity (0.0 = not important, 1.0 = most important)",
            )

            outbound_weight = st.slider(
                "Outbound Referral Importance",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.get("outbound_weight", 0.4),
                step=0.05,
                help="Relative importance of load balancing (fewer recent referrals preferred)",
            )

            # Normalize weights to sum to 1.0
            total_weight = distance_weight + outbound_weight
            if total_weight > 0:
                alpha = distance_weight / total_weight
                beta = outbound_weight / total_weight
            else:
                # Default equal weights if both are zero
                alpha = beta = 0.5

            gamma = 0.0  # No inbound weight

            st.markdown(
                f"**Normalized weights:** Distance: {alpha:.2f} | "
                f"Outbound Referrals: {beta:.2f} (Total: {alpha + beta:.2f})"
            )

            # Show raw values for transparency
            st.caption(
                f"Raw importance values: Distance({distance_weight:.2f}) + "
                f"Outbound({outbound_weight:.2f}) = {total_weight:.2f}"
            )

        # --- Referral Count Filter ---
        min_referrals = st.number_input(
            "Minimum Outbound Referral Count",
            min_value=0,
            value=st.session_state.get("min_referrals", 1),
            help="Only show providers with at least this many outbound referrals. Lower values show more providers, higher values show only established providers.",
        )

        # --- Time Period Filter
        time_period = st.date_input(
            "Time Period for Referral Count",
            value=[dt.date.today() - dt.timedelta(days=365), dt.date.today()],
            max_value=dt.date.today() + dt.timedelta(days=1),
            help="Calculate referral counts only for this time period. Defaults to rolling last year.",
        )

        use_time_filter = st.checkbox(
            "Enable time-based filtering",
            value=True,
            help="When enabled, referral counts will be calculated only for the selected time period. Applies to both inbound and outbound referrals.",
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

            # Save weight values to session state
            if has_inbound_data:
                st.session_state["distance_weight"] = distance_weight
                st.session_state["outbound_weight"] = outbound_weight
                st.session_state["inbound_weight"] = inbound_weight
                st.session_state["alpha"] = alpha
                st.session_state["beta"] = beta
                st.session_state["gamma"] = gamma
                st.session_state["scoring_type"] = "three_factor"
            else:
                st.session_state["distance_weight"] = distance_weight
                st.session_state["outbound_weight"] = outbound_weight
                st.session_state["alpha"] = alpha
                st.session_state["beta"] = beta
                st.session_state["gamma"] = gamma
                st.session_state["scoring_type"] = "two_factor"

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
            # Apply time filtering to both inbound and outbound referrals if enabled
            if use_time_filter and len(time_period) == 2:
                start_date, end_date = time_period
                working_df = apply_time_filtering(
                    provider_df, detailed_referrals_df, start_date, end_date, use_time_filter
                )
            else:
                # Use regular data without time filtering
                working_df = provider_df

            filtered_df = working_df[working_df["Referral Count"] >= min_referrals].copy()
            filtered_df["Distance (Miles)"] = calculate_distances(user_lat, user_lon, filtered_df)
            best, scored_df = recommend_provider(
                filtered_df,
                distance_weight=alpha,
                referral_weight=beta,
                inbound_weight=gamma,
                min_referrals=min_referrals,
            )

            # Store results and params in session state
            st.session_state["last_best"] = best
            st.session_state["last_scored_df"] = scored_df
            st.session_state["last_params"] = {
                "alpha": alpha,
                "beta": beta,
                "gamma": gamma,
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

        # Display scoring method used
        scoring_type = st.session_state.get("scoring_type", "two_factor")
        if scoring_type == "three_factor":
            alpha_disp = st.session_state.get("alpha", 0.33)
            beta_disp = st.session_state.get("beta", 0.33)
            gamma_disp = st.session_state.get("gamma", 0.33)
            st.write(
                f"*Three-factor scoring: Distance({alpha_disp:.1%}) + Outbound({beta_disp:.1%}) + Inbound({gamma_disp:.1%})*"
            )
        else:
            alpha_disp = st.session_state.get("alpha", 0.6)
            beta_disp = st.session_state.get("beta", 0.4)
            st.write(f"*Two-factor scoring: Distance({alpha_disp:.1%}) + Outbound({beta_disp:.1%})*")
        mandatory_cols = [
            "Full Name",
            "Full Address",
            "Distance (Miles)",
            "Referral Count",
        ]

        # Add inbound referral count if available
        if "Inbound Referral Count" in scored_df.columns:
            mandatory_cols.append("Inbound Referral Count")

        mandatory_cols.append("Score")  # Score should be last

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

                # Get current weights from session state
                scoring_type = st.session_state.get("scoring_type", "two_factor")
                if scoring_type == "three_factor":
                    alpha_disp = st.session_state.get("alpha", 0.33)
                    beta_disp = st.session_state.get("beta", 0.33)
                    gamma_disp = st.session_state.get("gamma", 0.33)
                    rationale.append(
                        f"The final score combines normalized distance, outbound referrals, and inbound referrals using your chosen weights: "
                        f"**Distance = {alpha_disp:.1%}**, **Outbound Referrals = {beta_disp:.1%}**, **Inbound Referrals = {gamma_disp:.1%}**."
                    )
                else:
                    alpha_disp = st.session_state.get("alpha", 0.6)
                    beta_disp = st.session_state.get("beta", 0.4)
                    rationale.append(
                        f"The final score combines normalized distance and outbound referrals using your chosen weights: "
                        f"**Distance = {alpha_disp:.1%}**, **Outbound Referrals = {beta_disp:.1%}**."
                    )
                rationale.append("The provider with the lowest composite score was recommended.")
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
    Our provider recommendation system uses a sophisticated algorithm that balances multiple key factors:
    **geographic proximity**, **outbound referral load balancing**, and **inbound referral patterns**
    to ensure optimal client care and fair distribution across our provider network.
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
        - Outbound Referral Count: Min-max normalization to [0,1] scale
        - Inbound Referral Count: Min-max normalization to [0,1] scale (when available)
        - Ensures fair comparison between different metrics
        """
        )

    with col2:
        st.markdown(
            """
        **4. Weighted Scoring**
        - Combines normalized distance, outbound referrals, and inbound referrals
        - Three-factor formula: `Score = α × Distance + β × Outbound_Referrals + γ × Inbound_Referrals`
        - Two-factor fallback: `Score = α × Distance + β × Referral_Count`
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
    st.markdown("#### 📊 Scoring Formulas")

    st.markdown("**Three-Factor Scoring (when inbound data is available):**")
    st.latex(r"Score = \alpha \times Distance_{norm} + \beta \times (1-Outbound_{norm}) + \gamma \times Inbound_{norm}")

    st.markdown("**Two-Factor Scoring (fallback):**")
    st.latex(r"Score = \alpha \times Distance_{norm} + \beta \times (1-Outbound_{norm})")

    st.markdown(
        """
    Where:
    - **α (alpha)**: Distance weight (normalized to 0.0-1.0, with all weights summing to 1.0)
    - **β (beta)**: Outbound referral count weight (normalized to 0.0-1.0)
    - **γ (gamma)**: Inbound referral count weight (normalized to 0.0-1.0, three-factor only)
    - **α + β + γ = 1.0** for three-factor scoring
    - **α + β = 1.0** for two-factor scoring
    - Weights represent relative importance/priority of each factor
    - Lower outbound referrals are preferred (load balancing)
    - Higher inbound referrals are preferred (mutual referral relationships)
    """
    )

    # Weight Selection Guide
    st.markdown("#### ⚖️ Weight Selection Guide")

    st.markdown("**Three-Factor Scoring Options:**")
    st.markdown(
        """
    Set the relative importance of each factor (weights will be automatically normalized to sum to 1.0):

    - **Distance-Priority**: Distance(0.6) + Outbound(0.3) + Inbound(0.1) → (60%, 30%, 10%)
    - **Balanced**: Distance(0.4) + Outbound(0.4) + Inbound(0.2) → (40%, 40%, 20%)
    - **Relationship-Focus**: Distance(0.2) + Outbound(0.3) + Inbound(0.5) → (20%, 30%, 50%)
    - **Load-Balancing**: Distance(0.2) + Outbound(0.6) + Inbound(0.2) → (20%, 60%, 20%)
    - **Equal Weight**: Distance(0.33) + Outbound(0.33) + Inbound(0.33) → (33%, 33%, 33%)

    💡 **Tip**: Higher raw values = more importance. The system automatically normalizes to percentages.
    """
    )

    st.markdown("**Two-Factor Scoring Options:**")
    st.markdown(
        """
    For two-factor scoring, set the relative importance (automatically normalized):

    - **Distance Priority**: Distance(0.8) + Outbound(0.2) → (80%, 20%)
    - **Balanced**: Distance(0.5) + Outbound(0.5) → (50%, 50%)
    - **Load Balancing Priority**: Distance(0.2) + Outbound(0.8) → (20%, 80%)
    - **Distance Only**: Distance(1.0) + Outbound(0.0) → (100%, 0%)
    - **Load Balancing Only**: Distance(0.0) + Outbound(1.0) → (0%, 100%)

    💡 **Tip**: The final weights always sum to 100% for consistent, interpretable scoring.
    """
    )

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
