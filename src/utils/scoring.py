"""Distance calculation and provider recommendation scoring."""
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd


def calculate_distances(user_lat: float, user_lon: float, provider_df: pd.DataFrame) -> List[Optional[float]]:
    lat_arr = np.radians(provider_df["Latitude"].to_numpy(dtype=float))
    lon_arr = np.radians(provider_df["Longitude"].to_numpy(dtype=float))
    user_lat_rad = np.radians(user_lat)
    user_lon_rad = np.radians(user_lon)

    valid = ~np.isnan(lat_arr) & ~np.isnan(lon_arr)
    dlat = lat_arr[valid] - user_lat_rad
    dlon = lon_arr[valid] - user_lon_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(user_lat_rad) * np.cos(lat_arr[valid]) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    distances = np.full(len(provider_df), np.nan)
    distances[valid] = 3958.8 * c

    return [None if np.isnan(d) else float(d) for d in distances]


def recommend_provider(
    provider_df: pd.DataFrame,
    distance_weight: float = 0.5,
    referral_weight: float = 0.5,
    inbound_weight: float = 0.0,
    min_referrals: Optional[int] = None,
) -> Tuple[Optional[pd.Series], Optional[pd.DataFrame]]:
    df = provider_df.copy(deep=True)
    df = df[df["Distance (Miles)"].notnull() & df["Referral Count"].notnull()]
    if min_referrals is not None:
        df = df[df["Referral Count"] >= min_referrals]

    if df.empty:
        return None, None

    referral_range = df["Referral Count"].max() - df["Referral Count"].min()
    dist_range = df["Distance (Miles)"].max() - df["Distance (Miles)"].min()

    df["norm_rank"] = (df["Referral Count"] - df["Referral Count"].min()) / referral_range if referral_range != 0 else 0
    df["norm_dist"] = (df["Distance (Miles)"] - df["Distance (Miles)"].min()) / dist_range if dist_range != 0 else 0

    df["Score"] = distance_weight * df["norm_dist"] + referral_weight * df["norm_rank"]

    if inbound_weight > 0 and "Inbound Referral Count" in df.columns:
        inbound_df = df[df["Inbound Referral Count"].notnull()].copy()
        if not inbound_df.empty:
            inbound_range = inbound_df["Inbound Referral Count"].max() - inbound_df["Inbound Referral Count"].min()
            if inbound_range != 0:
                inbound_df["norm_inbound"] = (
                    inbound_df["Inbound Referral Count"] - inbound_df["Inbound Referral Count"].min()
                ) / inbound_range
            else:
                inbound_df["norm_inbound"] = 0

            inbound_df["Score"] = (
                distance_weight * inbound_df["norm_dist"]
                + referral_weight * inbound_df["norm_rank"]
                + inbound_weight * inbound_df["norm_inbound"]
            )

            df.loc[inbound_df.index, "Score"] = inbound_df["Score"]
            df.loc[inbound_df.index, "norm_inbound"] = inbound_df["norm_inbound"]

    if distance_weight > referral_weight:
        sort_keys = ["Score", "Distance (Miles)", "Referral Count"]
    else:
        sort_keys = ["Score", "Referral Count", "Distance (Miles)"]

    if "Inbound Referral Count" in df.columns:
        sort_keys.append("Inbound Referral Count")

    candidate_keys = sort_keys + ["Full Name"]
    sort_keys_final = [k for k in candidate_keys if k in df.columns]
    ascending = [True] * len(sort_keys_final)

    df_sorted = df.sort_values(by=sort_keys_final, ascending=ascending).reset_index(drop=True)
    best = df_sorted.iloc[0]
    return best, df_sorted
