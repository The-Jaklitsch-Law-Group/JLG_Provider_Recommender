"""Test suite for provider recommendation scoring algorithm.

Tests verify that the scoring system correctly:
- Produces valid scores and rankings
- Favors providers with higher referral counts (higher scores are better)
- Handles edge cases like empty data and minimum referral thresholds
"""
import pandas as pd
import pytest

from src.utils.scoring import recommend_provider


@pytest.fixture
def sample_providers():
    """Sample provider data for testing."""
    return pd.DataFrame(
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


def test_recommend_provider_basic(sample_providers):
    """Test basic recommendation functionality with distance priority."""
    best, scored = recommend_provider(
        sample_providers, distance_weight=0.7, referral_weight=0.2, inbound_weight=0.1, min_referrals=0
    )

    # Verify valid output
    assert best is not None, "Should return a best provider"
    assert scored is not None, "Should return scored DataFrame"
    assert "Score" in scored.columns, "Should have Score column"
    assert len(scored) == 3, "Should score all providers"

    # Verify score properties
    assert scored["Score"].notnull().all(), "All scores should be non-null"
    assert (scored["Score"] >= 0).all(), "Scores should be non-negative"

    # Verify sorting (higher score is better)
    scores = scored["Score"].tolist()
    assert scores == sorted(scores, reverse=True), "Results should be sorted by score (descending)"

    # With high distance weight, closest provider should win
    assert best["Full Name"] == "Alpha", "Closest provider should be ranked first"


def test_higher_referrals_favored():
    """Test that providers with MORE outbound referrals get HIGHER (better) scores."""
    df = pd.DataFrame(
        [
            {
                "Full Name": "Low Experience",
                "Referral Count": 2,
                "Inbound Referral Count": 1,
                "Distance (Miles)": 10.0,
            },
            {
                "Full Name": "High Experience",
                "Referral Count": 100,
                "Inbound Referral Count": 50,
                "Distance (Miles)": 10.0,
            },
        ]
    )

    # Prioritize referral count heavily
    best, scored = recommend_provider(df, distance_weight=0.1, referral_weight=0.7, inbound_weight=0.2, min_referrals=0)

    assert best is not None, "Should return a best provider"
    assert scored is not None, "Should return scored results"
    assert best["Full Name"] == "High Experience", "Provider with more referrals should be ranked first"

    high_exp_score = scored.loc[scored["Full Name"] == "High Experience", "Score"].iloc[0]
    low_exp_score = scored.loc[scored["Full Name"] == "Low Experience", "Score"].iloc[0]
    assert high_exp_score > low_exp_score, "Higher referral count should result in higher (better) score"


def test_inbound_referrals_favored():
    """Test that providers with MORE inbound referrals get HIGHER (better) scores."""
    df = pd.DataFrame(
        [
            {
                "Full Name": "Low Inbound",
                "Referral Count": 10,
                "Inbound Referral Count": 1,
                "Distance (Miles)": 10.0,
            },
            {
                "Full Name": "High Inbound",
                "Referral Count": 10,
                "Inbound Referral Count": 20,
                "Distance (Miles)": 10.0,
            },
        ]
    )

    # Prioritize inbound referrals heavily
    best, scored = recommend_provider(df, distance_weight=0.1, referral_weight=0.1, inbound_weight=0.8, min_referrals=0)

    assert best is not None, "Should return a best provider"
    assert scored is not None, "Should return scored results"
    assert best["Full Name"] == "High Inbound", "Provider with more inbound referrals should be ranked first"

    high_inbound_score = scored.loc[scored["Full Name"] == "High Inbound", "Score"].iloc[0]
    low_inbound_score = scored.loc[scored["Full Name"] == "Low Inbound", "Score"].iloc[0]
    assert high_inbound_score > low_inbound_score, "Higher inbound count should result in higher (better) score"


def test_min_referrals_filter():
    """Test that min_referrals parameter correctly filters providers."""
    df = pd.DataFrame(
        [
            {"Full Name": "Newbie", "Referral Count": 2, "Inbound Referral Count": 0, "Distance (Miles)": 5.0},
            {"Full Name": "Experienced", "Referral Count": 25, "Inbound Referral Count": 10, "Distance (Miles)": 10.0},
        ]
    )

    # Filter out providers with fewer than 10 referrals
    best, scored = recommend_provider(df, distance_weight=0.5, referral_weight=0.5, min_referrals=10)

    assert best is not None, "Should return a provider meeting the threshold"
    assert scored is not None, "Should return scored results"
    assert best["Full Name"] == "Experienced", "Only provider with 10+ referrals should remain"
    assert len(scored) == 1, "Should filter out providers below threshold"


def test_empty_dataframe():
    """Test handling of empty provider DataFrame."""
    df = pd.DataFrame(columns=["Full Name", "Referral Count", "Inbound Referral Count", "Distance (Miles)"])

    best, scored = recommend_provider(df, distance_weight=0.5, referral_weight=0.5)

    assert best is None, "Should return None for empty DataFrame"
    assert scored is None, "Should return None for empty DataFrame"


def test_all_filtered_by_min_referrals():
    """Test handling when all providers are filtered by min_referrals."""
    df = pd.DataFrame(
        [
            {"Full Name": "A", "Referral Count": 2, "Inbound Referral Count": 0, "Distance (Miles)": 5.0},
            {"Full Name": "B", "Referral Count": 3, "Inbound Referral Count": 1, "Distance (Miles)": 10.0},
        ]
    )

    best, scored = recommend_provider(df, distance_weight=0.5, referral_weight=0.5, min_referrals=10)

    assert best is None, "Should return None when all providers filtered"
    assert scored is None, "Should return None when all providers filtered"
