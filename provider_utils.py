import pandas as pd
import numpy as np
from geopy.exc import GeocoderUnavailable
from geopy.distance import great_circle
import io
from docx import Document
import re


# --- Data Loading ---
def load_provider_data(filepath):
    """Load and preprocess provider data from Excel, CSV, Feather, or Parquet"""

    if '.xlsx' in filepath:
        df = pd.read_excel(filepath)
    elif '.csv' in filepath:
        df = pd.read_csv(filepath)
    elif '.feather' in filepath:
        df = pd.read_feather(filepath)
    elif '.parquet' in filepath:
        df = pd.read_parquet(filepath)
    else:
        print(f"Unable to read {filepath} - check file type.")

    df.columns = [col.strip() for col in df.columns]
    df['Zip'] = df['Zip'].apply(lambda x: str(x) if pd.notnull(x) else '')
    df['Full Address'] = (
        df['Street'].fillna('') + ', '
        + df['City'].fillna('') + ', '
        + df['State'].fillna('') + ' '
        + df['Zip'].fillna('')
    )
    df['Full Address'] = df['Full Address'].str.replace(r',\s*,', ',', regex=True).str.replace(r',\s*$', '', regex=True)
    return df


def sanitize_filename(name):
    """Sanitize a string for use as a filename."""
    return re.sub(r'[^A-Za-z0-9_]', '', name.replace(' ', '_'))


def get_word_bytes(best):
    """Generate a Word document as bytes for the recommended provider."""
    doc = Document()
    doc.add_heading('Recommended Provider', 0)
    doc.add_paragraph(f"Name: {best['Full Name']}")
    doc.add_paragraph(f"Address: {best['Full Address']}")
    # doc.add_paragraph(f"Phone: {best['Phone 1']}")
    # doc.add_paragraph(f"Email: {best['Email 1']}")
    # doc.add_paragraph(f"Specialty: {best['Specialty']}")
    # if best.get('Preferred', 0) == 1:
    #     doc.add_paragraph("Preferred Provider")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def recommend_provider(provider_df, alpha=0.5, beta=0.5):
    """Return the best provider and scored DataFrame, prioritizing preferred providers, then lowest blended score."""
    df = provider_df.copy()
    df = df[df['Distance (miles)'].notnull() & df['Referral Count'].notnull()]
    if df.empty:
        return None, None

    # Prioritize preferred providers: filter to preferred if any exist
    preferred_df = df[df['Preferred'] == 1]
    if not preferred_df.empty:
        df = preferred_df

    # Safe normalization (avoid division by zero)
    referral_range = df['Referral Count'].max() - df['Referral Count'].min()
    dist_range = df['Distance (miles)'].max() - df['Distance (miles)'].min()
    df['norm_rank'] = (df['Referral Count'] - df['Referral Count'].min()) / referral_range if referral_range != 0 else 0
    df['norm_dist'] = (df['Distance (miles)'] - df['Distance (miles)'].min()) / dist_range if dist_range != 0 else 0
    df['score'] = alpha * df['norm_rank'] + beta * df['norm_dist']
    best = df.sort_values(by='score').iloc[0]
    return best, df


def geocode_providers(addresses, _geocode):
    """Geocode a list of addresses, returning lists of latitudes and longitudes."""
    lats, lons = [], []
    for addr in addresses:
        try:
            location = _geocode(addr, timeout=10)
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


def calculate_distances(user_lat, user_lon, provider_df):
    """Calculate distances in miles from user to each provider."""
    user_loc = (user_lat, user_lon)
    distances = []
    for lat, lon in zip(provider_df['Latitude'], provider_df['Longitude']):
        if pd.notnull(lat) and pd.notnull(lon):
            dist = great_circle(user_loc, (lat, lon)).miles
        else:
            dist = None
        distances.append(dist)
    return distances 