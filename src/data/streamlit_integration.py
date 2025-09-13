"""
Streamlit Integration for Data Preparation

This module provides Streamlit UI components for triggering and monitoring
the data preparation process from the notebook-based workflow.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from src.data.preparation_enhanced import DataPreparationManager, process_referral_data


def show_data_preparation_ui():
    """
    Main Streamlit UI for data preparation.
    This can be called from the main Streamlit app.
    """
    st.header("🔧 Data Preparation & Cleaning")
    st.markdown("Process and clean referral data using the enhanced notebook-based workflow.")

    # Create tabs for different aspects
    tab1, tab2, tab3 = st.tabs(["📤 Process Data", "📊 View Results", "⚙️ Settings"])

    with tab1:
        show_processing_tab()

    with tab2:
        show_results_tab()

    with tab3:
        show_settings_tab()


def show_processing_tab():
    """Show the data processing interface."""
    st.subheader("Upload and Process Data")

    # File upload options
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Option 1: Upload New File")
        uploaded_file = st.file_uploader(
            "Choose Excel file", type=["xlsx", "xls"], help="Upload the full referrals Excel file for processing"
        )

    with col2:
        st.markdown("### Option 2: Use Existing File")
        data_dir = Path("data")
        raw_dir = data_dir / "raw"

        if raw_dir.exists():
            existing_files = list(raw_dir.glob("*.xlsx")) + list(raw_dir.glob("*.xls"))
            if existing_files:
                selected_file = st.selectbox(
                    "Select existing file:",
                    options=[None] + existing_files,
                    format_func=lambda x: "Choose file..." if x is None else x.name,
                )
            else:
                st.info("No Excel files found in data/raw directory")
                selected_file = None
        else:
            st.info("data/raw directory not found")
            selected_file = None

    # Processing button and options
    st.markdown("### Processing Options")

    col1, col2 = st.columns(2)
    with col1:
        run_tests = st.checkbox("Run integration tests", value=True)
        generate_summary = st.checkbox("Generate detailed summary", value=True)

    with col2:
        data_directory = st.text_input("Data directory", value="data")
        compression_type = st.selectbox("Compression type", ["snappy", "zstd", "gzip"], index=0)

    # Process button
    if st.button("🚀 Process Data", type="primary"):
        source_file = None

        # Determine source file
        if uploaded_file:
            # Save uploaded file temporarily
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            source_file = temp_dir / uploaded_file.name
            with open(source_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
        elif selected_file:
            source_file = selected_file

        if source_file:
            process_data_with_ui(str(source_file), data_directory, run_tests, generate_summary)
        else:
            st.error("Please select or upload a file to process")


def process_data_with_ui(source_filepath: str, data_dir: str, run_tests: bool, generate_summary: bool):
    """Process data with Streamlit UI feedback."""

    # Create progress containers
    progress_container = st.container()
    status_container = st.container()

    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()

    try:
        # Initialize the data preparation manager
        with status_container:
            status_text.text("🔄 Initializing data preparation...")

        manager = DataPreparationManager(data_dir=data_dir)
        progress_bar.progress(10)

        # Step 1: Load and validate data
        status_text.text("📂 Loading and validating source data...")
        df_all = manager.load_and_validate_source_data(source_filepath)
        progress_bar.progress(25)

        # Step 2: Process referrals
        status_text.text("⚙️ Processing referral data...")
        referral_results = manager.processor.process_all_referrals(df_all)
        progress_bar.progress(50)

        # Step 3: Create combined dataset
        status_text.text("🔗 Creating combined dataset...")
        df_all_referrals, df_inbound_combined, df_outbound = manager.create_combined_dataset(referral_results)
        progress_bar.progress(70)

        # Step 4: Save datasets
        status_text.text("💾 Saving processed datasets...")
        file_paths = manager.save_datasets(df_all_referrals, df_inbound_combined, df_outbound)
        progress_bar.progress(85)

        # Step 5: Run tests if requested
        test_results = None
        if run_tests:
            status_text.text("🧪 Running integration tests...")
            test_results = manager.run_integration_tests(file_paths)
        progress_bar.progress(95)

        # Step 6: Generate summary
        summary = None
        if generate_summary:
            status_text.text("📊 Generating summary...")
            summary = manager.get_processing_summary(df_all_referrals)

        progress_bar.progress(100)
        status_text.text("✅ Processing completed successfully!")

        # Store results in session state
        st.session_state["last_processing_result"] = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "source_file": source_filepath,
            "output_files": file_paths,
            "summary": summary,
            "test_results": test_results,
            "datasets": {"combined": df_all_referrals, "inbound": df_inbound_combined, "outbound": df_outbound},
        }

        # Show immediate results
        show_processing_results(summary, test_results, file_paths)

    except Exception as e:
        progress_bar.progress(100)
        status_text.text("❌ Processing failed!")
        st.error(f"Error during processing: {str(e)}")

        # Store error in session state
        st.session_state["last_processing_result"] = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "source_file": source_filepath,
        }


def show_processing_results(summary: Dict[str, Any], test_results: Dict[str, Any], file_paths: Dict[str, str]):
    """Display processing results in the UI."""

    st.success("🎉 Data processing completed successfully!")

    # Summary metrics
    if summary:
        st.markdown("### 📊 Processing Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", summary["total_records"])
        with col2:
            st.metric("Unique Providers", summary["unique_providers"])
        with col3:
            st.metric("Geocoding Coverage", f"{summary['geocoding_coverage']['geocoding_percentage']:.1f}%")
        with col4:
            st.metric("Bidirectional Providers", summary["bidirectional_providers"]["count"])

        # Referral distribution
        if "referral_distribution" in summary:
            st.markdown("#### Referral Type Distribution")
            referral_df = pd.DataFrame(list(summary["referral_distribution"].items()), columns=["Type", "Count"])
            st.bar_chart(referral_df.set_index("Type"))

    # Test results
    if test_results and test_results.get("success"):
        st.markdown("### 🧪 Integration Test Results")
        st.success("All integration tests passed!")

        if "tests" in test_results:
            with st.expander("View detailed test results"):
                st.json(test_results["tests"])

    # File outputs
    st.markdown("### 📁 Output Files")
    for file_type, file_path in file_paths.items():
        file_size = Path(file_path).stat().st_size / 1024  # KB
        st.info(f"**{file_type.title()}**: {file_path} ({file_size:.1f} KB)")


def show_results_tab():
    """Show results from previous processing runs."""
    st.subheader("Previous Processing Results")

    if "last_processing_result" in st.session_state:
        result = st.session_state["last_processing_result"]

        # Show basic info
        st.markdown(f"**Last processed**: {result['timestamp']}")
        st.markdown(f"**Source file**: {result['source_file']}")

        if result["success"]:
            st.success("✅ Last processing was successful")

            # Show summary if available
            if result.get("summary"):
                summary = result["summary"]

                st.markdown("#### Summary Statistics")
                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Total Records", summary["total_records"])
                    st.metric("Unique Providers", summary["unique_providers"])

                with col2:
                    geocoding_pct = summary["geocoding_coverage"]["geocoding_percentage"]
                    st.metric("Geocoding Coverage", f"{geocoding_pct:.1f}%")
                    st.metric("Date Range", f"{summary['date_range']['start']} to {summary['date_range']['end']}")

                # Data quality metrics
                st.markdown("#### Data Quality")
                quality = summary["data_quality"]
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Complete Contact Info", quality["complete_contact_info"])
                with col2:
                    st.metric("Missing Addresses", quality["missing_addresses"])
                with col3:
                    st.metric("Missing Phones", quality["missing_phones"])

                # Bidirectional providers
                if summary["bidirectional_providers"]["examples"]:
                    st.markdown("#### Bidirectional Providers (Examples)")
                    for provider in summary["bidirectional_providers"]["examples"]:
                        st.text(f"• {provider}")

            # Show dataset previews if available
            if result.get("datasets"):
                st.markdown("#### Dataset Previews")

                dataset_tab1, dataset_tab2, dataset_tab3 = st.tabs(["Combined", "Inbound", "Outbound"])

                with dataset_tab1:
                    if "combined" in result["datasets"]:
                        st.dataframe(result["datasets"]["combined"].head(10))

                with dataset_tab2:
                    if "inbound" in result["datasets"]:
                        st.dataframe(result["datasets"]["inbound"].head(10))

                with dataset_tab3:
                    if "outbound" in result["datasets"]:
                        st.dataframe(result["datasets"]["outbound"].head(10))

        else:
            st.error(f"❌ Last processing failed: {result.get('error', 'Unknown error')}")

    else:
        st.info("No previous processing results found. Process some data first!")


def show_settings_tab():
    """Show settings and configuration options."""
    st.subheader("Configuration Settings")

    # Data directories
    st.markdown("#### Directory Configuration")
    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Raw data directory", value="data/raw", key="raw_dir_setting")
        st.text_input("Processed data directory", value="data/processed", key="processed_dir_setting")

    with col2:
        st.text_input("Temp directory", value="temp", key="temp_dir_setting")
        st.text_input("Log directory", value="logs", key="log_dir_setting")

    # Processing options
    st.markdown("#### Processing Options")
    col1, col2 = st.columns(2)

    with col1:
        st.selectbox("Default compression", ["snappy", "zstd", "gzip"], key="default_compression")
        st.checkbox("Auto-run integration tests", value=True, key="auto_run_tests")

    with col2:
        st.checkbox("Generate detailed logs", value=True, key="detailed_logs")
        st.checkbox("Save intermediate results", value=False, key="save_intermediate")

    # Validation settings
    st.markdown("#### Validation Settings")
    col1, col2 = st.columns(2)

    with col1:
        st.number_input("Max missing addresses (%)", min_value=0, max_value=100, value=10, key="max_missing_addresses")
        st.number_input("Max missing phones (%)", min_value=0, max_value=100, value=20, key="max_missing_phones")

    with col2:
        st.number_input("Min geocoding coverage (%)", min_value=0, max_value=100, value=80, key="min_geocoding")
        st.number_input("Max processing time (minutes)", min_value=1, max_value=60, value=10, key="max_processing_time")

    # Save settings
    if st.button("💾 Save Settings"):
        st.success("Settings saved! (Note: This is a placeholder - implement actual persistence as needed)")

    # Clear cache
    if st.button("🗑️ Clear Processing Cache"):
        if "last_processing_result" in st.session_state:
            del st.session_state["last_processing_result"]
        st.success("Processing cache cleared!")


def add_data_preparation_to_sidebar():
    """Add data preparation quick actions to sidebar."""
    with st.sidebar:
        st.markdown("### 🔧 Data Preparation")

        if st.button("🚀 Quick Process", help="Process data with default settings"):
            st.session_state["show_data_prep"] = True

        # Show last processing status
        if "last_processing_result" in st.session_state:
            result = st.session_state["last_processing_result"]

            if result["success"]:
                st.success("✅ Data ready")
                if result.get("summary"):
                    total_records = result["summary"]["total_records"]
                    st.caption(f"{total_records} records processed")
            else:
                st.error("❌ Processing failed")
                st.caption("Check data preparation tab")


# Integration function for main app
def integrate_data_preparation_page():
    """
    Main integration function to be called from the Streamlit app.
    Add this to your main app routing.
    """
    show_data_preparation_ui()


if __name__ == "__main__":
    # For testing the UI independently
    st.set_page_config(page_title="Data Preparation", page_icon="🔧", layout="wide")

    show_data_preparation_ui()
