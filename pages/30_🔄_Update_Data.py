import traceback
from pathlib import Path

import streamlit as st

from src.data import process_and_save_cleaned_referrals, process_and_save_preferred_providers, refresh_data_cache

st.set_page_config(page_title="Update Data", page_icon="🗂️", layout="wide")

st.markdown("### 🔄 Update Referral Data")

st.markdown(
    """
Use this page to upload new referral data and automatically refresh the optimized datasets that power the app.
"""
)

st.markdown(
    """
⚠️ ***PLEASE NOTE:*** ⚠️
The data refresh here works only on a local machine - it will not function in the cloud environment.
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
        with st.spinner("Processing uploaded file and generating optimized Parquet files…"):
            # Process directly from memory without saving raw file to disk
            file_bytes = uploaded_file.getbuffer()
            summary = process_and_save_cleaned_referrals(
                file_bytes, 
                Path("data/processed"), 
                filename=uploaded_file.name
            )
            refresh_data_cache()

        st.success("✅ Upload complete and cleaned datasets refreshed.")
        st.caption(f"Processed file: `{uploaded_file.name}` ({uploaded_file.size:,} bytes)")

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

st.markdown("---")

st.markdown("#### Upload Preferred Providers File (Excel)")
st.markdown(
    """
Upload the preferred providers list with contact information. Records missing latitude and/or longitude 
will be identified and excluded from the cleaned dataset.
"""
)

preferred_providers_file = st.file_uploader(
    "Upload preferred providers data (Excel format)",
    type=["xlsx", "xls"],
    help="Upload an Excel file with preferred provider contact information",
    key="preferred_providers_uploader"
)

if preferred_providers_file is not None:
    try:
        with st.spinner("Processing preferred providers file…"):
            # Process directly from memory without saving raw file to disk
            file_bytes = preferred_providers_file.getbuffer()
            summary = process_and_save_preferred_providers(
                file_bytes, 
                Path("data/processed"), 
                filename=preferred_providers_file.name
            )
            refresh_data_cache()

        st.success("✅ Preferred providers upload complete and dataset refreshed.")
        st.caption(f"Processed file: `{preferred_providers_file.name}` ({preferred_providers_file.size:,} bytes)")

        # Display metrics
        metrics = st.columns(3)
        metrics[0].metric(label="Total records", value=f"{summary.total_count:,}")
        metrics[1].metric(label="Cleaned records", value=f"{summary.cleaned_count:,}")
        metrics[2].metric(label="Missing geo data", value=f"{summary.missing_geo_count:,}")

        # Show completion percentage
        if summary.total_count > 0:
            completion_rate = (summary.cleaned_count / summary.total_count) * 100
            st.progress(completion_rate / 100)
            st.caption(f"Data completeness: {completion_rate:.1f}%")

        # Display warnings if any
        if summary.warnings:
            for warning in summary.warnings:
                st.warning(warning)

        # Show records missing geo data if any
        if summary.missing_geo_count > 0 and summary.missing_records is not None:
            st.markdown("#### Records Missing Geographic Data")
            st.warning(
                f"The following {summary.missing_geo_count} record(s) were excluded due to missing "
                "latitude and/or longitude information:"
            )
            
            # Display the records (limit to reasonable number for display)
            display_records = summary.missing_records
            if len(display_records) > 50:
                st.caption("Showing the first 50 records")
                display_records = display_records.head(50)
            
            st.dataframe(display_records, width='stretch')
            
            # Optionally offer to download the missing records
            if st.button("📥 Download Missing Records as Excel", key="download_missing_geo"):
                try:
                    # Create Excel file in memory
                    from io import BytesIO
                    excel_buffer = BytesIO()
                    summary.missing_records.to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Missing Records",
                        data=excel_buffer.getvalue(),
                        file_name="Preferred_Providers_Missing_LatLong.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Failed to create Excel download: {e}")

    except Exception:
        st.error("Failed to process the preferred providers file.")
        st.code(traceback.format_exc())

st.markdown("---")

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
