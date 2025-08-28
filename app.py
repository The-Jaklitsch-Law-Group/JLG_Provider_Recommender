import streamlit as st
import datetime as dt
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from provider_utils import (
    sanitize_filename,
    load_provider_data,
    calculate_distances,
    recommend_provider,
    get_word_bytes,
)

# --- Helper Functions ---

provider_df = load_provider_data(filepath="data/cleaned_outbound_referrals.parquet")

# --- Set random seed for reproducibility ---
np.random.seed(42)  # Ensures consistent placeholder data and recommendations across runs

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Provider Recommender",
    page_icon=":hospital:",
    layout="wide"
)

# --- Company Logo and Title at Top ---
st.image("JaklitschLaw_NewLogo_withDogsRed.jpg", width=100)
st.markdown("<h1>Medical Provider Recommender for New Clients</h1>", unsafe_allow_html=True)


with st.expander(
    label="**INSTRUCTIONS** (*Click here to collapse.*)", expanded=True, icon="🧑‍🏫"
):
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

# # --- Start New Search Button ---
# if st.button("Start New Search"):
#     # Clear all session state keys related to form and results
#     for key in [
#         "street",
#         "city",
#         "state",
#         "zipcode",
#         "blend",
#         "alpha",
#         "last_best",
#         "last_scored_df",
#         "last_params",
#         "user_lat",
#         "user_lon",
#         "input_form",
#     ]:
#         if key in st.session_state:
#             del st.session_state[key]
#     # Rerun to reset form and results
#     st.rerun()

# --- User Input Form ---
# This form collects the client's address and preferences.

with st.sidebar:
    with st.form(key="input_form", clear_on_submit=True):

        street = st.text_input(
            "Street Address",
            value=st.session_state.get("street", ""),
            help="e.g., 123 Main St",
        )
        city = st.text_input(
            "City", value=st.session_state.get("city", ""), help="e.g., Baltimore"
        )
        state = st.text_input(
            "State", value=st.session_state.get("state", ""), help="e.g., MD"
        )
        zipcode = st.text_input(
            "Zip Code", value=st.session_state.get("zipcode", ""), help="5-digit ZIP"
        )

        # --- More accessible weight control ---
        blend = st.select_slider(
            "Prioritize Distance or Priority?",
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
        st.markdown(
            f"**Proximity (distance) weight:** {alpha:.2f}  |  **Referral Count weight:** {beta:.2f}"
        )
        
        # --- Referral Count Filter ---
        min_referrals = st.number_input(
            "Minimum Inbound Referral Count",
            min_value=0,
            value=st.session_state.get("min_referrals", 1),
            help="Only show providers with at least this many referrals. Lower values show more providers, higher values show only established providers.",
        )
        
        # --- Time Period Filter
        # Currently inactive pending updates to workflow.
        time_period = st.date_input(
            "Time Period for Referral Count",
            value = [dt.date.today() - dt.timedelta(days=365),dt.date.today()],
            max_value = dt.date.today() + dt.timedelta(days=1),
            help="Only show providers with referrals within this time period. Leave blank to include all time periods.",
        )

        submit = st.form_submit_button("Find Best Provider")

    if submit:
        # Save input values to session_state
        st.session_state["street"] = street
        st.session_state["city"] = city
        st.session_state["state"] = state
        st.session_state["zipcode"] = zipcode

        st.session_state["blend"] = blend
        st.session_state["alpha"] = alpha
        st.session_state["min_referrals"] = min_referrals
        # beta is always 1 - alpha


# --- Tabs for Main Content ---
tabs = st.tabs(["Find Provider", "How Selection Works"])


with tabs[0]:

    # --- Geocoding Setup ---
    geolocator = Nominatim(user_agent="provider_recommender")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2, max_retries=3)

    # --- Content for Results ---
    # Always show results if present in session state
    best = st.session_state.get("last_best")
    scored_df = st.session_state.get("last_scored_df")
    params = st.session_state.get("last_params", {})
    show_results = best is not None and scored_df is not None

    if submit:
        user_full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
        user_lat, user_lon = None, None
        try:
            user_location = geocode(user_full_address, timeout=10)
            if not user_location and street:
                street_simple = street.split(",")[0].split(" Apt")[0].split(" Suite")[0]
                user_location = geocode(street_simple, timeout=10)
            if not user_location:
                if city and state:
                    user_location = geocode(f"{city}, {state}", timeout=10)
                elif zipcode:
                    user_location = geocode(zipcode, timeout=10)
            if user_location:
                user_lat, user_lon = user_location.latitude, user_location.longitude
                st.session_state["user_lat"] = user_lat
                st.session_state["user_lon"] = user_lon
            else:
                st.error("Could not geocode your address. Please check and try again.")
        except Exception as e:
            st.error(f"Geocoding error: {e}")

        if user_lat is not None and user_lon is not None:
            filtered_df = provider_df[provider_df["Referral Count"] >= min_referrals].copy()
            filtered_df["Distance (Miles)"] = calculate_distances(
                user_lat, user_lon, filtered_df
            )
            best, scored_df = recommend_provider(
                filtered_df,
                distance_weight=alpha,
                referral_weight=beta,
            )

            # Store results and params in session state
            st.session_state["last_best"] = best
            st.session_state["last_scored_df"] = scored_df
            st.session_state["last_params"] = {
                "alpha": alpha,
                "beta": beta,
                "min_referrals": min_referrals,
            }

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
        st.markdown(
            # f"<h4 style='color: #117A65;'>{best['Full Name']}</h4>",
            f"<h4>{best['Full Name']}</h4>",
            unsafe_allow_html=True,
        )
        address_for_url = best["Full Address"].replace(" ", "+")
        maps_url = f"https://www.google.com/maps/search/?api=1&query={address_for_url}"
        st.markdown(
            f"🏥 <b>Address:</b> <a href='{maps_url}' target='_blank'>{best['Full Address']}</a>",
            unsafe_allow_html=True,
        )
        if "Phone Number" in best:
            st.markdown(
                f"📞 <b>Phone:</b> {best['Phone Number']}", unsafe_allow_html=True
            )

        st.write(f"*Providers sorted by: **{blend}***")
        mandatory_cols = [
            "Full Name",
            "Full Address",
            "Distance (Miles)",
            "Referral Count",
            "Score",
        ]
        display_cols = mandatory_cols
        if isinstance(scored_df, pd.DataFrame) and all(
            col in scored_df.columns for col in mandatory_cols
        ):
            
            
            df = st.dataframe(
                scored_df[display_cols]
                .sort_values(by="Score", ignore_index=True),
                hide_index=True
                # .head()
            )

        # --- Export Button ---
        provider_name = sanitize_filename(str(best["Full Name"]))
        base_filename = f"Provider_{provider_name}"
        word_bytes = get_word_bytes(best)
        st.download_button(
            label="Export as Word Document",
            data=word_bytes,
            file_name=f"{base_filename}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        # --- Rationale for Selection ---
        with st.expander("Why was this provider selected?", expanded=False):
            rationale = []
            rationale.append(
                f"* **Distance** from the address is **{best["Distance (Miles)"]:.2f} miles**."
            )
            rationale.append("")
            rationale.append(
                f"* This provider has **{best['Referral Count']}** recent referrals from our office (fewer are better for load balancing)."
            )
            rationale.append("")
            min_referrals_disp = params.get("min_referrals", min_referrals)
            rationale.append(
                f"* Only providers with **{min_referrals_disp} or more referrals** were considered in this search."
            )
            rationale.append("")
            rationale.append(
                f"The final score is a blend of normalized distance and referral count, using your chosen weights: **Distance weight = {alpha_disp:.2f}**, **Referral weight = {beta_disp:.2f}**."
            )
            rationale.append(
                "The provider with the lowest blended score was recommended."
            )
            st.markdown("<br>".join(rationale), unsafe_allow_html=True)
    elif submit:
        st.warning(
            f"No providers met the requirements (minimum {min_referrals} referrals). Please check the address, lower the minimum referral count, or try again."
        )
