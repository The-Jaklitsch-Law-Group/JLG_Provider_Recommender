import streamlit as st

from app import show_auto_update_status
from src.utils.responsive import resp_columns, responsive_sidebar_toggle

st.set_page_config(page_title="Home", page_icon="🏠", layout="centered")

# small sidebar toggle to force mobile stacked layout during development/testing
responsive_sidebar_toggle()

# Show S3 auto-update status if available
show_auto_update_status()

# Hero section
st.title("🏥 JLG Provider Recommender")
st.markdown("### Find the right healthcare provider for your client — quickly and confidently")

st.divider()

# Main action cards
st.subheader("🚀 What would you like to do?")

# col1, col2, col3 = resp_columns([1, 1, 1])
col1, col2 = resp_columns([1, 1])

with col1:
    with st.container():
        st.markdown("#### 🔎 Search")
        st.markdown("Find the best provider based on your client's address and your preferences.")
        st.markdown("**Perfect for:** Daily case assignments")
        st.page_link("pages/1_🔎_Search.py", label="Start Search →", icon="🔎")

with col2:
    with st.container():
        st.markdown("#### 📊 Dashboard")
        st.markdown("Explore provider data, referral patterns, and system insights.")
        st.markdown("**Perfect for:** Understanding trends")
        st.page_link("pages/20_📊_Data_Dashboard.py", label="View Dashboard →", icon="📊")

# with col3:
#     with st.container():
#         st.markdown("#### 🔄 Update Data")
#         st.markdown("Refresh the system with the latest referral information.")
#         st.markdown("**Perfect for:** Monthly data updates")
#         st.page_link("pages/30_🔄_Update_Data.py", label="Update Data →", icon="🔄")

st.divider()

# Main value proposition
st.subheader("Smart provider matching made simple:")

col1, col2 = resp_columns([2, 1])
with col1:
    st.markdown(
        """
    - 🎯 **Intelligent Scoring** — Balances proximity, workload, and relationships
    - ⚡ **Fast Results** — Get recommendations in seconds
    - 🎨 **Flexible Options** — Customize search or use preset profiles
    - 📊 **Data-Driven** — Based on real referral history and relationships
    """
    )

with col2:
    st.info("💡 **New to this tool?** Check out our [How It Works](/10_🛠️_How_It_Works) guide to get started!")


st.divider()

# Quick tips section
st.subheader("💡 Quick Tips")

tip_col1, tip_col2 = st.columns(2)

with tip_col1:
    st.markdown(
        """
    **For best results:**
    - Use complete addresses (street, city, state, ZIP)
    - Start with "Balanced" preset for most cases
    - Check the dashboard periodically to understand workload
    """
    )

with tip_col2:
    st.markdown(
        """
    **Common workflows:**
    1. 🔎 Search → Find provider → 📄 Export to Word
    2. 📊 Dashboard → Review data → 🔎 Adjust search
    3. 🔄 Update → Load new data → 🔎 Search
    """
    )

st.divider()

# Footer with help
col_help1, col_help2 = st.columns([1, 3])
with col_help1:
    st.page_link("pages/10_🛠️_How_It_Works.py", label="📖 How It Works", icon="🛠️")
with col_help2:
    st.caption("Learn more about the scoring algorithm, search options, and best practices.")
