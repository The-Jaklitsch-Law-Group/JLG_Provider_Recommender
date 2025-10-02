import datetime as dt
import streamlit as st

from src.app_logic import load_application_data
from src.utils.addressing import validate_address_input

try:
    from src.utils.geocoding import geocode_address_with_cache
    GEOCODE_AVAILABLE = True
except Exception:
    GEOCODE_AVAILABLE = False

st.set_page_config(page_title="Search", page_icon=":mag:", layout="wide")

st.title("🔎 Provider Search")
st.caption("Find the best provider for your client — just enter an address and click Search!")

with st.spinner("Loading provider data..."):
    provider_df, detailed_referrals_df = load_application_data()

has_inbound = ("Inbound Referral Count" in provider_df.columns) if not provider_df.empty else False

# Address input section with improved layout
st.subheader("📍 Client Address")
col1, col2 = st.columns([3, 1])
with col1:
    street = str(st.text_input(
        "Street Address",
        st.session_state.get("street", "14350 Old Marlboro Pike") or "",
        help="Enter the client's street address"
    ))
with col2:
    zipcode = str(st.text_input(
        "ZIP Code",
        st.session_state.get("zipcode", "20772") or "",
        help="5-digit ZIP code"
    ))

col3, col4 = st.columns(2)
with col3:
    city = str(st.text_input("City", st.session_state.get("city", "Upper Marlboro") or ""))
with col4:
    state = str(st.text_input(
        "State",
        st.session_state.get("state", "MD") or "",
        help="Two-letter state code (e.g., MD, VA)"
    ))

full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")

# Quick search presets
st.divider()
st.subheader("🎯 Search Preferences")

preset_choice = st.radio(
    "Choose a search profile:",
    ["Balanced (Recommended)", "Prioritize Proximity", "Balance Workload", "Custom Settings"],
    horizontal=True,
    help="Select a preset to automatically configure search weights, or choose Custom to set your own"
)

# Set weights based on preset
if preset_choice == "Balanced (Recommended)":
    distance_weight = 0.4
    outbound_weight = 0.4
    inbound_weight = 0.1 if has_inbound else 0.0
    preferred_weight = 0.1
elif preset_choice == "Prioritize Proximity":
    distance_weight = 0.7
    outbound_weight = 0.2
    inbound_weight = 0.05 if has_inbound else 0.0
    preferred_weight = 0.05
elif preset_choice == "Balance Workload":
    distance_weight = 0.2
    outbound_weight = 0.6
    inbound_weight = 0.1 if has_inbound else 0.0
    preferred_weight = 0.1
else:  # Custom Settings
    with st.expander("⚖️ Custom Scoring Weights", expanded=True):
        st.caption("Adjust these sliders to control how each factor influences the recommendation.")

        distance_weight = st.slider(
            "📍 Distance Importance",
            0.0,
            1.0,
            st.session_state.get("distance_weight", 0.4 if has_inbound else 0.6),
            0.05,
            help="Higher values prioritize providers closer to the client"
        )
        outbound_weight = st.slider(
            "📊 Outbound Referral Importance",
            0.0,
            1.0,
            st.session_state.get("outbound_weight", 0.4),
            0.05,
            help="Higher values favor providers with fewer active cases"
        )
        if has_inbound:
            inbound_weight = st.slider(
                "🤝 Inbound Referral Importance",
                0.0,
                1.0,
                st.session_state.get("inbound_weight", 0.2),
                0.05,
                help="Higher values favor providers who refer cases to us"
            )
        else:
            inbound_weight = 0.0
        preferred_weight = st.slider(
            "⭐ Preferred Provider Importance",
            0.0,
            1.0,
            st.session_state.get("preferred_weight", 0.1),
            0.05,
            help="Higher values favor designated preferred providers"
        )

# Calculate normalized weights
total = distance_weight + outbound_weight + (inbound_weight if has_inbound else 0) + preferred_weight
if total == 0:
    st.error("⚠️ At least one weight must be greater than 0. Please adjust your settings.")
alpha = distance_weight / total if total else 0.5
beta = outbound_weight / total if total else 0.5
gamma = inbound_weight / total if has_inbound and total else 0.0
pref_norm = preferred_weight / total if total else 0.0

# Show normalized weights in a more visual way
if preset_choice == "Custom Settings":
    with st.expander("📊 View Normalized Weights"):
        st.caption("Your settings automatically adjusted to total 100%:")
        cols = st.columns(4 if has_inbound else 3)
        cols[0].metric("Distance", f"{alpha*100:.0f}%")
        cols[1].metric("Outbound", f"{beta*100:.0f}%")
        if has_inbound:
            cols[2].metric("Inbound", f"{gamma*100:.0f}%")
            cols[3].metric("Preferred", f"{pref_norm*100:.0f}%")
        else:
            cols[2].metric("Preferred", f"{pref_norm*100:.0f}%")

# Advanced filters in collapsible section
with st.expander("⚙️ Advanced Filters (Optional)"):
    st.caption("Set additional criteria to refine your search results.")

    max_radius_miles = st.slider(
        "Maximum Distance (miles)",
        1,
        200,
        st.session_state.get("max_radius_miles", 25),
        5,
        help="Only show providers within this distance"
    )

    min_referrals = st.number_input(
        "Minimum Experience (referral count)",
        0,
        100,
        value=st.session_state.get("min_referrals", 0),
        help="Require providers to have handled at least this many cases"
    )

    col_time1, col_time2 = st.columns([3, 1])
    with col_time1:
        time_period = st.date_input(
            "Referral Time Period",
            value=st.session_state.get(
                "time_period", [dt.date.today() - dt.timedelta(days=365), dt.date.today()]
            ),
            help="Consider only referrals within this date range"
        )
    with col_time2:
        use_time_filter = st.checkbox(
            "Enable",
            value=st.session_state.get("use_time_filter", True),
            help="Apply time period filter"
        )

st.divider()

# Prominent search button
col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
with col_btn2:
    search_clicked = st.button("🔍 Find Providers", type="primary", use_container_width=True)

if search_clicked:
    # Validate address
    addr_valid, addr_msg = validate_address_input(street, city, state, zipcode)
    if not addr_valid:
        st.error("⚠️ Please fix the following address issues:")
        if addr_msg:
            st.info(addr_msg)
        st.stop()

    # Check geocoding availability
    if not GEOCODE_AVAILABLE:
        st.error("❌ Geocoding service unavailable. Please contact support.")
        st.info("Technical note: geopy package is not installed")
        st.stop()

    # Geocode the address
    with st.spinner("🌍 Looking up address coordinates..."):
        coords = geocode_address_with_cache(full_address) if GEOCODE_AVAILABLE else None

    if not coords:
        st.error("❌ Unable to find the address. Please check and try again.")
        st.info(f"Tried to geocode: {full_address}")
        st.stop()

    # Success! Store search parameters
    user_lat, user_lon = coords
    st.session_state["street"] = street
    st.session_state["city"] = city
    st.session_state["state"] = state
    st.session_state["zipcode"] = zipcode
    st.session_state["user_lat"] = float(user_lat)
    st.session_state["user_lon"] = float(user_lon)
    st.session_state["alpha"] = float(alpha)
    st.session_state["beta"] = float(beta)
    st.session_state["gamma"] = float(gamma)
    st.session_state["preferred_weight"] = float(preferred_weight)
    st.session_state["preferred_norm"] = float(pref_norm)
    st.session_state["distance_weight"] = float(distance_weight)
    st.session_state["outbound_weight"] = float(outbound_weight)
    st.session_state["inbound_weight"] = float(inbound_weight)
    st.session_state["min_referrals"] = int(min_referrals)
    st.session_state["time_period"] = time_period
    st.session_state["use_time_filter"] = bool(use_time_filter)
    st.session_state["max_radius_miles"] = int(max_radius_miles)

    # Navigate to results
    with st.spinner("🔍 Searching for providers..."):
        st.switch_page("pages/2_📄_Results.py")

# Help section at bottom
with st.expander("❓ Need Help?"):
    st.markdown("""
    **How to use this search:**
    1. Enter the client's complete address
    2. Choose a search profile or customize your own weights
    3. (Optional) Set advanced filters to refine results
    4. Click "Find Providers" to see recommendations

    **Tips:**
    - Use "Balanced (Recommended)" for most situations
    - "Prioritize Proximity" is best for clients with mobility concerns
    - "Balance Workload" helps distribute cases fairly among providers
    - Advanced filters help narrow results for specific needs

    For more information, visit the [How It Works](/10_🛠️_How_It_Works) page.
    """)
