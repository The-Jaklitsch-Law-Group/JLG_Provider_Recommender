import streamlit as st
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import great_circle
from geopy.exc import GeocoderUnavailable

# --- Recommendation Function ---
def recommend_provider(provider_df, alpha=0.5, beta=0.5):
    df = provider_df.copy()
    df = df[df['Distance (miles)'].notnull() & df['Rank'].notnull()]
    if df.empty:
        return None, None
    # Prioritize preferred providers: filter to preferred if any exist
    preferred_df = df[df['Preferred'] == 1]
    if not preferred_df.empty:
        df = preferred_df
    df['norm_rank'] = (df['Rank'] - df['Rank'].min()) / (df['Rank'].max() - df['Rank'].min())
    df['norm_dist'] = (df['Distance (miles)'] - df['Distance (miles)'].min()) / (df['Distance (miles)'].max() - df['Distance (miles)'].min())
    df['score'] = alpha * df['norm_rank'] + beta * df['norm_dist']
    best = df.sort_values(by='score').iloc[0]
    return best, df


# --- Data Loading ---
def load_provider_data():
    df = pd.read_excel('data/Ranked_Contacts.xlsx')
    df.columns = [col.strip() for col in df.columns]
    df['Address 1 Zip'] = df['Address 1 Zip'].apply(lambda x: str(int(x)) if pd.notnull(x) else '')
    df['Full Address'] = (
        df['Address 1 Line 1'].fillna('') + ', '
        + df['Address 1 City'].fillna('') + ', '
        + df['Address 1 State'].fillna('') + ' '
        + df['Address 1 Zip'].fillna('')
    )
    df['Full Address'] = df['Full Address'].str.replace(r',\s*,', ',', regex=True).str.replace(r',\s*$', '', regex=True)
    return df

provider_df = load_provider_data()

# --- Add temporary placeholders if needed ---
if 'Specialty' not in provider_df.columns:
    placeholder_specialties = [
        'Primary Care', 'Urgent Care', 'Chiropractor', 'Physical Therapy'
    ]
    provider_df['Specialty'] = np.random.choice(placeholder_specialties, size=len(provider_df))
if 'Phone 1' not in provider_df.columns:
    provider_df['Phone 1'] = '555-555-1234'
if 'Email 1' not in provider_df.columns:
    provider_df['Email 1'] = 'provider@example.com'
# Add a preferred provider flag/score if not present
if 'Preferred' not in provider_df.columns:
    provider_df['Preferred'] = np.random.choice([1, 0], size=len(provider_df), p=[0.3, 0.7])  # 30% preferred

st.set_page_config(page_title="Provider Recommender", page_icon=":hospital:")#, layout="wide")

st.title('Provider Recommender for Personal Injury Clients')

# --- Tabs for Results and Overview ---
tabs = st.tabs(["Find Provider", "How Selection Works"])

with tabs[0]:
    # --- Layout: Instructions on the left, form/results on the right ---
    with st.expander('Instructions:', expanded=True):
        st.markdown("""
            1. Enter the client's address and preferences.<br>
            2. Adjust the sliders to set the importance (weight) of provider rank vs. distance.<br>
            3. Select a provider specialty if needed.<br>
            4. Click <b>Find Best Provider</b> to get a recommendation. The app prioritizes the law firm's preferred providers, then considers proximity and ranking.<br>
            5. The final result is contact information to direct the client to the best provider.
            </div>
            """, unsafe_allow_html=True)
    
    left_col, right_col = st.columns([.5, .5])
    with left_col:
        # Only show input form if no results yet
        show_form = 'show_form' not in st.session_state or st.session_state.get('show_form', True)
        # Initialize variables to avoid unbound errors
        street = st.session_state.get('street', '')
        city = st.session_state.get('city', '')
        state = st.session_state.get('state', '')
        zipcode = st.session_state.get('zipcode', '')
        specialty = st.session_state.get('specialty', 'Any')
        alpha = st.session_state.get('alpha', 0.5)
        beta = st.session_state.get('beta', 0.5)
        submit = False  # Ensure submit is always defined
        if show_form:
            specialties = sorted(provider_df['Specialty'].dropna().unique()) if 'Specialty' in provider_df.columns else []
            
            with st.expander('🏠 Enter Client Address', expanded=True):
                with st.form(key='address_form'):
                    street = st.text_input('Street Address (e.g., 123 Main St)', value=street)
                    city = st.text_input('City', value=city)
                    state = st.text_input('State (e.g., NY)', value=state)
                    zipcode = st.text_input('Zip Code', value=zipcode)
                    specialty = st.selectbox('Provider Specialty (optional)', ['Any'] + specialties) if specialties else 'Any'
                    col1, col2 = st.columns(2)
                    with col1:
                        alpha = st.slider('Weight for Rank', min_value=0.0, max_value=1.0, value=alpha, step=0.05)
                    with col2:
                        beta = st.slider('Weight for Distance', min_value=0.0, max_value=1.0, value=beta, step=0.05)
                    if alpha + beta != 1.0:
                        total = alpha + beta
                        alpha = alpha / total
                        beta = beta / total
                    submit = st.form_submit_button('Find Best Provider')

            st.session_state['street'] = street
            st.session_state['city'] = city
            st.session_state['state'] = state
            st.session_state['zipcode'] = zipcode
            st.session_state['alpha'] = alpha
            st.session_state['beta'] = beta
            st.session_state['specialty'] = specialty
        else:
            # Show a button to start a new search
            if st.button('New Search'):
                for key in ['user_lat', 'user_lon', 'recommendation', 'show_form']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

        # --- Geocoding Setup ---
        geolocator = Nominatim(user_agent="provider_recommender")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2, max_retries=3)

        @st.cache_data(show_spinner=True)
        def geocode_providers(addresses):
            lats, lons = [], []
            for addr in addresses:
                try:
                    location = geocode(addr, timeout=10)
                    if location:
                        lats.append(location.latitude)
                        lons.append(location.longitude)
                    else:
                        lats.append(None)
                        lons.append(None)
                except GeocoderUnavailable as e:
                    lats.append(None)
                    lons.append(None)
                    print(f"GeocoderUnavailable for address '{addr}': {e}")
                except Exception as e:
                    lats.append(None)
                    lons.append(None)
                    print(f"Geocoding error for address '{addr}': {e}")
            return lats, lons

        provider_lats, provider_lons = geocode_providers(provider_df['Full Address'])
        provider_df['Latitude'] = provider_lats
        provider_df['Longitude'] = provider_lons

    if show_form and submit:
        st.session_state['show_form'] = False
        user_full_address = f"{street}, {city}, {state} {zipcode}".strip(', ')
        user_lat, user_lon = None, None
        try:
            user_location = geocode(user_full_address, timeout=10)
            if not user_location and street:
                street_simple = street.split(',')[0].split(' Apt')[0].split(' Suite')[0]
                user_location = geocode(street_simple, timeout=10)
            if not user_location:
                if city and state:
                    user_location = geocode(f"{city}, {state}", timeout=10)
                elif zipcode:
                    user_location = geocode(zipcode, timeout=10)
            if user_location:
                user_lat, user_lon = user_location.latitude, user_location.longitude
                st.session_state['user_lat'] = user_lat
                st.session_state['user_lon'] = user_lon
            else:
                st.error("Could not geocode your address. Please check and try again.")
        except GeocoderUnavailable as e:
            st.error(f"Geocoding service unavailable: {e}")
        except Exception as e:
            st.error(f"Geocoding error: {e}")

        def calculate_distances(user_lat, user_lon, provider_df):
            user_loc = (user_lat, user_lon)
            distances = []
            for lat, lon in zip(provider_df['Latitude'], provider_df['Longitude']):
                if pd.notnull(lat) and pd.notnull(lon):
                    dist = great_circle(user_loc, (lat, lon)).miles
                else:
                    dist = None
                distances.append(dist)
            return distances

        
        if not show_form:
            st.info('Click "New Search" to enter a new address.')

    with right_col:
        st.subheader('Best Provider Recommendation')
        if user_lat is not None and user_lon is not None:
            filtered_df = provider_df.copy()
            if specialty != 'Any' and 'Specialty' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Specialty'] == specialty]
            filtered_df['Distance (miles)'] = calculate_distances(user_lat, user_lon, filtered_df)

        best, scored_df = recommend_provider(filtered_df, alpha=alpha, beta=beta)
        if best is not None and isinstance(scored_df, pd.DataFrame):
            st.markdown(f"**Name:** {best['Full Name']}")
            address_for_url = best['Full Address'].replace(' ', '+')
            maps_url = f"https://www.google.com/maps/search/?api=1&query={address_for_url}"
            st.markdown(f"**Address:** [{best['Full Address']}]({maps_url})")
            st.markdown(f"**Phone:** {best['Phone 1']}")
            st.markdown(f"**Email:** {best['Email 1']}")
            st.markdown(f"**Specialty:** {best['Specialty']}")
            if best.get('Preferred', 0) == 1:
                st.markdown(f"<span style='color: green; font-weight: bold;'>Preferred Provider</span>", unsafe_allow_html=True)
            st.write('Top 5 providers by blended score:')
            st.dataframe(scored_df[['Full Name', 'Full Address', 'Distance (miles)', 'Rank', 'score', 'Preferred']].sort_values(by='score').head())

            # --- Rationale for Selection ---
            st.markdown('---')
            st.subheader('Why was this provider selected?')
            rationale = []
            if best.get('Preferred', 0) == 1:
                rationale.append('This provider is a **Preferred Provider** for the law firm, which means they are trusted and have a strong track record with our clients.')
            else:
                rationale.append('This provider is not marked as preferred, but was selected based on a balance of proximity and ranking.')
            rationale.append(f"The provider's **distance** from the client is **{best['Distance (miles)']:.2f} miles**.")
            rationale.append(f"The provider's **rank** is **{best['Rank']}** (lower is better).")
            rationale.append(f"The selected specialty is **{best['Specialty']}**.")
            rationale.append(f"The final score is a blend of normalized rank and distance, using your chosen weights: **Rank weight = {alpha:.2f}**, **Distance weight = {beta:.2f}**.")
            rationale.append(f"The provider with the lowest blended score was recommended.")
            st.markdown('<br>'.join(rationale), unsafe_allow_html=True)
        else:
            st.warning('No providers with both rank and distance available.')
    

with tabs[1]:
    # --- High-Level Overview of Selection Process ---
    st.markdown("""
    ### How Provider Selection Works
    - This app is designed for personal injury law firms to help new clients identify healthcare providers.
    - The law firm's **preferred providers** are prioritized in recommendations.
    - **Step 1:** The client's address is geocoded (converted to latitude/longitude). If the full address fails, the app tries less specific versions (street only, city/state, or zip).
    - **Step 2:** The distance from the client to each provider is calculated.
    - **Step 3:** Each provider has a pre-assigned rank (lower is better).
    - **Step 4:** The app calculates a **blended score** for each provider:
        - The score is a weighted sum: `score = weight_rank * normalized_rank + weight_distance * normalized_distance`
        - Both rank and distance are normalized (scaled between 0 and 1) so they are comparable.
        - The weights are set by you using the sliders above.
        - Lower scores mean a better balance of proximity and provider quality.
    - **Step 5:** If any preferred providers are available, only those are considered for the final recommendation.
    - **Step 6:** The provider with the lowest blended score is recommended as the best option.
    - The final product is clear contact information to direct the client to the best provider.
    - You will also see the top 5 providers by blended score for comparison.
    """)