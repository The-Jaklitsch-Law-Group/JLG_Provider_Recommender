import pandas as pd
import numpy as np
from geopy.exc import GeocoderUnavailable
import io
from docx import Document
import re
from pathlib import Path
from functools import lru_cache


# --- Data Loading ---
@lru_cache(maxsize=1)
def load_provider_data(filepath: str) -> pd.DataFrame:
    """Load and preprocess provider data from Excel, CSV, Feather, or Parquet."""

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File {filepath} does not exist")

    suffix = path.suffix.lower()
    if suffix == '.xlsx':
        df = pd.read_excel(path)
    elif suffix == '.csv':
        df = pd.read_csv(path)
    elif suffix == '.feather':
        df = pd.read_feather(path)
    elif suffix == '.parquet':
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

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


def recommend_provider(provider_df, distance_weight=0.5, referral_weight=0.5):
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
    df['norm_rank'] = (
        (df['Referral Count'] - df['Referral Count'].min()) / referral_range
        if referral_range != 0
        else 0
    )
    df['norm_dist'] = (
        (df['Distance (miles)'] - df['Distance (miles)'].min()) / dist_range
        if dist_range != 0
        else 0
    )
    df['score'] = distance_weight * df['norm_dist'] + referral_weight * df['norm_rank']
    best = df.sort_values(by='score').iloc[0]
    return best, df


_geocode_cache = {}


def geocode_providers(addresses, _geocode):
    """Geocode a list of addresses, returning lists of latitudes and longitudes."""

    def _cached_geocode(addr):
        if addr not in _geocode_cache:
            try:
                location = _geocode(addr, timeout=10)
                if location:
                    _geocode_cache[addr] = (location.latitude, location.longitude)
                else:
                    _geocode_cache[addr] = (None, None)
            except GeocoderUnavailable as e:
                _geocode_cache[addr] = (None, None)
                print(f"GeocoderUnavailable for address '{addr}': {e}")
            except Exception as e:
                _geocode_cache[addr] = (None, None)
                print(f"Geocoding error for address '{addr}': {e}")
        return _geocode_cache[addr]

    results = pd.Series(addresses).map(_cached_geocode)
    lats, lons = zip(*results)
    return list(lats), list(lons)


def calculate_distances(user_lat, user_lon, provider_df):
    """Calculate distances in miles from user to each provider using vectorized operations."""

    lat_rad = np.radians(provider_df['Latitude'].to_numpy(dtype=float))
    lon_rad = np.radians(provider_df['Longitude'].to_numpy(dtype=float))
    user_lat_rad = np.radians(user_lat)
    user_lon_rad = np.radians(user_lon)

    valid = ~np.isnan(lat_rad) & ~np.isnan(lon_rad)
    dlat = lat_rad[valid] - user_lat_rad
    dlon = lon_rad[valid] - user_lon_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(user_lat_rad) * np.cos(lat_rad[valid]) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    distances = np.full(len(provider_df), np.nan)
    distances[valid] = 3958.8 * c  # Earth radius in miles

    # Convert NaN to None for consistency with previous behavior
    return [None if np.isnan(d) else float(d) for d in distances]
