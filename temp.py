import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Load your Excel file
df = pd.read_excel("./data/Ranked_Contacts.xlsx")

# Set up geocoder
geolocator = Nominatim(user_agent="my_geocoder")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

# Geocode each address
latitudes, longitudes = [], []
for i, row in df.iterrows():
    full_address = f"{row['Address 1 Line 1']}, {row['Address 1 City']}, {row['Address 1 State']} {row['Address 1 Zip']}"
    try:
        location = geocode(full_address)
        latitudes.append(location.latitude if location else None)
        longitudes.append(location.longitude if location else None)
    except Exception:
        latitudes.append(None)
        longitudes.append(None)

# Append lat/lon to DataFrame
df["Latitude"] = latitudes
df["Longitude"] = longitudes

# Save new Excel file
df.to_excel("./data/Ranked_Providers_with_Loc.xlsx", index=False)
print("Geocoded file saved.")
