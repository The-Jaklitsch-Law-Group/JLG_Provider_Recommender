import traceback
from pathlib import Path

import streamlit as st

from src.data import process_and_save_cleaned_referrals, process_and_save_preferred_providers, refresh_data_cache
from src.utils.s3_client import S3DataClient, list_s3_files, get_latest_s3_file

st.set_page_config(page_title="Update Data", page_icon="🗂️", layout="centered")

st.markdown("### 🔄 Update Referral Data")

st.markdown(
    """
Use this page to upload new referral data and automatically refresh the optimized datasets that power the app.
"""
)

# Check S3 configuration
s3_client = S3DataClient()
s3_enabled = s3_client.is_configured()

# default effective folder map (may be overridden by session state when s3 is enabled)
effective_folder_map = None

if s3_enabled:
    st.info("✅ AWS S3 is configured. You can pull data from S3 or upload files manually.")
    # Allow advanced users to override the S3 folder mapping
    # Persist overrides in session_state so they survive reruns
    effective_folder_map = st.session_state.get('s3_folder_map', None)

    with st.expander("S3 Folder Overrides (advanced)", expanded=False):
        with st.form("s3_folder_form"):
            # defaults come from the currently-initialized client (which reads config)
            top_default = getattr(s3_client, 'folder_map', {}).get('top_folder', '')
            ref_default = getattr(s3_client, 'folder_map', {}).get('referrals_folder', '')
            prov_default = getattr(s3_client, 'folder_map', {}).get('preferred_providers_folder', '')

            top_in = st.text_input("Top folder", value=top_default, help="Top-level S3 folder (e.g. jaklitschfvdomo)")
            referrals_in = st.text_input("Referrals subfolder", value=ref_default, help="Subfolder for referrals data (e.g. 990046944)")
            providers_in = st.text_input("Preferred providers subfolder", value=prov_default, help="Subfolder for preferred providers data (e.g. 990047553)")

            submitted = st.form_submit_button("Apply folder overrides")
            if submitted:
                # normalize empty strings to None to fall back to defaults/config
                fm = {
                    'top_folder': top_in.strip() if top_in and top_in.strip() else '',
                    'referrals_folder': referrals_in.strip() if referrals_in and referrals_in.strip() else '',
                    'preferred_providers_folder': providers_in.strip() if providers_in and providers_in.strip() else '',
                }
                st.session_state['s3_folder_map'] = fm
                effective_folder_map = fm
                st.success("Folder overrides applied — these will be used for subsequent S3 operations on this page")

        # Option to clear overrides
        if st.button("Clear folder overrides"):
            if 's3_folder_map' in st.session_state:
                del st.session_state['s3_folder_map']
            effective_folder_map = None
            st.info("Folder overrides cleared — defaults/config will be used")
else:
    st.warning(
        "⚠️ AWS S3 is not configured. Only manual file upload is available. "
        "Configure S3 credentials in secrets to enable automatic data pull."
    )

# S3 Data Pull Section
if s3_enabled:
    st.markdown("---")
    st.markdown("#### ⚡ On-demand S3 Refresh")
    st.markdown(
        """
Use this button to pull the latest referrals and preferred providers files from S3 and
process them immediately. This is handy when an external system drops new files into
the S3 folders and you want to update the app without manually selecting individual files.

Note: This will attempt to download and process both referrals and preferred providers
using the most recently modified Excel file found in each folder.
        """
    )

    if st.button("🔁 Pull & Refresh Latest from S3", key="s3_pull_all"):
        try:
            with st.spinner("Pulling latest files from S3 and processing…"):
                # Create an operational client that respects any folder_map overrides
                op_client = S3DataClient(folder_map=effective_folder_map)

                # Referrals
                referrals_name = None
                providers_name = None
                referrals_result = op_client.download_latest_file('referrals')
                if referrals_result:
                    referrals_bytes, referrals_name = referrals_result
                    summary_ref = process_and_save_cleaned_referrals(
                        referrals_bytes,
                        Path("data/processed"),
                        filename=referrals_name,
                    )
                else:
                    summary_ref = None

                # Preferred providers
                providers_result = op_client.download_latest_file('preferred_providers')
                if providers_result:
                    providers_bytes, providers_name = providers_result
                    summary_prov = process_and_save_preferred_providers(
                        providers_bytes,
                        Path("data/processed"),
                        filename=providers_name,
                    )
                else:
                    summary_prov = None

                # Refresh cached datasets
                refresh_data_cache()

            # Report results
            if summary_ref:
                st.success(f"✅ Referrals updated from `{referrals_name}`")
                cols = st.columns(3)
                cols[0].metric(label="Inbound rows", value=f"{summary_ref.inbound_count:,}")
                cols[1].metric(label="Outbound rows", value=f"{summary_ref.outbound_count:,}")
                cols[2].metric(label="All referrals", value=f"{summary_ref.all_count:,}")
            else:
                st.warning("No referrals file found in S3 to update.")

            if summary_prov:
                st.success(f"✅ Preferred providers updated from `{providers_name}`")
                cols = st.columns(3)
                cols[0].metric(label="Total records", value=f"{summary_prov.total_count:,}")
                cols[1].metric(label="Cleaned records", value=f"{summary_prov.cleaned_count:,}")
                cols[2].metric(label="Missing geo", value=f"{summary_prov.missing_geo_count:,}")
            else:
                st.warning("No preferred providers file found in S3 to update.")

        except Exception as e:
            st.error(f"Failed to pull & refresh from S3: {e}")
            st.code(traceback.format_exc())

    st.markdown("---")
    st.markdown("#### 📥 Pull Data from AWS S3")
    st.markdown("Automatically download and process the latest files from your S3 bucket.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Referrals Data**")
        # Use the cached helper but pass the overrides so cache keys separate per mapping
        referrals_files = list_s3_files('referrals', folder_map=effective_folder_map)
        
        if referrals_files:
            latest_referral_file, latest_referral_date = referrals_files[0]
            st.caption(f"Latest file: `{latest_referral_file}`")
            st.caption(f"Modified: {latest_referral_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if st.button("📥 Pull Latest Referrals from S3", key="s3_pull_referrals"):
                try:
                    with st.spinner("Downloading and processing data from S3..."):
                        op_client = S3DataClient(folder_map=effective_folder_map)
                        file_bytes = op_client.download_file('referrals', latest_referral_file)
                        if file_bytes:
                            summary = process_and_save_cleaned_referrals(
                                file_bytes,
                                Path("data/processed"),
                                filename=latest_referral_file
                            )
                            refresh_data_cache()
                            
                            st.success(f"✅ Successfully pulled and processed `{latest_referral_file}` from S3")
                            
                            metrics = st.columns(3)
                            metrics[0].metric(label="Inbound rows", value=f"{summary.inbound_count:,}")
                            metrics[1].metric(label="Outbound rows", value=f"{summary.outbound_count:,}")
                            metrics[2].metric(label="All referrals", value=f"{summary.all_count:,}")
                        else:
                            st.error("Failed to download file from S3")
                except Exception as e:
                    st.error(f"Failed to pull data from S3: {e}")
                    st.code(traceback.format_exc())
        else:
            st.caption("No files found in S3 referrals folder")
    
    with col2:
        st.markdown("**Preferred Providers Data**")
        providers_files = list_s3_files('preferred_providers', folder_map=effective_folder_map)
        
        if providers_files:
            latest_provider_file, latest_provider_date = providers_files[0]
            st.caption(f"Latest file: `{latest_provider_file}`")
            st.caption(f"Modified: {latest_provider_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if st.button("📥 Pull Latest Providers from S3", key="s3_pull_providers"):
                try:
                    with st.spinner("Downloading and processing data from S3..."):
                        op_client = S3DataClient(folder_map=effective_folder_map)
                        file_bytes = op_client.download_file('preferred_providers', latest_provider_file)
                        if file_bytes:
                            summary = process_and_save_preferred_providers(
                                file_bytes,
                                Path("data/processed"),
                                filename=latest_provider_file
                            )
                            refresh_data_cache()
                            
                            st.success(f"✅ Successfully pulled and processed `{latest_provider_file}` from S3")
                            
                            metrics = st.columns(3)
                            metrics[0].metric(label="Total records", value=f"{summary.total_count:,}")
                            metrics[1].metric(label="Cleaned records", value=f"{summary.cleaned_count:,}")
                            metrics[2].metric(label="Missing geo", value=f"{summary.missing_geo_count:,}")
                        else:
                            st.error("Failed to download file from S3")
                except Exception as e:
                    st.error(f"Failed to pull data from S3: {e}")
                    st.code(traceback.format_exc())
        else:
            st.caption("No files found in S3 providers folder")

st.markdown("---")

st.markdown("#### 📤 Upload Raw Referral File (Excel)")
st.markdown("Upload a file manually if S3 is not configured or if you want to process a specific file.")
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

st.markdown("#### 📤 Upload Preferred Providers File (Excel)")
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
