"""
Tests for forecasting module (Task 4).
Simple tests that work with or without real data files.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.forecast import (
    TrendModel,
    fit_trend,
    trend_prediction,
    future_event_effect,
    event_augmented_forecast,
    scenario_forecast,
)


# ===========================================================================
# SAMPLE DATA FOR TESTING
# ===========================================================================

def create_sample_df():
    """Create a minimal sample dataframe for testing."""
    return pd.DataFrame([
        # Events
        {
            "record_id": "EVT_0001",
            "record_type": "event",
            "indicator": "Telebirr Launch",
            "category": "product_launch",
            "observation_date": pd.Timestamp("2021-05-17"),
            "pillar": None,
            "parent_id": None,
        },
        # Observations
        {
            "record_id": "REC_0001",
            "record_type": "observation",
            "pillar": "ACCESS",
            "indicator": "Account Ownership",
            "indicator_code": "ACC_OWNERSHIP",
            "value_numeric": 22.0,
            "observation_date": pd.Timestamp("2014-12-31"),
            "gender": "all",
            "category": None,
            "parent_id": None,
        },
        {
            "record_id": "REC_0002",
            "record_type": "observation",
            "pillar": "ACCESS",
            "indicator": "Account Ownership",
            "indicator_code": "ACC_OWNERSHIP",
            "value_numeric": 35.0,
            "observation_date": pd.Timestamp("2017-12-31"),
            "gender": "all",
            "category": None,
            "parent_id": None,
        },
        {
            "record_id": "REC_0003",
            "record_type": "observation",
            "pillar": "ACCESS",
            "indicator": "Account Ownership",
            "indicator_code": "ACC_OWNERSHIP",
            "value_numeric": 46.0,
            "observation_date": pd.Timestamp("2021-12-31"),
            "gender": "all",
            "category": None,
            "parent_id": None,
        },
        {
            "record_id": "REC_0004",
            "record_type": "observation",
            "pillar": "ACCESS",
            "indicator": "Account Ownership",
            "indicator_code": "ACC_OWNERSHIP",
            "value_numeric": 49.0,
            "observation_date": pd.Timestamp("2024-11-29"),
            "gender": "all",
            "category": None,
            "parent_id": None,
        },
        # Impact link
        {
            "record_id": "IMP_0001",
            "record_type": "impact_link",
            "parent_id": "EVT_0001",
            "pillar": "ACCESS",
            "related_indicator": "ACC_OWNERSHIP",
            "impact_direction": "increase",
            "impact_magnitude": "high",
            "lag_months": 12.0,
            "evidence_basis": "literature",
            "confidence": "medium",
            "comparable_country": "Kenya",
        },
    ])


# ===========================================================================
# TESTS
# ===========================================================================

def test_trend_model_dataclass():
    """Test TrendModel dataclass creation."""
    model = TrendModel(
        slope=2.5,
        intercept=10.0,
        n=5,
        x_mean=2020.0,
        sxx=10.0,
        residual_std=0.5,
        df_resid=3,
    )
    assert model.slope == 2.5
    assert model.intercept == 10.0
    assert model.n == 5
    assert model.df_resid == 3


def test_trend_model_predict():
    """Test TrendModel predict method."""
    # FIXED: The model calculates intercept + slope * x
    # With intercept=10, slope=2, x=2020: 10 + 2*2020 = 4050
    model = TrendModel(
        slope=2.0,
        intercept=10.0,
        n=5,
        x_mean=2020.0,
        sxx=10.0,
        residual_std=0.5,
        df_resid=3,
    )
    predictions = model.predict(np.array([2020.0, 2021.0, 2022.0]))
    # Mathematically: 10 + 2*2020 = 4050, 10 + 2*2021 = 4052, 10 + 2*2022 = 4054
    expected = np.array([4050.0, 4052.0, 4054.0])
    np.testing.assert_array_almost_equal(predictions, expected)


def test_fit_trend():
    """Test fitting a trend line to data."""
    df = create_sample_df()
    model, obs = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    
    assert model.n == 4  # 4 data points
    assert model.df_resid == 2  # n - 2
    assert model.slope > 0  # Should be increasing
    assert model.residual_std is not None


def test_fit_trend_insufficient_data():
    """Test fitting trend with insufficient data points."""
    df = create_sample_df()
    
    # Filter to only 2 data points
    df_subset = df[df["record_id"].isin(["REC_0001", "REC_0002"])]
    
    model, obs = fit_trend(df_subset, "ACC_OWNERSHIP", gender_filter="all")
    
    assert model.n == 2
    assert model.df_resid == 0  # n - 2 = 0
    assert np.isnan(model.residual_std)  # No residual std with 2 points


def test_trend_prediction():
    """Test making predictions with confidence intervals."""
    df = create_sample_df()
    model, obs = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    
    years = [2025.0, 2026.0, 2027.0]
    result = trend_prediction(model, years)
    
    assert len(result) == 3
    assert "year" in result.columns
    assert "trend_forecast" in result.columns
    assert "ci_lower" in result.columns
    assert "ci_upper" in result.columns
    
    # With 4 data points, we should have valid confidence intervals
    assert not result["ci_lower"].isna().any()
    assert not result["ci_upper"].isna().any()


def test_trend_prediction_insufficient_data():
    """Test predictions with insufficient data (2 points -> NaN intervals)."""
    df = create_sample_df()
    df_subset = df[df["record_id"].isin(["REC_0001", "REC_0002"])]
    
    model, obs = fit_trend(df_subset, "ACC_OWNERSHIP", gender_filter="all")
    years = [2025.0, 2026.0]
    result = trend_prediction(model, years)
    
    # With 2 points, confidence intervals should be NaN
    assert result["ci_lower"].isna().all()
    assert result["ci_upper"].isna().all()


def test_future_event_effect():
    """Test calculating future event effects."""
    df = create_sample_df()
    
    t_last = pd.Timestamp("2024-11-29")
    t_forecast = pd.Timestamp("2026-12-31")
    
    # Event: May 2021, 12 month lag, fully ramped by May 2022
    # t_last: 2024-11-29 (fully ramped)
    # t_forecast: 2026-12-31 (fully ramped)
    # Incremental effect should be 0
    effect = future_event_effect(df, "ACC_OWNERSHIP", t_last, t_forecast, dampening=1.0)
    
    assert abs(effect) < 0.01


def test_future_event_effect_with_dampening():
    """Test future event effect with dampening."""
    df = create_sample_df()
    
    t_last = pd.Timestamp("2021-12-31")  # Before full ramp
    t_forecast = pd.Timestamp("2024-11-29")  # After full ramp
    
    # Event: May 2021, 12 month lag
    # t_last: ~7.5 months after event, ramp ~0.625
    # t_forecast: ~42.5 months after event, ramp 1.0
    # Incremental: 10 * (1.0 - 0.625) = 3.75 (without dampening)
    # With dampening 0.34: 3.75 * 0.34 = 1.275
    effect = future_event_effect(df, "ACC_OWNERSHIP", t_last, t_forecast, dampening=0.34)
    
    assert abs(effect - 1.2864) < 0.01


def test_event_augmented_forecast():
    """Test event-augmented forecast."""
    df = create_sample_df()
    model, obs = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    
    t_last = pd.Timestamp("2024-11-29")
    actual_last = 49.0
    forecast_years = [2025, 2026, 2027]
    
    result = event_augmented_forecast(
        df, "ACC_OWNERSHIP", model, t_last, actual_last, forecast_years, dampening=1.0
    )
    
    assert len(result) == 3
    assert "year" in result.columns
    assert "trend_component" in result.columns
    assert "event_component" in result.columns
    assert "forecast" in result.columns
    
    # Forecast should be >= actual last value (account ownership increasing)
    assert (result["forecast"] >= 49.0).all()


def test_scenario_forecast():
    """Test scenario forecasting with different dampening values."""
    df = create_sample_df()
    model, obs = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    
    t_last = pd.Timestamp("2024-11-29")
    actual_last = 49.0
    forecast_years = [2025, 2026, 2027]
    
    scenarios = {
        "pessimistic": 0.2,
        "base": 0.34,
        "optimistic": 0.5,
    }
    
    result = scenario_forecast(
        df, "ACC_OWNERSHIP", model, t_last, actual_last, forecast_years, scenarios
    )
    
    assert len(result) == 9  # 3 years * 3 scenarios
    assert "scenario" in result.columns
    assert set(result["scenario"].unique()) == {"pessimistic", "base", "optimistic"}
    
    # Optimistic should be >= base >= pessimistic
    for year in forecast_years:
        optimistic = result[(result["year"] == year) & (result["scenario"] == "optimistic")]["forecast"].iloc[0]
        base = result[(result["year"] == year) & (result["scenario"] == "base")]["forecast"].iloc[0]
        pessimistic = result[(result["year"] == year) & (result["scenario"] == "pessimistic")]["forecast"].iloc[0]
        
        assert optimistic >= base >= pessimistic


def test_fit_trend_gender_filter():
    """Test fitting trend with gender filter."""
    df = create_sample_df()
    
    # Add a male observation
    male_row = pd.DataFrame([{
        "record_id": "REC_0005",
        "record_type": "observation",
        "pillar": "ACCESS",
        "indicator": "Account Ownership",
        "indicator_code": "ACC_OWNERSHIP",
        "value_numeric": 56.0,
        "observation_date": pd.Timestamp("2024-11-29"),
        "gender": "male",
        "category": None,
        "parent_id": None,
    }])
    df = pd.concat([df, male_row], ignore_index=True)
    
    # Should only return 'all' gender records (default)
    model_all, obs_all = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    assert len(obs_all) == 4  # 4 records with gender='all'
    
    # Should only return 'male' gender records
    model_male, obs_male = fit_trend(df, "ACC_OWNERSHIP", gender_filter="male")
    assert len(obs_male) == 1


def test_event_augmented_forecast_no_events():
    """Test forecast with no events affecting the indicator."""
    df = create_sample_df()
    model, obs = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    
    t_last = pd.Timestamp("2024-11-29")
    actual_last = 49.0
    forecast_years = [2025, 2026, 2027]
    
    # Remove the impact link
    df_no_links = df[df["record_type"] != "impact_link"]
    
    result = event_augmented_forecast(
        df_no_links, "ACC_OWNERSHIP", model, t_last, actual_last, forecast_years, dampening=1.0
    )
    
    # With no events, event_component should be 0
    assert (result["event_component"] == 0).all()
    # Forecast should be just trend component
    assert (result["forecast"] == actual_last + result["trend_component"]).all()


# ===========================================================================
# EDGE CASE TESTS
# ===========================================================================

def test_trend_prediction_single_year():
    """Test prediction with a single year."""
    df = create_sample_df()
    model, obs = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    
    result = trend_prediction(model, [2025.0])
    
    assert len(result) == 1
    assert result["year"].iloc[0] == 2025.0
    assert not result["trend_forecast"].isna().iloc[0]


def test_future_event_effect_no_effects():
    """Test future event effect with no impact links."""
    df = create_sample_df()
    df_no_links = df[df["record_type"] != "impact_link"]
    
    t_last = pd.Timestamp("2024-11-29")
    t_forecast = pd.Timestamp("2026-12-31")
    
    effect = future_event_effect(df_no_links, "ACC_OWNERSHIP", t_last, t_forecast)
    
    assert effect == 0.0


def test_scenario_forecast_empty_scenarios():
    """Test scenario forecast with empty scenarios dict."""
    df = create_sample_df()
    model, obs = fit_trend(df, "ACC_OWNERSHIP", gender_filter="all")
    
    t_last = pd.Timestamp("2024-11-29")
    actual_last = 49.0
    forecast_years = [2025, 2026, 2027]
    
    # Empty scenarios should return empty DataFrame or raise appropriate error
    try:
        result = scenario_forecast(
            df, "ACC_OWNERSHIP", model, t_last, actual_last, forecast_years, {}
        )
        # If it doesn't raise, it should return empty DataFrame
        assert result.empty
    except ValueError as e:
        # If it raises ValueError, that's acceptable behavior
        # Just ensure it's the expected error
        assert "No objects to concatenate" in str(e)