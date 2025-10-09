import streamlit as st

from app import show_auto_update_status
from src.utils.responsive import resp_columns, responsive_sidebar_toggle

st.set_page_config(page_title="Home", page_icon="🏠", layout="centered")

# small sidebar toggle to force mobile stacked layout during development/testing
responsive_sidebar_toggle()

# Show S3 auto-update status if available
# show_auto_update_status()

# Hero section (concise)
st.title("🏥 JLG Provider Recommender")
st.markdown("Find the right healthcare provider for your client — quickly and confidently")

# Prominent quick CTA: big, centered link to the Search page
cta_col_left, cta_col_center, cta_col_right = st.columns([1, 2, 1])
with cta_col_center:
    st.markdown("### Ready to find a provider?")
    st.page_link("pages/1_🔎_Search.py", label="Start a Search", icon="🔎")

# Keep the main actions but simplify and shorten descriptions
st.divider()
st.subheader("Quick actions")
col1, col2 = resp_columns([1, 1])

with col1:
    st.markdown("**🔄 Update Data** — Refresh the system with the latest referral information.")
    st.page_link("pages/30_🔄_Update_Data.py", label="Open Update Data", icon="🔄")

with col2:
    st.markdown("**📊 Dashboard** — View provider metrics and referral trends.")
    st.page_link("pages/20_📊_Data_Dashboard.py", label="Open Dashboard", icon="📊")

# Condense value props into an expander to reduce visual noise
with st.expander("Why use this tool?", expanded=False):
    st.markdown(
        "- Intelligent scoring combining distance and referral history\n- Fast results and easy export\n- Configurable presets for common workflows"
    )

# Move tips into an expander so the page stays clean for non-technical users
with st.expander("💡 Quick Tips", expanded=False):
    st.markdown(
        "**For best results:**\n- Use full addresses (street, city, state, ZIP)\n- Try the Balanced preset first\n\n**Common workflows:**\n1. Search → Select provider → Export\n2. Dashboard → Review metrics → Adjust search"
    )

# Footer with help
col_help1, col_help2 = st.columns([1, 3])
with col_help1:
    st.page_link("pages/10_🛠️_How_It_Works.py", label="📖 How It Works", icon="🛠️")
with col_help2:
    st.caption("Learn more about the scoring algorithm, search options, and best practices.")
