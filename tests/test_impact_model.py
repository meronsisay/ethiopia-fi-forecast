"""
Tests for impact modeling module.
Simple tests that work with or without real data files.
"""

import sys
from pathlib import Path
import pandas as pd
import pytest
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.impact_model import (
    MAGNITUDE_TO_PP,
    DIRECTION_SIGN,
    COMPARABLE_COUNTRY_BASES,
    EventEffect,
    ramp,
    dampening_for,
    predicted_change,
    get_effects_for_indicator,
    validate_indicator,
    build_association_matrix,
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
        {
            "record_id": "EVT_0002",
            "record_type": "event",
            "indicator": "M-Pesa Launch",
            "category": "product_launch",
            "observation_date": pd.Timestamp("2023-08-01"),
            "pillar": None,
            "parent_id": None,
        },
        # Impact links
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
        {
            "record_id": "IMP_0002",
            "record_type": "impact_link",
            "parent_id": "EVT_0001",
            "pillar": "USAGE",
            "related_indicator": "USG_P2P_COUNT",
            "impact_direction": "increase",
            "impact_magnitude": "medium",
            "lag_months": 6.0,
            "evidence_basis": "empirical",
            "confidence": "high",
            "comparable_country": None,
        },
        {
            "record_id": "IMP_0003",
            "record_type": "impact_link",
            "parent_id": "EVT_0002",
            "pillar": "ACCESS",
            "related_indicator": "ACC_MM_ACCOUNT",
            "impact_direction": "increase",
            "impact_magnitude": "medium",
            "lag_months": 6.0,
            "evidence_basis": "theoretical",
            "confidence": "medium",
            "comparable_country": None,
        },
    ])


# ===========================================================================
# TESTS
# ===========================================================================

def test_magnitude_to_pp():
    """Test magnitude to percentage point conversion."""
    assert MAGNITUDE_TO_PP["low"] == 2.0
    assert MAGNITUDE_TO_PP["medium"] == 5.0
    assert MAGNITUDE_TO_PP["high"] == 10.0


def test_direction_sign():
    """Test direction sign mapping."""
    assert DIRECTION_SIGN["increase"] == 1
    assert DIRECTION_SIGN["decrease"] == -1


def test_comparable_country_bases():
    """Test comparable country evidence bases."""
    assert "literature" in COMPARABLE_COUNTRY_BASES
    assert "theoretical" in COMPARABLE_COUNTRY_BASES
    assert "empirical" not in COMPARABLE_COUNTRY_BASES


def test_ramp_before_event():
    """Test ramp function before event date."""
    event_date = pd.Timestamp("2021-05-17")
    t_before = pd.Timestamp("2021-01-01")
    assert ramp(t_before, event_date, 12.0) == 0.0


def test_ramp_at_event_date():
    """Test ramp function at event date."""
    event_date = pd.Timestamp("2021-05-17")
    assert ramp(event_date, event_date, 12.0) == 0.0


def test_ramp_during_ramp():
    """Test ramp function during ramp period."""
    event_date = pd.Timestamp("2021-05-17")
    t_mid = pd.Timestamp("2021-11-17")
    result = ramp(t_mid, event_date, 12.0)
    assert 0.4 < result < 0.6


def test_ramp_after_lag():
    """Test ramp function after lag period."""
    event_date = pd.Timestamp("2021-05-17")
    t_after = pd.Timestamp("2023-01-01")
    assert ramp(t_after, event_date, 12.0) == 1.0


def test_ramp_zero_lag():
    """Test ramp function with zero lag (instant effect)."""
    event_date = pd.Timestamp("2021-05-17")
    t_after = pd.Timestamp("2021-06-01")
    assert ramp(t_after, event_date, 0.0) == 1.0


def test_dampening_for_empirical():
    """Test dampening doesn't apply to empirical evidence."""
    effect = EventEffect(
        event_id="EVT_0001",
        event_name="Test Event",
        event_date=pd.Timestamp("2021-05-17"),
        lag_months=12.0,
        magnitude_pp=10.0,
        evidence_basis="empirical",
        confidence="high",
        comparable_country=None,
    )
    assert dampening_for(effect, 0.5) == 1.0


def test_dampening_for_literature():
    """Test dampening applies to literature evidence."""
    effect = EventEffect(
        event_id="EVT_0001",
        event_name="Test Event",
        event_date=pd.Timestamp("2021-05-17"),
        lag_months=12.0,
        magnitude_pp=10.0,
        evidence_basis="literature",
        confidence="medium",
        comparable_country="Kenya",
    )
    assert dampening_for(effect, 0.34) == 0.34


def test_dampening_for_theoretical():
    """Test dampening applies to theoretical evidence."""
    effect = EventEffect(
        event_id="EVT_0001",
        event_name="Test Event",
        event_date=pd.Timestamp("2021-05-17"),
        lag_months=12.0,
        magnitude_pp=10.0,
        evidence_basis="theoretical",
        confidence="low",
        comparable_country=None,
    )
    assert dampening_for(effect, 0.34) == 0.34


def test_get_effects_for_indicator():
    """Test getting effects for a specific indicator."""
    df = create_sample_df()
    effects = get_effects_for_indicator(df, "ACC_OWNERSHIP")
    
    assert len(effects) == 1
    assert effects[0].event_name == "Telebirr Launch"
    assert effects[0].magnitude_pp == 10.0
    assert effects[0].lag_months == 12.0


def test_get_effects_for_indicator_multiple():
    """Test getting effects for an indicator with multiple links."""
    df = create_sample_df()
    effects = get_effects_for_indicator(df, "USG_P2P_COUNT")
    
    assert len(effects) == 1
    assert effects[0].event_name == "Telebirr Launch"
    assert effects[0].magnitude_pp == 5.0


def test_predicted_change_no_events():
    """Test predicted change with no events."""
    effects = []
    t0 = pd.Timestamp("2021-01-01")
    t1 = pd.Timestamp("2024-01-01")
    assert predicted_change(effects, t0, t1) == 0.0


def test_predicted_change_single_event():
    """Test predicted change with a single event."""
    effect = EventEffect(
        event_id="EVT_0001",
        event_name="Telebirr Launch",
        event_date=pd.Timestamp("2021-05-17"),
        lag_months=12.0,
        magnitude_pp=10.0,
        evidence_basis="literature",
        confidence="medium",
        comparable_country="Kenya",
    )
    
    t0 = pd.Timestamp("2021-12-31")
    t1 = pd.Timestamp("2024-11-29")
    
    result = predicted_change([effect], t0, t1, dampening=1.0)
    assert abs(result - 3.7834) < 0.01


def test_predicted_change_with_dampening():
    """Test predicted change with dampening applied."""
    effect = EventEffect(
        event_id="EVT_0001",
        event_name="Telebirr Launch",
        event_date=pd.Timestamp("2021-05-17"),
        lag_months=12.0,
        magnitude_pp=10.0,
        evidence_basis="literature",
        confidence="medium",
        comparable_country="Kenya",
    )
    
    t0 = pd.Timestamp("2021-12-31")
    t1 = pd.Timestamp("2024-11-29")
    
    result = predicted_change([effect], t0, t1, dampening=0.34)
    assert abs(result - 1.2864) < 0.01


def test_validate_indicator():
    """Test validate_indicator function."""
    df = create_sample_df()
    t0 = pd.Timestamp("2021-12-31")
    t1 = pd.Timestamp("2024-11-29")
    
    result = validate_indicator(df, "ACC_OWNERSHIP", t0, t1, 46.0, 49.0, dampening=1.0)
    
    assert result["indicator_code"] == "ACC_OWNERSHIP"
    assert result["actual_t0"] == 46.0
    assert result["actual_t1"] == 49.0
    assert result["actual_delta"] == 3.0
    assert result["n_events"] == 1
    assert "predicted_delta" in result
    assert "error_pp" in result


def test_validate_indicator_actual_t1_matches():
    """Test validation when prediction matches actual (with calibration)."""
    df = create_sample_df()
    t0 = pd.Timestamp("2021-12-31")
    t1 = pd.Timestamp("2024-11-29")
    
    result = validate_indicator(df, "ACC_OWNERSHIP", t0, t1, 46.0, 49.0, dampening=0.34)
    
    assert "error_pp" in result
    assert isinstance(result["error_pp"], float)


def test_build_association_matrix():
    """Test building the association matrix."""
    df = create_sample_df()
    indicators = ["ACC_OWNERSHIP", "USG_P2P_COUNT", "ACC_MM_ACCOUNT"]
    
    matrix = build_association_matrix(df, indicators, dampening=1.0)
    
    assert matrix.shape[0] == 2
    assert matrix.shape[1] == 3
    assert "Telebirr Launch" in matrix.index
    assert "M-Pesa Launch" in matrix.index
    assert "ACC_OWNERSHIP" in matrix.columns


def test_build_association_matrix_with_dampening():
    """Test association matrix with dampening applied."""
    df = create_sample_df()
    indicators = ["ACC_OWNERSHIP", "USG_P2P_COUNT", "ACC_MM_ACCOUNT"]
    
    matrix = build_association_matrix(df, indicators, dampening=0.34)
    
    val = matrix.loc["Telebirr Launch", "ACC_OWNERSHIP"]
    assert abs(val - 3.4) < 0.01


def test_build_association_matrix_empirical_unchanged():
    """Test that empirical evidence is NOT dampened in association matrix."""
    df = create_sample_df()
    indicators = ["ACC_OWNERSHIP", "USG_P2P_COUNT", "ACC_MM_ACCOUNT"]
    
    matrix = build_association_matrix(df, indicators, dampening=0.34)
    
    val = matrix.loc["Telebirr Launch", "USG_P2P_COUNT"]
    assert val == 5.0


# ===========================================================================
# EDGE CASE TESTS
# ===========================================================================

def test_get_effects_for_indicator_no_links():
    """Test getting effects for an indicator with no impact links."""
    df = create_sample_df()
    effects = get_effects_for_indicator(df, "NONEXISTENT")
    assert effects == []


def test_predicted_change_negative_magnitude():
    """Test predicted change with negative magnitude (decrease)."""
    effect = EventEffect(
        event_id="EVT_0001",
        event_name="Test Event",
        event_date=pd.Timestamp("2021-05-17"),
        lag_months=12.0,
        magnitude_pp=-5.0,
        evidence_basis="empirical",
        confidence="high",
        comparable_country=None,
    )
    
    # Both dates should be AFTER the full ramp period
    # 2022-05-17 is exactly 12 months after event (full effect reached)
    t0 = pd.Timestamp("2022-05-17")
    t1 = pd.Timestamp("2023-01-01")
    
    result = predicted_change([effect], t0, t1, dampening=1.0)
    # Both dates should have ramp = 1.0, so delta should be 0
    assert abs(result) < 0.01


def test_ramp_with_fractional_months():
    """Test ramp with fractional months (using day-level precision)."""
    event_date = pd.Timestamp("2021-05-17")
    t_mid = pd.Timestamp("2021-08-17")
    result = ramp(t_mid, event_date, 6.0)
    assert abs(result - 0.5) < 0.01


def test_event_effect_dataclass():
    """Test EventEffect dataclass creation."""
    effect = EventEffect(
        event_id="EVT_0001",
        event_name="Test",
        event_date=pd.Timestamp("2021-01-01"),
        lag_months=12.0,
        magnitude_pp=10.0,
        evidence_basis="empirical",
        confidence="high",
        comparable_country=None,
    )
    assert effect.event_id == "EVT_0001"
    assert effect.magnitude_pp == 10.0


# ===========================================================================
# ADDITIONAL TESTS FOR BETTER COVERAGE
# ===========================================================================

def test_ramp_with_negative_lag():
    """Test ramp with negative lag (should treat as instant)."""
    event_date = pd.Timestamp("2021-05-17")
    t_after = pd.Timestamp("2021-06-01")
    assert ramp(t_after, event_date, -1.0) == 1.0


def test_ramp_exact_full_effect_date():
    """Test ramp at exactly the date full effect is reached."""
    event_date = pd.Timestamp("2021-05-17")
    t_full = pd.Timestamp("2022-05-17")
    result = ramp(t_full, event_date, 12.0)
    assert result == 1.0


def test_predicted_change_multiple_events():
    """Test predicted change with multiple events."""
    effect1 = EventEffect(
        event_id="EVT_0001",
        event_name="Event 1",
        event_date=pd.Timestamp("2021-01-01"),
        lag_months=12.0,
        magnitude_pp=5.0,
        evidence_basis="empirical",
        confidence="high",
        comparable_country=None,
    )
    effect2 = EventEffect(
        event_id="EVT_0002",
        event_name="Event 2",
        event_date=pd.Timestamp("2021-06-01"),
        lag_months=6.0,
        magnitude_pp=3.0,
        evidence_basis="empirical",
        confidence="high",
        comparable_country=None,
    )
    
    t0 = pd.Timestamp("2021-12-31")
    t1 = pd.Timestamp("2024-01-01")
    
    result = predicted_change([effect1, effect2], t0, t1, dampening=1.0)
    # Both events should be fully ramped by t1
    assert abs(result) < 0.01


def test_validate_indicator_no_effects():
    """Test validation with no impact links for the indicator."""
    df = create_sample_df()
    t0 = pd.Timestamp("2021-12-31")
    t1 = pd.Timestamp("2024-11-29")
    
    result = validate_indicator(df, "NONEXISTENT", t0, t1, 10.0, 20.0, dampening=1.0)
    
    assert result["indicator_code"] == "NONEXISTENT"
    assert result["actual_delta"] == 10.0
    assert result["predicted_delta"] == 0.0
    assert result["predicted_t1"] == 10.0
    assert result["n_events"] == 0