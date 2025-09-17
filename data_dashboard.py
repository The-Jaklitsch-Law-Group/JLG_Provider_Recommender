"""Data validation and quality monitoring dashboard."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data.ingestion import load_detailed_referrals, load_provider_data
from src.utils.consolidated_functions import validate_provider_data


def calculate_referral_counts(provider_df, detailed_df):
    """Calculate referral counts if missing from provider data."""
    if not detailed_df.empty and "Full Name" in detailed_df.columns:
        referral_counts = detailed_df.groupby("Full Name").size().reset_index(name="Referral Count")
        # Merge with provider data
        provider_df = provider_df.merge(referral_counts, on="Full Name", how="left")
        provider_df["Referral Count"] = provider_df["Referral Count"].fillna(0)
    else:
        # If no detailed referral data, set all counts to 0
        provider_df["Referral Count"] = 0

    return provider_df


def display_data_quality_dashboard():
    """Display comprehensive data quality dashboard."""

    st.title("📊 Data Quality Dashboard")
    st.markdown("Monitor provider data quality and system health.")

    # Load data
    try:
        provider_df = load_provider_data()
        try:
            detailed_df = load_detailed_referrals()  # This loads the cleaned outbound referrals
        except Exception:
            # Fallback to empty DataFrame if detailed referrals not found
            detailed_df = pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    # Add referral counts if missing
    if "Referral Count" not in provider_df.columns:
        st.info("📊 Calculating referral counts from detailed referral data...")
        provider_df = calculate_referral_counts(provider_df, detailed_df)

    # Overview metrics
    st.markdown("## 🎯 Overview Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_providers = len(provider_df)
        st.metric("Total Providers", total_providers)

    with col2:
        if not detailed_df.empty:
            total_referrals = len(detailed_df)
            st.metric("Total Referrals", total_referrals)
        else:
            st.metric("Total Referrals", "N/A")

    with col3:
        if "Referral Count" in provider_df.columns:
            avg_referrals = provider_df["Referral Count"].mean()
            st.metric("Avg Referrals/Provider", f"{avg_referrals:.1f}")
        else:
            st.metric("Avg Referrals/Provider", "N/A")

    with col4:
        # Data freshness
        if not detailed_df.empty and "Referral Date" in detailed_df.columns:
            latest_referral = detailed_df["Referral Date"].max()
            days_since = (datetime.now() - latest_referral).days
            st.metric("Days Since Last Referral", days_since)
        else:
            st.metric("Days Since Last Referral", "N/A")

    # Data Quality Assessment
    st.markdown("## ✅ Data Quality Assessment")

    data_valid, data_message = validate_provider_data(provider_df)

    if data_valid:
        st.success("✅ **Data Quality: GOOD**")
    else:
        st.warning("⚠️ **Data Quality: NEEDS ATTENTION**")

    st.markdown(data_message)

    # Geographic Coverage
    st.markdown("## 🗺️ Geographic Coverage")

    if "Latitude" in provider_df.columns and "Longitude" in provider_df.columns:
        valid_coords = provider_df.dropna(subset=["Latitude", "Longitude"])

        if not valid_coords.empty:
            # Create map
            fig = px.scatter_mapbox(
                valid_coords,
                lat="Latitude",
                lon="Longitude",
                hover_name="Full Name",
                hover_data=["City", "State", "Referral Count"],
                color="Referral Count",
                size="Referral Count",
                color_continuous_scale="Viridis",
                mapbox_style="open-street-map",
                title="Provider Geographic Distribution",
                height=500,
            )
            fig.update_layout(mapbox=dict(center=dict(lat=39.2904, lon=-76.6122), zoom=8))
            st.plotly_chart(fig, use_container_width=True)

            # Geographic stats
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### Coverage Statistics")
                if "State" in provider_df.columns:
                    state_counts = provider_df["State"].value_counts()
                    st.write("**Providers by State:**")
                    for state, count in state_counts.items():
                        st.write(f"- {state}: {count} providers")

            with col2:
                st.markdown("### Coordinate Quality")
                total_providers = len(provider_df)
                valid_coords_count = len(valid_coords)
                missing_coords = total_providers - valid_coords_count

                coord_quality_fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Valid Coordinates", "Missing Coordinates"],
                            values=[valid_coords_count, missing_coords],
                            hole=0.4,
                        )
                    ]
                )
                coord_quality_fig.update_layout(title="Coordinate Completeness")
                st.plotly_chart(coord_quality_fig, use_container_width=True)
        else:
            st.warning("No valid coordinates found in provider data.")

    # Referral Distribution Analysis
    st.markdown("## 📈 Referral Distribution Analysis")

    if "Referral Count" in provider_df.columns:
        col1, col2 = st.columns(2)

        with col1:
            # Histogram of referral counts
            fig = px.histogram(
                provider_df,
                x="Referral Count",
                nbins=20,
                title="Distribution of Referral Counts",
                labels={"count": "Number of Providers", "Referral Count": "Referral Count"},
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Top providers by referral count
            top_providers = provider_df.nlargest(10, "Referral Count")[["Full Name", "Referral Count"]]
            fig = px.bar(
                top_providers,
                x="Referral Count",
                y="Full Name",
                orientation="h",
                title="Top 10 Providers by Referral Count",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

    # Time-based Analysis
    if not detailed_df.empty and "Referral Date" in detailed_df.columns:
        st.markdown("## ⏰ Referral Trends Over Time")

        # Convert referral date and create monthly aggregation
        detailed_df["Referral Date"] = pd.to_datetime(detailed_df["Referral Date"])
        detailed_df["Month"] = detailed_df["Referral Date"].dt.to_period("M")

        monthly_referrals = detailed_df.groupby("Month").size().reset_index(name="Referral Count")
        monthly_referrals["Month"] = monthly_referrals["Month"].astype(str)

        if len(monthly_referrals) > 1:
            fig = px.line(
                monthly_referrals, x="Month", y="Referral Count", title="Monthly Referral Trends", markers=True
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

        # Recent activity
        st.markdown("### Recent Activity")
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_referrals = detailed_df[detailed_df["Referral Date"] >= recent_cutoff]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Referrals (Last 30 Days)", len(recent_referrals))

        with col2:
            if len(recent_referrals) > 0:
                unique_providers = recent_referrals["Full Name"].nunique()
                st.metric("Active Providers (Last 30 Days)", unique_providers)

    # Data Issues and Recommendations
    st.markdown("## 🔧 Data Issues and Recommendations")

    issues = []
    recommendations = []

    # Check for missing coordinates
    if "Latitude" in provider_df.columns and "Longitude" in provider_df.columns:
        missing_coords = provider_df[provider_df["Latitude"].isna() | provider_df["Longitude"].isna()]
        if not missing_coords.empty:
            issues.append(f"{len(missing_coords)} providers missing geographic coordinates")
            recommendations.append("Update provider geocoding to ensure all providers have valid coordinates")

    # Check for providers with zero referrals
    if "Referral Count" in provider_df.columns:
        zero_referrals = provider_df[provider_df["Referral Count"] == 0]
        if not zero_referrals.empty:
            issues.append(f"{len(zero_referrals)} providers have zero referrals")
            recommendations.append("Review providers with zero referrals - consider removing inactive providers")

    # Check for missing contact information
    if "Phone Number" in provider_df.columns:
        missing_phone = provider_df[provider_df["Phone Number"].isna() | (provider_df["Phone Number"] == "")]
        if not missing_phone.empty:
            issues.append(f"{len(missing_phone)} providers missing phone numbers")
            recommendations.append("Update provider contact information to ensure completeness")

    # Check data freshness
    if not detailed_df.empty and "Referral Date" in detailed_df.columns:
        latest_referral = detailed_df["Referral Date"].max()
        days_since = (datetime.now() - latest_referral).days
        if days_since > 7:
            issues.append(f"No referrals recorded in the last {days_since} days")
            recommendations.append("Verify data pipeline is updating regularly")

    if issues:
        st.warning("**Issues Found:**")
        for issue in issues:
            st.write(f"- {issue}")

        st.info("**Recommendations:**")
        for rec in recommendations:
            st.write(f"- {rec}")
    else:
        st.success("No major data quality issues detected!")

    # Raw Data Preview
    with st.expander("🔍 Raw Data Preview", expanded=False):
        st.markdown("### Provider Data Sample")
        if not provider_df.empty:
            st.dataframe(provider_df.head(10))

        if not detailed_df.empty:
            st.markdown("### Detailed Referrals Sample")
            st.dataframe(detailed_df.head(10))


if __name__ == "__main__":
    # Run as standalone Streamlit app
    st.set_page_config(page_title="Data Quality Dashboard", page_icon="📊", layout="wide")

    display_data_quality_dashboard()
