import traceback
from pathlib import Path

import streamlit as st

from src.data import process_and_save_cleaned_referrals, refresh_data_cache

st.set_page_config(page_title="Update Data", page_icon="🗂️", layout="wide")

st.markdown("### 🔄 Update Referral Data")

st.markdown(
    """
Use this page to upload new referral data and automatically refresh the optimized datasets that power the app.
"""
)

st.info(
    "Uploads now trigger the cleaning pipeline automatically and refresh the Parquet files in `data/processed/`."
)

st.markdown("#### Upload Raw Referral File (Excel)")
uploaded_file = st.file_uploader(
    "Upload new referral data (Excel format)",
    type=["xlsx", "xls"],
    help="Upload an Excel export with referrals and provider info",
)

if uploaded_file is not None:
    try:
        raw_data_path = Path("data/raw")
        raw_data_path.mkdir(exist_ok=True, parents=True)

        file_path = raw_data_path / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Cleaning data and regenerating optimized Parquet files…"):
            summary = process_and_save_cleaned_referrals(file_path, Path("data/processed"))
            refresh_data_cache()

        st.success("✅ Upload complete and cleaned datasets refreshed.")
        st.caption(f"Raw file saved to `{file_path}` ({uploaded_file.size:,} bytes)")

        metrics = st.columns(3)
        metrics[0].metric(label="Inbound rows", value=f"{summary.inbound_count:,}")
        metrics[1].metric(label="Outbound rows", value=f"{summary.outbound_count:,}")
        metrics[2].metric(label="All referrals", value=f"{summary.all_count:,}")

        if summary.skipped_configs:
            st.warning(
                "Skipped sections during processing: " + ", ".join(summary.skipped_configs)
            )

        if summary.warnings:
            for message in summary.warnings:
                st.info(message)

        if summary.issue_records:
            st.markdown("#### Records Requiring Attention")
            for key, issue_df in summary.issue_records.items():
                display_name = key.replace("_", " ").title()
                total_rows = len(issue_df)
                st.markdown(f"**{display_name}** — {total_rows} record(s) flagged")
                if total_rows > 200:
                    st.caption("Showing the first 200 rows")
                    st.dataframe(issue_df.head(200))
                else:
                    st.dataframe(issue_df)
    except Exception:
        st.error("Failed to save the uploaded file.")
        st.code(traceback.format_exc())

st.markdown("#### Clear Cached Data")
if st.button("🔄 Clear cache and reload data"):
    try:
        refresh_data_cache()
        # Clear any time filter info flags to avoid stale notices
        keys_to_remove = [
            key for key in list(st.session_state.keys())
            if isinstance(key, str) and key.startswith("time_filter_msg_")
        ]
        for key in keys_to_remove:
            del st.session_state[key]
        st.success("Cache cleared. The app will reload data on next access.")
        st.rerun()
    except Exception:
        st.error("Could not clear cache.")
        st.code(traceback.format_exc())

# st.markdown("---")
# st.markdown(
#     "Need analytics? Launch the separate dashboard with: `streamlit run data_dashboard.py`"
# )
