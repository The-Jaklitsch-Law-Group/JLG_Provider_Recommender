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

st.title("Provider Search")
st.caption("Enter client address and preferences, then run search.")

with st.spinner("Loading provider data..."):
    provider_df, detailed_referrals_df = load_application_data()

if provider_df.empty:
    st.warning("No provider data loaded. Please verify data files.")

data_valid, data_msg = validate_provider_data(provider_df) if not provider_df.empty else (False, "")
if data_msg and not data_valid:
    st.warning(data_msg)

street = str(st.text_input("Street", st.session_state.get("street", "14350 Old Marlboro Pike") or ""))
city = str(st.text_input("City", st.session_state.get("city", "Upper Marlboro") or ""))
state = str(st.text_input("State", st.session_state.get("state", "MD") or ""))
zipcode = str(st.text_input("Zip", st.session_state.get("zipcode", "20772") or ""))

full_address = f"{street}, {city}, {state} {zipcode}".strip(", ")
if len(full_address) > 5:
    ok, msg = validate_address(full_address)
    if ok:
        st.caption("Address format OK.")
    elif msg:
        st.warning(msg)

has_inbound = ("Inbound Referral Count" in provider_df.columns) if not provider_df.empty else False

st.subheader("Scoring Weights")
distance_weight = st.slider(
    "Distance Importance",
    0.0,
    1.0,
    st.session_state.get("distance_weight", 0.4 if has_inbound else 0.6),
    0.05,
)
outbound_weight = st.slider(
    "Outbound Referral Importance",
    0.0,
    1.0,
    st.session_state.get("outbound_weight", 0.4),
    0.05,
)
inbound_weight = 0.0
if has_inbound:
    inbound_weight = st.slider(
        "Inbound Referral Importance",
        0.0,
        1.0,
        st.session_state.get("inbound_weight", 0.2),
        0.05,
    )
total = distance_weight + outbound_weight + (inbound_weight if has_inbound else 0)
if total == 0:
    st.error("At least one weight must be > 0.")
alpha = distance_weight / total if total else 0.5
beta = outbound_weight / total if total else 0.5
gamma = inbound_weight / total if has_inbound and total else 0.0
st.caption(
    f"Normalized Weights: Distance {alpha:.2f} | Outbound {beta:.2f}"
    + (f" | Inbound {gamma:.2f}" if has_inbound else "")
)

min_referrals = st.number_input(
    "Minimum Outbound Referral Count", 0, value=st.session_state.get("min_referrals", 0)
)
time_period = st.date_input(
    "Time Period",
    value=st.session_state.get(
        "time_period", [dt.date.today() - dt.timedelta(days=365), dt.date.today()]
    ),
)
use_time_filter = st.checkbox(
    "Enable time-based filtering", value=st.session_state.get("use_time_filter", True)
)
max_radius_miles = st.slider(
    "Maximum Radius (miles)", 1, 200, st.session_state.get("max_radius_miles", 25)
)

if st.button("Search", type="primary"):
    addr_valid, addr_msg = validate_address_input(street, city, state, zipcode)
    if not addr_valid:
        st.error("Fix address issues before searching.")
        if addr_msg:
            st.info(addr_msg)
        st.stop()
    if not GEOCODE_AVAILABLE:
        st.error("Geocoding unavailable (geopy not installed).")
        st.stop()
    coords = geocode_address_with_cache(full_address) if GEOCODE_AVAILABLE else None
    if not coords:
        st.error("Could not geocode address.")
        st.stop()
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
    st.session_state["distance_weight"] = float(distance_weight)
    st.session_state["outbound_weight"] = float(outbound_weight)
    st.session_state["inbound_weight"] = float(inbound_weight)
    st.session_state["min_referrals"] = int(min_referrals)
    st.session_state["time_period"] = time_period
    st.session_state["use_time_filter"] = bool(use_time_filter)
    st.session_state["max_radius_miles"] = int(max_radius_miles)
    st.switch_page("pages/2_📄_Results.py")
