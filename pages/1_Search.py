import datetime as dt
import pandas as pd
import streamlit as st

from src.app_logic import load_application_data, validate_provider_data
from src.utils.addressing import validate_address, validate_address_input

try:
    from src.utils.geocoding import geocode_address_with_cache
    GEOCODE_AVAILABLE = True
except Exception:
    GEOCODE_AVAILABLE = False

st.set_page_config(page_title="Search", page_icon=":mag:", layout="wide")

st.title("🔍 Provider Search")
st.markdown(
    """
    Find the best provider for your client based on their location and your preferences.
    The system recommends providers by balancing proximity, workload, and referral relationships.
    """
)

with st.spinner("Loading provider data..."):
    provider_df, detailed_referrals_df = load_application_data()

if provider_df.empty:
    st.warning("No provider data loaded. Please verify data files.")

data_valid, data_msg = validate_provider_data(provider_df) if not provider_df.empty else (False, "")
if data_msg and not data_valid:
    st.warning(data_msg)

st.divider()

# Client Address Section
st.subheader("📍 Client Address")
st.caption("Enter the client's address to find nearby providers.")

col1, col2 = st.columns([3, 1])
with col1:
    street = str(st.text_input("Street Address", st.session_state.get("street", "14350 Old Marlboro Pike") or "", placeholder="123 Main Street"))
with col2:
    zipcode = str(st.text_input("ZIP Code", st.session_state.get("zipcode", "20772") or "", placeholder="20772"))

col3, col4 = st.columns(2)
with col3:
    city = str(st.text_input("City", st.session_state.get("city", "Upper Marlboro") or "", placeholder="City"))
with col4:
    state = str(st.text_input("State", st.session_state.get("state", "MD") or "", placeholder="MD"))

full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
if len(full_address) > 5:
    ok, msg = validate_address(full_address)
    if ok:
        st.success("✓ Address format looks good")
    elif msg:
        st.warning(f"⚠️ {msg}")

has_inbound = ("Inbound Referral Count" in provider_df.columns) if not provider_df.empty else False

st.divider()

# Preferences Section
st.subheader("⚙️ Search Preferences")

# Simple preferences first
max_radius_miles = st.slider(
    "Search Radius (miles)",
    1, 200, 
    st.session_state.get("max_radius_miles", 25),
    help="Only include providers within this distance from the client's address."
)

min_referrals = st.number_input(
    "Minimum Experience (referrals)",
    0, 
    value=st.session_state.get("min_referrals", 0),
    help="Only show providers with at least this many outbound referrals."
)

# Advanced scoring options in expander
with st.expander("🎯 Advanced: Scoring Preferences", expanded=False):
    st.markdown(
        """
        **Customize how providers are ranked:**
        - **Distance**: Prioritize providers closer to the client
        - **Load Balancing**: Prioritize providers with fewer recent referrals
        """ + (
        "- **Mutual Relationships**: Prioritize providers with existing referral relationships"
        if has_inbound else ""
        )
    )
    
    st.caption("💡 Tip: Adjust these sliders to change what matters most. They'll be automatically balanced.")
    
    distance_weight = st.slider(
        "Distance Priority",
        0.0,
        1.0,
        st.session_state.get("distance_weight", 0.4 if has_inbound else 0.6),
        0.05,
        help="Higher values prioritize providers closer to the client."
    )
    outbound_weight = st.slider(
        "Load Balancing Priority",
        0.0,
        1.0,
        st.session_state.get("outbound_weight", 0.4),
        0.05,
        help="Higher values prioritize providers with fewer recent referrals."
    )
    inbound_weight = 0.0
    if has_inbound:
        inbound_weight = st.slider(
            "Mutual Relationship Priority",
            0.0,
            1.0,
            st.session_state.get("inbound_weight", 0.2),
            0.05,
            help="Higher values prioritize providers with existing referral relationships."
        )
    
    total = distance_weight + outbound_weight + (inbound_weight if has_inbound else 0)
    if total == 0:
        st.error("⚠️ At least one priority must be greater than 0.")
    else:
        alpha = distance_weight / total
        beta = outbound_weight / total
        gamma = inbound_weight / total if has_inbound else 0.0
        
        st.info(
            f"**Normalized weights:** Distance {alpha:.0%} • Load Balancing {beta:.0%}"
            + (f" • Relationships {gamma:.0%}" if has_inbound else "")
        )

# Time filtering in expander
with st.expander("📅 Advanced: Time-Based Filtering", expanded=False):
    st.markdown("Filter referrals by date range to focus on recent activity.")
    
    use_time_filter = st.checkbox(
        "Enable time-based filtering",
        value=st.session_state.get("use_time_filter", True),
        help="When enabled, only counts referrals within the selected date range."
    )
    time_period = st.date_input(
        "Referral Date Range",
        value=st.session_state.get(
            "time_period", [dt.date.today() - dt.timedelta(days=365), dt.date.today()]
        ),
        help="Only count referrals that occurred within this date range."
    )

st.divider()

st.divider()

# Search button with prominent styling
if st.button("🔍 Find Best Provider", type="primary", use_container_width=True):
    addr_valid, addr_msg = validate_address_input(street, city, state, zipcode)
    if not addr_valid:
        st.error("❌ Please fix the address issues before searching.")
        if addr_msg:
            st.info(addr_msg)
        st.stop()
    if not GEOCODE_AVAILABLE:
        st.error("❌ Geocoding service unavailable (geopy not installed).")
        st.stop()
    
    with st.spinner("🌍 Locating address..."):
        coords = geocode_address_with_cache(full_address) if GEOCODE_AVAILABLE else None
    
    if not coords:
        st.error("❌ Could not find the address. Please check and try again.")
        st.stop()
    
    user_lat, user_lon = coords
    
    # Store search parameters
    st.session_state["street"] = street
    st.session_state["city"] = city
    st.session_state["state"] = state
    st.session_state["zipcode"] = zipcode
    st.session_state["user_lat"] = float(user_lat)
    st.session_state["user_lon"] = float(user_lon)
    st.session_state["alpha"] = float(alpha)
    st.session_state["beta"] = float(beta)
    st.session_state["gamma"] = float(gamma)
    st.session_state["distance_weight"] = float(distance_weight)
    st.session_state["outbound_weight"] = float(outbound_weight)
    st.session_state["inbound_weight"] = float(inbound_weight)
    st.session_state["min_referrals"] = int(min_referrals)
    st.session_state["time_period"] = time_period
    st.session_state["use_time_filter"] = bool(use_time_filter)
    st.session_state["max_radius_miles"] = int(max_radius_miles)
    
    st.success("✅ Address found! Redirecting to results...")
    st.switch_page("pages/2_Results.py")
