import pandas as pd
import numpy as np
from geopy.exc import GeocoderUnavailable
import streamlit as st
import io
from docx import Document
import re
from pathlib import Path


# --- Data Loading ---
@st.cache_data(ttl=3600)
def load_provider_data(filepath: str) -> pd.DataFrame:
    """Load and preprocess provider data from Excel, CSV, Feather, or Parquet."""

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File {filepath} does not exist")

    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        df = pd.read_excel(path)
    elif suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix == ".feather":
        df = pd.read_feather(path)
    elif suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    df.columns = [col.strip() for col in df.columns]
    df = df.drop(columns="Preference", errors="ignore")
    df["Zip"] = df["Zip"].apply(lambda x: str(x) if pd.notnull(x) else "")
    df["Referral Count"] = pd.to_numeric(df["Referral Count"], errors="coerce")
    df["Full Address"] = (
        df["Street"].fillna("")
        + ", "
        + df["City"].fillna("")
        + ", "
        + df["State"].fillna("")
        + " "
        + df["Zip"].fillna("")
    )
    df["Full Address"] = (
        df["Full Address"]
        .str.replace(r",\s*,", ",", regex=True)
        .str.replace(r",\s*$", "", regex=True)
    )
    return df


def sanitize_filename(name):
    """Sanitize a string for use as a filename."""
    return re.sub(r"[^A-Za-z0-9_]", "", name.replace(" ", "_"))


def get_word_bytes(best):
    """Generate a Word document as bytes for the recommended provider."""
    doc = Document()
    doc.add_heading("Recommended Provider", 0)
    doc.add_paragraph(f"Name: {best['Full Name']}")
    doc.add_paragraph(f"Address: {best['Full Address']}")
    phone = best.get("Phone Number") or best.get("Phone 1")
    if phone:
        doc.add_paragraph(f"Phone: {phone}")
    # doc.add_paragraph(f"Email: {best['Email 1']}")
    # doc.add_paragraph(f"Specialty: {best['Specialty']}")
    # if best.get('Preferred', 0) == 1:
    #     doc.add_paragraph("Preferred Provider")
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    # Return raw bytes which can be passed directly to Streamlit's download APIs
    return buffer.getvalue()


def recommend_provider(provider_df, distance_weight=0.5, referral_weight=0.5, min_referrals=None):
    """Return the best provider and scored DataFrame.

    Parameters
    - provider_df: DataFrame with at least 'Distance (Miles)' and 'Referral Count'
    - distance_weight, referral_weight: blend weights (should sum to 1 but not required)
    - min_referrals: optional int to filter providers with Referral Count >= min_referrals
    """
    df = provider_df.copy(deep=True)
    df = df[df["Distance (Miles)"].notnull() & df["Referral Count"].notnull()]
    if min_referrals is not None:
        df = df[df["Referral Count"] >= min_referrals]

    if df.empty:
        return None, None

    # # Prioritize preferred providers: filter to preferred if any exist
    # preferred_df = df[df['Preferred'] == 1]
    # if not preferred_df.empty:
    #     df = preferred_df

    # Safe normalization (avoid division by zero)
    referral_range = df["Referral Count"].max() - df["Referral Count"].min()
    dist_range = df["Distance (Miles)"].max() - df["Distance (Miles)"].min()
    df["norm_rank"] = (
        (df["Referral Count"] - df["Referral Count"].min()) / referral_range
        if referral_range != 0
        else 0
    )
    df["norm_dist"] = (
        (df["Distance (Miles)"] - df["Distance (Miles)"].min()) / dist_range
        if dist_range != 0
        else 0
    )
    df["Score"] = distance_weight * df["norm_dist"] + referral_weight * df["norm_rank"]

    # Tie-break behavior:
    # - If distance is prioritized (distance_weight > referral_weight), sort ties by
    #   Distance (ascending) then Referral Count (ascending).
    # - Otherwise, sort ties by Referral Count (ascending) then Distance (ascending).
    # This ensures deterministic ordering when multiple providers share the same score.
    if distance_weight > referral_weight:
        sort_keys = ["Score", "Distance (Miles)", "Referral Count"]
    else:
        sort_keys = ["Score", "Referral Count", "Distance (Miles)"]

    # Add a stable final tie-break key so ordering is deterministic across runs/users.
    # Prefer alphabetical provider name if available.
    candidate_keys = sort_keys + ["Full Name"]
    sort_keys_final = [k for k in candidate_keys if k in df.columns]
    ascending = [True] * len(sort_keys_final)

    df_sorted = df.sort_values(by=sort_keys_final, ascending=ascending).reset_index(drop=True)
    best = df_sorted.iloc[0]
    return best, df_sorted


_geocode_cache = {}


def geocode_address(addresses, _geocode):
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


@st.cache_data(ttl=60 * 60 * 24)
def cached_geocode_address(q: str):
    """Cached single-address geocode using Nominatim+RateLimiter.

    Returns a geopy Location or None. TTL 24 hours to reuse results.
    """
    try:
        from geopy.geocoders import Nominatim
        from geopy.extra.rate_limiter import RateLimiter

        geolocator_local = Nominatim(user_agent="provider_recommender")
        geocode_local = RateLimiter(geolocator_local.geocode, min_delay_seconds=2, max_retries=3)
        return geocode_local(q, timeout=10)
    except GeocoderUnavailable:
        return None
    except Exception:
        return None


def calculate_distances(user_lat, user_lon, provider_df):
    """Calculate distances in miles from user to each provider using vectorized operations."""

    lat_rad = np.radians(provider_df["Latitude"].to_numpy(dtype=float))
    lon_rad = np.radians(provider_df["Longitude"].to_numpy(dtype=float))
    user_lat_rad = np.radians(user_lat)
    user_lon_rad = np.radians(user_lon)

    valid = ~np.isnan(lat_rad) & ~np.isnan(lon_rad)
    dlat = lat_rad[valid] - user_lat_rad
    dlon = lon_rad[valid] - user_lon_rad
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(user_lat_rad) * np.cos(lat_rad[valid]) * np.sin(dlon / 2) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))
    distances = np.full(len(provider_df), np.nan)
    distances[valid] = 3958.8 * c  # Earth radius in miles

    # Convert NaN to None for consistency with previous behavior
    return [None if np.isnan(d) else float(d) for d in distances]
