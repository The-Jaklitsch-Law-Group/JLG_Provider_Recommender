import numpy as np
import pandas as pd

from app import filter_providers_by_radius


def make_df(distances_miles):
    return pd.DataFrame(
        {"Full Name": [f"P{i}" for i in range(len(distances_miles))], "Distance (Miles)": distances_miles}
    )


def test_filter_providers_by_radius_filters_correctly():
    # Prepare data: distances in miles roughly corresponding to 10, 30, 40, 100 km
    # Convert km to miles for test clarity
    miles_per_km = 0.621371
    distances_km = [10, 30, 40, 100]
    distances_miles = [d * miles_per_km for d in distances_km]

    df = make_df(distances_miles)

    # Filter with max_radius_miles ~= 31 (50 km) should keep first three (10,30,40)
    result = filter_providers_by_radius(df, 50 * miles_per_km)
    assert len(result) == 3
    assert list(result["Full Name"]) == ["P0", "P1", "P2"]

    # Filter with max_radius_km = 20 should keep only the first
    result2 = filter_providers_by_radius(df, 20 * miles_per_km)
    assert len(result2) == 1
    assert list(result2["Full Name"]) == ["P0"]
