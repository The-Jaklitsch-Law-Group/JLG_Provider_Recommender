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

if st.sidebar.button("🡄 New Search", type="secondary"):
    # Switch back to the Search page. Using the main `app.py` filename here
    # won't work because `app.py` is not registered as a pages entry in
    # Streamlit's page registry (we intentionally excluded it to avoid
    # a recursion/import loop). Pointing at the actual page file ensures
    # `st.switch_page` can find and navigate to it.
    st.switch_page("pages/1_🔎_Search.py")

required_keys = ["user_lat", "user_lon", "alpha", "beta", "min_referrals", "max_radius_miles"]
if any(k not in st.session_state for k in required_keys):
    st.warning("No search parameters found. Redirecting to search.")
    st.switch_page("pages/1_🔎_Search.py")

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

st.title("Recommended Provider")

if best is None or scored_df is None or (isinstance(scored_df, pd.DataFrame) and scored_df.empty):
    st.warning("No providers met the criteria.")
    st.stop()

provider_name = "".join(["🧑‍⚕️ ", (best.get("Full Name", "Unknown Provider") if isinstance(best, pd.Series) else "Unknown Provider")])
st.subheader(provider_name)

if isinstance(best, pd.Series):
    if "Full Address" in best and best["Full Address"]:
        st.write("🏥 Address:", best["Full Address"])
    phone_value = None
    for phone_key in ["Work Phone Number", "Work Phone", "Phone Number", "Phone 1"]:
        candidate = best.get(phone_key)
        if candidate:
            phone_value = candidate
            break
    if phone_value:
        st.write("📞 Phone:", phone_value)

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
    st.dataframe(display_df, hide_index=True, width='stretch')
else:
    st.error("No displayable columns in results.")

try:
    base_filename = f"Provider_{sanitize_filename(provider_name)}"
    st.download_button(
        "Export Selected Provider (Word)",
        data=get_word_bytes(best),
        file_name=f"{base_filename}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
except Exception as e:
    st.error(f"Export failed: {e}")

with st.expander("Scoring Details"):
    alpha = st.session_state.get("alpha", 0.5)
    beta = st.session_state.get("beta", 0.5)
    gamma = st.session_state.get("gamma", 0.0)
    st.markdown(
        f"Weighted score = Distance*{alpha:.2f} + Outbound*{beta:.2f}" + (f" + Inbound*{gamma:.2f}" if gamma > 0 else "")
    )
