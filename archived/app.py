import streamlit as st
import pandas as pd  # For data handling
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.distance import great_circle
from geopy.exc import GeocoderUnavailable

# Educational comment: Streamlit is a Python library for building interactive web apps easily.
# To run this app, use the command: streamlit run app.py

# Educational comment: session_state allows you to store variables across reruns (e.g., for each user session).
if 'user_address' not in st.session_state:
    st.session_state['user_address'] = ''
if 'recommendation' not in st.session_state:
    st.session_state['recommendation'] = None

st.title('Provider Recommender')

# Educational comment: st.text_input creates a text box for user input.
user_address = st.text_input('Enter your address:', value=st.session_state['user_address'])

# Update session_state with the latest input
st.session_state['user_address'] = user_address

# Educational comment: st.button creates a clickable button.
if st.button('Find Best Provider'):
    # Placeholder for recommendation logic
    st.session_state['recommendation'] = 'Recommendation will appear here.'

# Educational comment: Display the recommendation if available.
if st.session_state['recommendation']:
    st.success(st.session_state['recommendation'])

# More logic will be added in the next steps to read the Excel file, geocode addresses, and recommend a provider.

# Educational comment: Read the Excel file with provider data using pandas.
def load_provider_data():
    df = pd.read_excel('data/Ranked_Contacts.xlsx')
    # Clean up column names (remove leading/trailing spaces)
    df.columns = [col.strip() for col in df.columns]
    # Ensure zip codes are strings and remove decimals if present
    df['Address 1 Zip'] = df['Address 1 Zip'].apply(lambda x: str(int(x)) if pd.notnull(x) else '')
    # Combine address columns into a single full address string for geocoding
    df['Full Address'] = (
        df['Address 1 Line 1'].fillna('') + ', '
        + df['Address 1 City'].fillna('') + ', '
        + df['Address 1 State'].fillna('') + ' '
        + df['Address 1 Zip'].fillna('')
    )
    # Remove redundant commas and spaces
    df['Full Address'] = df['Full Address'].str.replace(r',\s*,', ',', regex=True).str.replace(r',\s*$', '', regex=True)
    return df

# Load and display provider data for educational purposes
provider_df = load_provider_data()

# Educational comment: Geocoding converts addresses to latitude/longitude coordinates.
# We use Nominatim (OpenStreetMap) via geopy for free geocoding.
geolocator = Nominatim(user_agent="provider_recommender")
# Educational comment: Increase timeout and add retries to handle seslow or unreliable geocoding responses.
# Use a longer delay to respect Nominatim's rate limits
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=2, max_retries=3)

# Educational comment: Pass timeout=10 to each geocode call to allow up to 10 seconds per request.
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
            # Educational comment: Handle Nominatim server unavailability gracefully.
            lats.append(None)
            lons.append(None)
            print(f"GeocoderUnavailable for address '{addr}': {e}")
        except Exception as e:
            # Educational comment: Handle other geocoding errors gracefully and log them for debugging.
            lats.append(None)
            lons.append(None)
            print(f"Geocoding error for address '{addr}': {e}")
    return lats, lons

# Geocode provider addresses (only once, thanks to caching)
provider_lats, provider_lons = geocode_providers(provider_df['Full Address'])
provider_df['Latitude'] = provider_lats
provider_df['Longitude'] = provider_lons

# Geocode user address when button is pressed
user_lat, user_lon = None, None
if st.session_state['user_address'] and st.button('Geocode My Address'):
    try:
        user_location = geocode(st.session_state['user_address'], timeout=10)
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

# Educational: Show geocoded provider coordinates
st.subheader('Geocoded Provider Coordinates (first 5)')
st.dataframe(provider_df[['Full Name', 'Full Address', 'Latitude', 'Longitude']].head())

# Educational comment: st.dataframe displays a pandas DataFrame in the app.
st.subheader('Preview of Provider Data')
st.dataframe(provider_df[['Full Name', 'Full Address', 'Rank']].head())

# Educational comment: Calculate distance (in miles) between user and providers using great_circle formula.
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

# Only calculate distances if user coordinates are available
if 'user_lat' in st.session_state and 'user_lon' in st.session_state:
    provider_df['Distance (miles)'] = calculate_distances(
        st.session_state['user_lat'], st.session_state['user_lon'], provider_df
    )
    # Educational: Show the 5 closest providers
    st.subheader('Closest Providers (by distance)')
    st.dataframe(
        provider_df[['Full Name', 'Full Address', 'Distance (miles)', 'Rank']]
        .sort_values('Distance (miles)').head()
    )
else:
    st.info('Enter and geocode your address to see provider distances.')

# Educational comment: Blend provider ranking and distance to recommend the best provider.
# We'll use a simple weighted score: score = alpha * normalized_rank + beta * normalized_distance
# Lower scores are better. You can adjust alpha/beta to change the importance of rank vs. distance.
def recommend_provider(provider_df, alpha=0.5, beta=0.5):
    df = provider_df.copy()
    # Normalize rank and distance to [0, 1]
    df = df[df['Distance (miles)'].notnull() & df['Rank'].notnull()]
    if df.empty:
        return None, None
    df['norm_rank'] = (df['Rank'] - df['Rank'].min()) / (df['Rank'].max() - df['Rank'].min())
    df['norm_dist'] = (df['Distance (miles)'] - df['Distance (miles)'].min()) / (df['Distance (miles)'].max() - df['Distance (miles)'].min())
    df['score'] = alpha * df['norm_rank'] + beta * df['norm_dist']
    best = df.sort_values('score').iloc[0]
    return best, df

# Only recommend if distances are available
if 'Distance (miles)' in provider_df.columns:
    st.subheader('Best Provider Recommendation')
    best, scored_df = recommend_provider(provider_df, alpha=0.5, beta=0.5)
    if best is not None:
        st.session_state['recommendation'] = f"Best provider: {best['Full Name']}\nAddress: {best['Full Address']}\nDistance: {best['Distance (miles)']:.2f} miles\nRank: {best['Rank']}"
        st.success(st.session_state['recommendation'])
        # Educational: Show the top 5 scored providers
        st.write('Top 5 providers by blended score:')
        st.dataframe(scored_df[['Full Name', 'Full Address', 'Distance (miles)', 'Rank', 'score']].sort_values('score').head())
    else:
        st.warning('No providers with both rank and distance available.') 