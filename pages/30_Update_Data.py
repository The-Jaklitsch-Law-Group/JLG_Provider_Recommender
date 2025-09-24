import traceback
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Update Data", page_icon="🗂️", layout="wide")

st.markdown("### 🔄 Update Referral Data")

st.markdown(
    """
Use this page to upload new referral data and refresh cached datasets.
This will not automatically process raw files into cleaned Parquet; follow the manual step below if needed.
"""
)

st.info(
    "After uploading, run your existing cleaning pipeline to regenerate Parquet files in `data/processed/` (see `prepare_contacts/contact_cleaning.ipynb`)."
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

        st.success(f"✅ File uploaded to: {file_path}")
        st.caption(f"Size: {uploaded_file.size:,} bytes")
        st.markdown(
            """
**Next step (manual processing):**
- Open and run `prepare_contacts/contact_cleaning.ipynb` to transform the raw Excel into cleaned Parquet files under `data/processed/`.
- Alternatively, use your established ETL script if you have one.
- Return to this app and use the button below to clear cache and reload.
"""
        )
    except Exception:
        st.error("Failed to save the uploaded file.")
        st.code(traceback.format_exc())

st.markdown("#### Clear Cached Data")
if st.button("🔄 Clear cache and reload data"):
    try:
        st.cache_data.clear()
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

st.markdown("---")
st.markdown(
    "Need analytics? Launch the separate dashboard with: `streamlit run data_dashboard.py`"
)
