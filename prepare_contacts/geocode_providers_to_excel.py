"""Geocode provider addresses and save updated Excel file."""

from __future__ import annotations

import time

import pandas as pd
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


EXCEL_PATH = "data/Ranked_Contacts.xlsx"
df = pd.read_excel(EXCEL_PATH)

if "Full Address" not in df.columns:
    df["Full Address"] = (
        df["Address 1 Line 1"].fillna("")
        + ", "
        + df["Address 1 City"].fillna("")
        + ", "
        + df["Address 1 State"].fillna("")
        + " "
        + df["Address 1 Zip"].fillna("")
    )
    df["Full Address"] = (
        df["Full Address"]
        .str.replace(r",\s*,", ",", regex=True)
        .str.replace(r",\s*$", "", regex=True)
    )

geolocator = Nominatim(user_agent="provider_geocoder")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=3)

if "Latitude" not in df.columns:
    df["Latitude"] = None
if "Longitude" not in df.columns:
    df["Longitude"] = None

for idx, row in df.iterrows():
    if pd.isnull(row["Latitude"]) or pd.isnull(row["Longitude"]):
        address = row["Full Address"]
        try:
            location = geocode(address, timeout=10)
            if location:
                df.at[idx, "Latitude"] = location.latitude
                df.at[idx, "Longitude"] = location.longitude
            else:
                print(f"No result for: {address}")
        except Exception as e:  # noqa: BLE001
            print(f"Error geocoding {address}: {e}")
        time.sleep(1)  # Be nice to the API

print("Saving updated Excel file...")
df.to_excel(EXCEL_PATH, index=False)
print("Done.")
