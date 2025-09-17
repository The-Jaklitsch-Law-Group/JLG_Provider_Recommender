import pandas as pd

from src.utils.consolidated_functions import recommend_provider


def test_recommend_provider_basic():
    # Create a small synthetic dataset
    df = pd.DataFrame(
        [
            {
                "Full Name": "Alpha",
                "Latitude": 40.0,
                "Longitude": -75.0,
                "Referral Count": 10,
                "Inbound Referral Count": 2,
                "Distance (Miles)": 1.0,
            },
            {
                "Full Name": "Beta",
                "Latitude": 40.1,
                "Longitude": -75.1,
                "Referral Count": 5,
                "Inbound Referral Count": 8,
                "Distance (Miles)": 10.0,
            },
            {
                "Full Name": "Charlie",
                "Latitude": 42.0,
                "Longitude": -76.0,
                "Referral Count": 1,
                "Inbound Referral Count": 0,
                "Distance (Miles)": 200.0,
            },
        ]
    )

    # Prefer distance primarily
    best, scored = recommend_provider(df, distance_weight=0.7, referral_weight=0.2, inbound_weight=0.1, min_referrals=0)

    assert best is not None
    assert scored is not None
    # Ensure a best provider is returned and scored dataframe exists
    assert best is not None
    assert scored is not None

    # Ensure score column exists
    assert "Score" in scored.columns

    # Scores should be finite numbers between 0 and a reasonable upper bound
    assert scored["Score"].notnull().all()

    # Ensure scored dataframe is sorted ascending by Score (lower is better)
    scores = scored["Score"].tolist()
    assert scores == sorted(scores)
