import pandas as pd
import streamlit as st

from src.app_logic import apply_time_filtering, load_application_data, run_recommendation, validate_provider_data
from src.utils.io_utils import get_word_bytes, sanitize_filename

st.set_page_config(page_title="Results", page_icon=":bar_chart:", layout="wide")

# Sidebar navigation
if st.sidebar.button("← New Search", type="secondary", width="stretch"):
    st.switch_page("pages/1_🔎_Search.py")

st.sidebar.divider()
st.sidebar.caption("**Your Search Criteria:**")
if "max_radius_miles" in st.session_state:
    st.sidebar.write(f"📍 Radius: {st.session_state['max_radius_miles']} miles")
if "min_referrals" in st.session_state:
    st.sidebar.write(f"📊 Min. Experience: {st.session_state['min_referrals']} cases")
if "street" in st.session_state and "city" in st.session_state:
    st.sidebar.write(f"🏠 From: {st.session_state.get('city', 'N/A')}, {st.session_state.get('state', 'N/A')}")

required_keys = ["user_lat", "user_lon", "alpha", "beta", "min_referrals", "max_radius_miles"]
if any(k not in st.session_state for k in required_keys):
    st.warning("No search parameters found. Redirecting to search.")
    st.switch_page("pages/1_🔎_Search.py")

provider_df, detailed_referrals_df = load_application_data()

if (
    st.session_state.get("use_time_filter")
    and isinstance(st.session_state.get("time_period"), list)
    and len(st.session_state["time_period"]) == 2
):
    start_date, end_date = st.session_state["time_period"]
    provider_df = apply_time_filtering(provider_df, detailed_referrals_df, start_date, end_date)

valid, msg = validate_provider_data(provider_df)
if not valid and msg:
    # st.warning(msg)
    pass

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
        # Prefer normalized preferred weight when available (preferred_norm); fall back to preferred_weight
        preferred_weight=st.session_state.get("preferred_norm", st.session_state.get("preferred_weight", 0.1)),
    )
    st.session_state["last_best"] = best
    st.session_state["last_scored_df"] = scored_df

st.title("🎯 Provider Recommendations")

if best is None or scored_df is None or (isinstance(scored_df, pd.DataFrame) and scored_df.empty):
    st.warning("⚠️ No providers matched your search criteria.")
    st.info("💡 Try adjusting your filters or expanding the search radius.")
    st.stop()

# Top recommendation in a prominent card
st.subheader("✨ Best Match")

provider_name = best.get("Full Name", "Unknown Provider") if isinstance(best, pd.Series) else "Unknown Provider"

# Create a nice card-like display for the top provider
with st.container():
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"### 🧑‍⚕️ {provider_name}")

        if isinstance(best, pd.Series):
            # Display key information
            info_items = []

            if "Full Address" in best and best["Full Address"]:
                info_items.append(("🏥 Address", best["Full Address"]))

            # Find phone number
            phone_value = None
            for phone_key in ["Work Phone Number", "Work Phone", "Phone Number", "Phone 1"]:
                candidate = best.get(phone_key)
                if candidate:
                    phone_value = candidate
                    break
            if phone_value:
                info_items.append(("📞 Phone", phone_value))

            if "Distance (Miles)" in best:
                info_items.append(("📍 Distance", f"{best['Distance (Miles)']:.1f} miles"))

            if "Referral Count" in best:
                info_items.append(("📊 Cases Handled", int(best["Referral Count"])))

            # Display in a clean format
            for label, value in info_items:
                st.write(f"**{label}:** {value}")

    with col2:
        # Key metrics
        if isinstance(best, pd.Series):
            if "Score" in best:
                st.metric("Match Score", f"{best['Score']:.3f}", help="Lower scores indicate better matches")

            if "Preferred Provider" in best:
                is_preferred = best["Preferred Provider"]
                if is_preferred:
                    st.success("⭐ Preferred Provider")

st.divider()

# Export button in a prominent position
try:
    base_filename = f"Provider_{sanitize_filename(provider_name)}"
    st.download_button(
        "📄 Export to Word Document",
        data=get_word_bytes(best),
        file_name=f"{base_filename}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=False,
        type="primary",
    )
except Exception as e:
    st.error(f"❌ Export failed: {e}")

st.divider()

# All results in a clean table
st.subheader("📋 All Matching Providers")

cols = ["Full Name", "Work Phone Number", "Full Address", "Distance (Miles)", "Referral Count"]
cols.append("Preferred Provider")
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

    # Format boolean Preferred Provider column for better display
    if "Preferred Provider" in display_df.columns:
        display_df = display_df.copy()
        display_df["Preferred Provider"] = display_df["Preferred Provider"].map({True: "⭐ Yes", False: "No"})

    # Round distance to 1 decimal place for cleaner display
    if "Distance (Miles)" in display_df.columns:
        display_df["Distance (Miles)"] = display_df["Distance (Miles)"].round(1)

    # Round score to 3 decimal places
    if "Score" in display_df.columns:
        display_df["Score"] = display_df["Score"].round(3)

    display_df.insert(0, "Rank", range(1, len(display_df) + 1))

    st.caption(f"Showing {len(display_df)} provider(s) matching your criteria")
    st.dataframe(display_df, hide_index=True, width="stretch", height=400)
else:
    st.error("❌ No displayable columns in results.")

# Scoring details in expander at the bottom
with st.expander("📊 How Scoring Works"):
    alpha = st.session_state.get("alpha", 0.5)
    beta = st.session_state.get("beta", 0.5)
    gamma = st.session_state.get("gamma", 0.0)
    pref = st.session_state.get("preferred_norm", st.session_state.get("preferred_weight", 0.1))

    st.markdown(
        """
    **Scoring Formula:**

    Providers are scored using a weighted combination of factors. **Lower scores indicate better matches.**
    """
    )

    formula_parts = [f"**Distance** × {alpha:.2f}", f"**Outbound Referrals** × {beta:.2f}"]
    if gamma > 0:
        formula_parts.append(f"**Inbound Referrals** × {gamma:.2f}")
    formula_parts.append(f"**Preferred Status** × {pref:.2f}")

    st.markdown("Score = " + " + ".join(formula_parts))

    st.markdown(
        """
    **What this means:**
    - Each factor is normalized to a 0-1 scale
    - Weights are automatically adjusted to total 100%
    - The provider with the lowest score is your best match
    """
    )
