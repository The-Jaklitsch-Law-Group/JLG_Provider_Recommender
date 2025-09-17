import pandas as pd
import pytest

from src.utils import providers


def test_calculate_distances_wrapper_monkeypatched(monkeypatch):
    calls = {}

    def fake_calc(user_lat, user_lon, df):
        # record and return a predictable result
        calls["args"] = (user_lat, user_lon, df.copy())
        return [0.1 for _ in range(len(df))]

    monkeypatch.setattr(providers, "_calculate_distances", fake_calc)

    df = pd.DataFrame({"Latitude": [40.0, 41.0], "Longitude": [-74.0, -75.0]})
    result = providers.calculate_distances(40.0, -74.0, df)

    assert isinstance(result, list)
    assert result == [0.1, 0.1]
    assert "args" in calls


def test_recommend_provider_wrapper_monkeypatched(monkeypatch):
    # Prepare dummy outputs
    dummy_best = pd.Series({"Full Name": "Dr. X", "Score": 0.0})
    dummy_df = pd.DataFrame([{"Full Name": "Dr. X", "Score": 0.0}])

    def fake_recommend(df, distance_weight=0.5, referral_weight=0.5, inbound_weight=0.0, min_referrals=None):
        return dummy_best, dummy_df

    monkeypatch.setattr(providers, "_recommend_provider", fake_recommend)

    input_df = pd.DataFrame({"Distance (Miles)": [1.0], "Referral Count": [5], "Full Name": ["Dr. X"]})
    best, scored = providers.recommend_provider(input_df, distance_weight=0.7, referral_weight=0.2, inbound_weight=0.1)

    assert isinstance(best, pd.Series)
    assert isinstance(scored, pd.DataFrame)
    assert best["Full Name"] == "Dr. X"


def test_validate_address_wrapper(monkeypatch):
    def fake_validate(address):
        return True, "ok"

    monkeypatch.setattr(providers, "_validate_address", fake_validate)

    ok, msg = providers.validate_address("123 Main St, Anytown, NY")
    assert ok is True
    assert msg == "ok"


def test_validate_and_clean_coordinates_wrapper(monkeypatch):
    df_in = pd.DataFrame({"Latitude": ["40.0"], "Longitude": ["-74.0"]})

    def fake_validate(df):
        # simulate conversion to numeric
        out = df.copy()
        out["Latitude"] = out["Latitude"].astype(float)
        out["Longitude"] = out["Longitude"].astype(float)
        return out

    monkeypatch.setattr(providers, "_validate_and_clean_coordinates", fake_validate)

    out = providers.validate_and_clean_coordinates(df_in)
    assert out["Latitude"].dtype == float
    assert out["Longitude"].dtype == float


def test_validate_provider_data_wrapper(monkeypatch):
    def fake_validate(df):
        return True, "All good"

    monkeypatch.setattr(providers, "_validate_provider_data", fake_validate)

    ok, msg = providers.validate_provider_data(pd.DataFrame())
    assert ok is True
    assert msg == "All good"


def test_geocode_wrappers_monkeypatched(monkeypatch):
    monkeypatch.setattr(providers, "_geocode_address_with_cache", lambda addr: (40.0, -74.0))
    monkeypatch.setattr(providers, "_cached_geocode_address", lambda addr: object())

    coords = providers.geocode_address_with_cache("123 Main St")
    assert coords == (40.0, -74.0)

    loc = providers.cached_geocode_address("123 Main St")
    assert loc is not None
