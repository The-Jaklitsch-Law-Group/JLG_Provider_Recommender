import streamlit as st
import pandas as pd

from src.app_logic import (
    load_application_data,
    apply_time_filtering,
    run_recommendation,
    validate_provider_data,
)
from src.utils.io_utils import get_word_bytes, sanitize_filename

st.set_page_config(page_title="Results", page_icon=":bar_chart:", layout="wide")

# Sidebar navigation
if st.sidebar.button("← New Search", type="secondary", use_container_width=True):
    st.switch_page("app.py")

st.sidebar.divider()
st.sidebar.caption("Current search parameters:")
if "max_radius_miles" in st.session_state:
    st.sidebar.write(f"📍 Radius: {st.session_state['max_radius_miles']} miles")
if "min_referrals" in st.session_state:
    st.sidebar.write(f"📊 Min. referrals: {st.session_state['min_referrals']}")

required_keys = ["user_lat", "user_lon", "alpha", "beta", "min_referrals", "max_radius_miles"]
if any(k not in st.session_state for k in required_keys):
    st.warning("No search parameters found. Redirecting to search.")
    st.switch_page("app.py")

provider_df, detailed_referrals_df = load_application_data()

if st.session_state.get("use_time_filter") and isinstance(
    st.session_state.get("time_period"), list
) and len(st.session_state["time_period"]) == 2:
    start_date, end_date = st.session_state["time_period"]
    provider_df = apply_time_filtering(provider_df, detailed_referrals_df, start_date, end_date)

valid, msg = validate_provider_data(provider_df)
if not valid and msg:
    st.warning(msg)

best = st.session_state.get("last_best")
scored_df = st.session_state.get("last_scored_df")

if best is None or scored_df is None or (isinstance(scored_df, pd.DataFrame) and scored_df.empty):
    best, scored_df = run_recommendation(
        provider_df,
        st.session_state["user_lat"],
        st.session_state["user_lon"],
        min_referrals=st.session_state["min_referrals"],
        max_radius_miles=st.session_state["max_radius_miles"],
        alpha=st.session_state["alpha"],
        beta=st.session_state["beta"],
        gamma=st.session_state.get("gamma", 0.0),
    )
    st.session_state["last_best"] = best
    st.session_state["last_scored_df"] = scored_df

st.title("🎯 Recommended Provider")

if best is None or scored_df is None or (isinstance(scored_df, pd.DataFrame) and scored_df.empty):
    st.warning("⚠️ No providers found matching your criteria. Try adjusting your search parameters.")
    if st.button("← Adjust Search Parameters"):
        st.switch_page("pages/1_Search.py")
    st.stop()

# Top recommendation highlight
provider_name = best.get("Full Name", "Unknown Provider") if isinstance(best, pd.Series) else "Unknown Provider"

st.markdown("### 🌟 Top Recommendation")
st.success(f"**{provider_name}**")

if isinstance(best, pd.Series):
    col1, col2 = st.columns(2)
    
    with col1:
        if "Full Address" in best and best["Full Address"]:
            st.markdown(f"📍 **Address**  \n{best['Full Address']}")
        
        if "Distance (Miles)" in best:
            st.markdown(f"🚗 **Distance**  \n{best['Distance (Miles)']:.1f} miles")
    
    with col2:
        phone_value = None
        for phone_key in ["Work Phone Number", "Work Phone", "Phone Number", "Phone 1"]:
            candidate = best.get(phone_key)
            if candidate:
                phone_value = candidate
                break
        if phone_value:
            st.markdown(f"📞 **Phone**  \n{phone_value}")
        
        if "Referral Count" in best:
            st.markdown(f"📊 **Referrals**  \n{int(best['Referral Count'])} outbound")

st.divider()

# All results table
st.markdown("### 📋 All Matching Providers")
st.caption(f"Showing {len(scored_df)} providers within your search criteria, ranked by best match.")

cols = ["Full Name", "Work Phone Number", "Full Address", "Distance (Miles)", "Referral Count"]
if "Inbound Referral Count" in scored_df.columns:
    cols.append("Inbound Referral Count")
if "Score" in scored_df.columns:
    cols.append("Score")
available = [c for c in cols if c in scored_df.columns]
if available:
    display_df = (
        scored_df[available]
        .drop_duplicates(subset=["Full Name"], keep="first")
        .sort_values(by="Score" if "Score" in available else available[0])
        .reset_index(drop=True)
    )
    display_df.insert(0, "Rank", range(1, len(display_df) + 1))
    
    # Format numeric columns for better readability
    if "Distance (Miles)" in display_df.columns:
        display_df["Distance (Miles)"] = display_df["Distance (Miles)"].round(1)
    if "Score" in display_df.columns:
        display_df["Score"] = display_df["Score"].round(3)
    
    st.dataframe(
        display_df, 
        hide_index=True, 
        use_container_width=True,
        height=400
    )
else:
    st.error("No displayable columns in results.")

st.divider()

# Export section
st.markdown("### 💾 Export")
try:
    base_filename = f"Provider_{sanitize_filename(provider_name)}"
    col1, col2 = st.columns([2, 1])
    with col1:
        st.download_button(
            "📄 Export Top Provider (Word Document)",
            data=get_word_bytes(best),
            file_name=f"{base_filename}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with col2:
        st.caption(f"Export details for {provider_name}")
except Exception as e:
    st.error(f"❌ Export failed: {e}")

# Scoring details in expander
with st.expander("📊 View Scoring Details"):
    st.markdown("**How the recommendation was calculated:**")
    alpha = st.session_state.get("alpha", 0.5)
    beta = st.session_state.get("beta", 0.5)
    gamma = st.session_state.get("gamma", 0.0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Distance Weight", f"{alpha:.0%}")
    with col2:
        st.metric("Load Balancing Weight", f"{beta:.0%}")
    if gamma > 0:
        with col3:
            st.metric("Relationship Weight", f"{gamma:.0%}")
    
    st.latex(
        r"\text{Score} = " + f"{alpha:.2f}" + r" \times \text{Distance} + " 
        + f"{beta:.2f}" + r" \times \text{Load Balance}"
        + (f" + {gamma:.2f}" + r" \times \text{Relationships}" if gamma > 0 else "")
    )
    st.caption("Lower scores indicate better matches. Distance and load balancing are normalized to 0-1 scale.")
