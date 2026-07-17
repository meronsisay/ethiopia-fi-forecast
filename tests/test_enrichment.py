"""
Tests for dataset enrichment functionality.
Simple tests that work with or without data files.
"""

import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.enrichment import (
    add_record,
    append_log_entry,
    next_record_id,
    _is_duplicate,
    DEDUP_KEYS,
    REQUIRED_FIELDS,
    LOG_PATH,
)


# ============================
# SAMPLE DATA FOR TESTING 
# ============================

def create_sample_df():
    """Create a minimal sample dataframe for testing."""
    return pd.DataFrame([
        {
            "record_id": "REC_0001",
            "record_type": "observation",
            "pillar": "ACCESS",
            "indicator": "Account Ownership",
            "indicator_code": "ACC_OWNERSHIP",
            "value_numeric": 49.0,
            "observation_date": pd.Timestamp("2024-11-29"),
            "source_name": "Global Findex",
            "source_url": "https://example.com",
            "confidence": "high",
            "category": None,
            "parent_id": None,
            "related_indicator": None,
            "impact_direction": None,
            "impact_magnitude": None,
            "lag_months": None,
            "evidence_basis": None,
        },
        {
            "record_id": "EVT_0001",
            "record_type": "event",
            "pillar": None,
            "category": "product_launch",
            "indicator": "Telebirr Launch",
            "indicator_code": None,
            "value_numeric": None,
            "observation_date": pd.Timestamp("2021-05-17"),
            "source_name": "Ethio Telecom",
            "source_url": "https://example.com",
            "confidence": "high",
            "parent_id": None,
            "related_indicator": None,
            "impact_direction": None,
            "impact_magnitude": None,
            "lag_months": None,
            "evidence_basis": None,
        },
        {
            "record_id": "IMP_0001",
            "record_type": "impact_link",
            "pillar": "ACCESS",
            "parent_id": "EVT_0001",
            "related_indicator": "ACC_OWNERSHIP",
            "impact_direction": "increase",
            "impact_magnitude": "high",
            "lag_months": 12.0,
            "evidence_basis": "literature",
            "indicator": None,
            "indicator_code": None,
            "value_numeric": None,
            "observation_date": None,
            "source_name": None,
            "source_url": None,
            "confidence": None,
            "category": None,
        }
    ])


# ===========================================================================
# TESTS
# ===========================================================================

def test_next_record_id_observation():
    """Test generating next record ID for observations."""
    df = create_sample_df()
    next_id = next_record_id(df, "observation")
    assert next_id == "REC_0002"  # REC_0001 exists, so next is REC_0002


def test_next_record_id_event():
    """Test generating next record ID for events."""
    df = create_sample_df()
    next_id = next_record_id(df, "event")
    assert next_id == "EVT_0002"  # EVT_0001 exists


def test_next_record_id_impact():
    """Test generating next record ID for impact links."""
    df = create_sample_df()
    next_id = next_record_id(df, "impact_link")
    assert next_id == "IMP_0002"  # IMP_0001 exists


def test_next_record_id_empty():
    """Test generating first record ID when no records exist."""
    df = pd.DataFrame(columns=["record_id"])
    next_id = next_record_id(df, "observation")
    assert next_id == "REC_0001"
    
    next_id = next_record_id(df, "event")
    assert next_id == "EVT_0001"


def test_add_record_observation():
    """Test adding a new observation record."""
    df = create_sample_df()
    
    new_record = {
        "record_type": "observation",
        "pillar": "USAGE",
        "indicator": "Digital Payment Usage",
        "indicator_code": "USG_DIGITAL_PAYMENT",
        "value_numeric": 21.0,
        "observation_date": "2024-11-29",
        "source_name": "Global Findex",
        "source_url": "https://example.com",
        "confidence": "high",
    }
    
    df_new, added = add_record(df, new_record)
    assert added is True
    assert len(df_new) == len(df) + 1
    assert df_new.iloc[-1]["record_id"] == "REC_0002"
    assert df_new.iloc[-1]["pillar"] == "USAGE"


def test_add_record_event():
    """Test adding a new event record."""
    df = create_sample_df()
    
    new_record = {
        "record_type": "event",
        "category": "policy",
        "indicator": "NFIS-II Strategy",
        "observation_date": "2021-09-01",
        "source_name": "NBE",
    }
    
    df_new, added = add_record(df, new_record)
    assert added is True
    assert len(df_new) == len(df) + 1
    assert df_new.iloc[-1]["record_id"] == "EVT_0002"
    assert df_new.iloc[-1]["category"] == "policy"


def test_add_record_impact_link():
    """Test adding a new impact_link record."""
    df = create_sample_df()
    
    new_record = {
        "record_type": "impact_link",
        "parent_id": "EVT_0001",
        "pillar": "USAGE",
        "related_indicator": "USG_DIGITAL_PAYMENT",
        "impact_direction": "increase",
        "impact_magnitude": "medium",
        "lag_months": 6.0,
        "evidence_basis": "empirical",
    }
    
    df_new, added = add_record(df, new_record)
    assert added is True
    assert len(df_new) == len(df) + 1
    assert df_new.iloc[-1]["record_id"] == "IMP_0002"
    assert df_new.iloc[-1]["parent_id"] == "EVT_0001"


def test_add_record_missing_required_fields():
    """Test that missing required fields raise ValueError."""
    df = create_sample_df()
    
    # Missing required 'pillar' field
    new_record = {
        "record_type": "observation",
        "indicator": "Account Ownership",
        "indicator_code": "ACC_OWNERSHIP",
        "value_numeric": 50.0,
        "observation_date": "2024-11-29",
        "source_name": "Global Findex",
        "source_url": "https://example.com",
        "confidence": "high",
    }
    
    with pytest.raises(ValueError) as excinfo:
        add_record(df, new_record)
    assert "Missing required fields" in str(excinfo.value)


def test_add_record_event_with_pillar_raises_error():
    """Test that events with pillar assigned raise ValueError."""
    df = create_sample_df()
    
    # Event with pillar (not allowed by schema)
    new_record = {
        "record_type": "event",
        "pillar": "ACCESS",  # This should raise an error!
        "category": "product_launch",
        "indicator": "New Product",
        "observation_date": "2025-01-01",
        "source_name": "Source",
    }
    
    with pytest.raises(ValueError) as excinfo:
        add_record(df, new_record)
    assert "Events must NOT have a pillar assigned" in str(excinfo.value)


def test_is_duplicate_observation():
    """Test duplicate detection for observations."""
    df = create_sample_df()
    
    # Same as existing REC_0001
    duplicate = {
        "record_type": "observation",
        "pillar": "ACCESS",
        "indicator": "Account Ownership",
        "indicator_code": "ACC_OWNERSHIP",
        "value_numeric": 49.0,
        "observation_date": "2024-11-29",
        "source_name": "Global Findex",
        "source_url": "https://example.com",
        "confidence": "high",
    }
    
    assert _is_duplicate(df, duplicate) is True
    
    # Different value
    not_duplicate = duplicate.copy()
    not_duplicate["value_numeric"] = 50.0
    assert _is_duplicate(df, not_duplicate) is False


def test_is_duplicate_event():
    """Test duplicate detection for events."""
    df = create_sample_df()
    
    # Same as existing EVT_0001
    duplicate = {
        "record_type": "event",
        "category": "product_launch",
        "indicator": "Telebirr Launch",
        "observation_date": "2021-05-17",
        "source_name": "Ethio Telecom",
    }
    
    assert _is_duplicate(df, duplicate) is True


def test_is_duplicate_impact():
    """Test duplicate detection for impact links."""
    df = create_sample_df()
    
    # Same as existing IMP_0001
    duplicate = {
        "record_type": "impact_link",
        "parent_id": "EVT_0001",
        "pillar": "ACCESS",
        "related_indicator": "ACC_OWNERSHIP",
        "impact_direction": "increase",
        "impact_magnitude": "high",
        "lag_months": 12.0,
        "evidence_basis": "literature",
    }
    
    assert _is_duplicate(df, duplicate) is True


def test_add_record_prevents_duplicate():
    """Test that add_record prevents duplicate records."""
    df = create_sample_df()
    
    # Try to add a duplicate of EVT_0001
    duplicate = {
        "record_type": "event",
        "category": "product_launch",
        "indicator": "Telebirr Launch",
        "observation_date": "2021-05-17",
        "source_name": "Ethio Telecom",
    }
    
    df_new, added = add_record(df, duplicate)
    assert added is False
    assert len(df_new) == len(df)  # No change


def test_append_log_entry(tmp_path):
    """Test appending log entries."""
    # Use a temporary path for testing
    global LOG_PATH
    original_log_path = LOG_PATH
    test_log_path = tmp_path / "test_enrichment_log.md"
    
    # Monkey patch LOG_PATH for this test
    import src.enrichment
    src.enrichment.LOG_PATH = test_log_path
    
    try:
        # First entry should be added
        result = append_log_entry(
            record_id="REC_9999",
            record_type="observation",
            description="Test record",
            source_url="https://example.com",
            original_text="Test original text",
            confidence="high",
            collected_by="Tester",
            notes="Test notes",
        )
        assert result is True
        assert test_log_path.exists()
        
        # Second entry with same header should be skipped
        result = append_log_entry(
            record_id="REC_9999",
            record_type="observation",
            description="Test record",
            source_url="https://example.com",
            original_text="Different text",
            confidence="high",
            collected_by="Tester",
            notes="Different notes",
        )
        assert result is False
        
    finally:
        # Restore original LOG_PATH
        import src.enrichment
        src.enrichment.LOG_PATH = original_log_path


def test_required_fields_exist():
    """Test that REQUIRED_FIELDS is properly defined."""
    assert "observation" in REQUIRED_FIELDS
    assert "event" in REQUIRED_FIELDS
    assert "impact_link" in REQUIRED_FIELDS
    
    # Check observation required fields
    assert "pillar" in REQUIRED_FIELDS["observation"]
    assert "indicator_code" in REQUIRED_FIELDS["observation"]
    assert "value_numeric" in REQUIRED_FIELDS["observation"]
    
    # Check event required fields
    assert "category" in REQUIRED_FIELDS["event"]
    assert "indicator" in REQUIRED_FIELDS["event"]
    
    # Check impact_link required fields
    assert "parent_id" in REQUIRED_FIELDS["impact_link"]
    assert "related_indicator" in REQUIRED_FIELDS["impact_link"]


def test_dedup_keys_exist():
    """Test that DEDUP_KEYS is properly defined."""
    assert "observation" in DEDUP_KEYS
    assert "event" in DEDUP_KEYS
    assert "impact_link" in DEDUP_KEYS