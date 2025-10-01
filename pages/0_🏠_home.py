import streamlit as st

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

st.title("JLG Provider Recommender")
st.caption("Welcome — use the navigation to run a search, view results, or manage data.")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Search")
    st.write("Find the best provider based on address and referral data.")
    st.page_link("pages/1_🔎_Search.py", label="Open Search", icon="🔎")

with col2:
    st.subheader("Data Dashboard")
    st.write("Explore cleaned provider and referral data.")
    st.page_link("pages/20_📊_Data_Dashboard.py", label="Open Dashboard", icon="📊")

with col3:
    st.subheader("Update Data")
    st.write("Refresh processed data using the current pipeline.")
    st.page_link("pages/30_🔄_Update_Data.py", label="Open Update Data", icon="♻️")

st.divider()
st.write("Learn more about how the recommender works:")
st.page_link("pages/10_🛠️_How_It_Works.py", label="How it works", icon="🛠️")
