import pandas as pd
import streamlit as st

from src.utils.cleaning import validate_provider_data

st.set_page_config(page_title="Data Quality", page_icon="📊", layout="wide")

st.markdown("### 📊 Data Quality Monitoring")

st.markdown(
    """
Monitor the quality and completeness of provider data used in recommendations.
Use this dashboard to identify data issues and track system health.
"""
)

st.info("💡 Tip: For detailed analytics, run: `streamlit run data_dashboard.py`")

# We avoid re-loading heavy data here; rely on app cache if available
from src.data.ingestion import load_provider_data  # noqa: E402

provider_df = load_provider_data()

st.markdown("#### Quick Quality Check")
if not provider_df.empty:
    data_valid, data_message = validate_provider_data(provider_df)

    if data_valid:
        st.success("✅ Provider data quality is good!")
    else:
        st.warning("⚠️ Provider data has some quality issues.")

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

    with st.expander("📋 Data Quality Details", expanded=False):
        st.markdown(data_message)
else:
    st.error("❌ No provider data available. Please check data files.")
