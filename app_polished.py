import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import great_circle
from geopy.exc import GeocoderUnavailable

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

st.title('Provider Recommender')

# --- Tabs for Results and Overview ---
tabs = st.tabs(["Find Provider", "How Selection Works"])

with tabs[0]:
    # --- User Instructions ---
    st.markdown("""
    **Instructions:**
    1. Enter your street address, city, state, and zip code in the fields below.
    2. Adjust the sliders to set the importance (weight) of provider rank vs. distance.
    3. Click 'Find Best Provider' to get a recommendation based on your location and provider ranking.
    4. If your address is not found, the app will automatically try less specific versions of your address.
    """)

    # --- User Address Input ---
    st.subheader('Enter Your Address')
    with st.form(key='address_form'):
        street = st.text_input('Street Address (e.g., 123 Main St)', value=st.session_state.get('street', ''))
        city = st.text_input('City', value=st.session_state.get('city', ''))
        state = st.text_input('State (e.g., NY)', value=st.session_state.get('state', ''))
        zipcode = st.text_input('Zip Code', value=st.session_state.get('zipcode', ''))
        col1, col2 = st.columns(2)
        with col1:
            alpha = st.slider('Weight for Rank', min_value=0.0, max_value=1.0, value=0.5, step=0.05)
        with col2:
            beta = st.slider('Weight for Distance', min_value=0.0, max_value=1.0, value=0.5, step=0.05)
        # Normalize weights if not exactly 1.0
        if alpha + beta != 1.0:
            total = alpha + beta
            alpha = alpha / total
            beta = beta / total
        submit = st.form_submit_button('Find Best Provider')

    # Save user input in session state
    st.session_state['street'] = street
    st.session_state['city'] = city
    st.session_state['state'] = state
    st.session_state['zipcode'] = zipcode
    st.session_state['alpha'] = alpha
    st.session_state['beta'] = beta

    # --- Geocoding Setup ---
    geolocator = Nominatim(user_agent="provider_recommender")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2, max_retries=3)

    # --- Geocode Providers (cached) ---
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

    # --- User Geocoding and Recommendation ---
    if submit:
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
                st.success(f"Your location: ({user_lat:.5f}, {user_lon:.5f})")
            else:
                st.error("Could not geocode your address. Please check and try again.")
        except GeocoderUnavailable as e:
            st.error(f"Geocoding service unavailable: {e}")
        except Exception as e:
            st.error(f"Geocoding error: {e}")

        # --- Distance Calculation ---
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

        if user_lat is not None and user_lon is not None:
            provider_df['Distance (miles)'] = calculate_distances(user_lat, user_lon, provider_df)

            # --- Recommendation Logic ---
            def recommend_provider(provider_df, alpha=0.5, beta=0.5):
                df = provider_df.copy()
                df = df[df['Distance (miles)'].notnull() & df['Rank'].notnull()]
                if df.empty:
                    return None, None
                df['norm_rank'] = (df['Rank'] - df['Rank'].min()) / (df['Rank'].max() - df['Rank'].min())
                df['norm_dist'] = (df['Distance (miles)'] - df['Distance (miles)'].min()) / (df['Distance (miles)'].max() - df['Distance (miles)'].min())
                df['score'] = alpha * df['norm_rank'] + beta * df['norm_dist']
                best = df.sort_values(by='score').iloc[0]
                return best, df

            st.subheader('Best Provider Recommendation')
            best, scored_df = recommend_provider(provider_df, alpha=alpha, beta=beta)
            if best is not None and isinstance(scored_df, pd.DataFrame):
                st.session_state['recommendation'] = f"Best provider: {best['Full Name']}\nAddress: {best['Full Address']}\nDistance: {best['Distance (miles)']:.2f} miles\nRank: {best['Rank']}"
                st.success(st.session_state['recommendation'])
                st.write('Top 5 providers by blended score:')
                st.dataframe(scored_df[['Full Name', 'Full Address', 'Distance (miles)', 'Rank', 'score']].sort_values(by='score').head())
            else:
                st.warning('No providers with both rank and distance available.')
    else:
        st.info('Enter your address and click "Find Best Provider" to see recommendations.')

with tabs[1]:
    # --- High-Level Overview of Selection Process ---
    st.markdown("""
    ### How Provider Selection Works
    - The app recommends the best provider based on a combination of your location and each provider's ranking.
    - **Step 1:** Your address is geocoded (converted to latitude/longitude). If the full address fails, the app tries less specific versions (street only, city/state, or zip).
    - **Step 2:** The distance from your location to each provider is calculated.
    - **Step 3:** Each provider has a pre-assigned rank (lower is better).
    - **Step 4:** The app calculates a **blended score** for each provider:
        - The score is a weighted sum: `score = weight_rank * normalized_rank + weight_distance * normalized_distance`
        - Both rank and distance are normalized (scaled between 0 and 1) so they are comparable.
        - The weights are set by you using the sliders above.
        - Lower scores mean a better balance of proximity and provider quality.
    - **Step 5:** The provider with the lowest blended score is recommended as the best option.
    - You will also see the top 5 providers by blended score for comparison.
    """) 