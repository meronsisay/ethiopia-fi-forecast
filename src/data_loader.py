"""
Utilities for loading and exploring the unified Ethiopia financial inclusion dataset.

The dataset uses one shared schema across four record types:
    observation, event, impact_link, target
See README.md at the project root for the full field-by-field description.

This module covers Task 1 (Data Exploration and Enrichment):
    - loading the three raw files
    - schema-level exploration (counts, temporal range, indicator coverage,
      event catalog, impact_link review)
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

# Columns that are genuinely date-like. Note: 'collection_date' is NOT
# included here on purpose -- inspecting the raw file shows some rows have
# free text in that column (e.g. "Account ownership increased from 46% to
# 49%") instead of a date, which is a source-data bug, not a parsing bug.
# Forcing a date parse on it would silently turn that bug into NaT and hide
# it. Flag it as a correction in Task 1 instead of parsing around it.
DATE_COLUMNS = ["observation_date", "period_start", "period_end"]


def load_unified_data(path: Path = RAW_DIR / "ethiopia_fi_unified_data.csv") -> pd.DataFrame:
    """
    Load the unified dataset (observations + events + impact_links + targets).

    observation_date is plain dates ('YYYY-MM-DD'); period_start/period_end
    include a time component ('YYYY-MM-DD HH:MM:SS'). format="mixed" lets
    pandas infer the right format per column without the dateutil fallback
    warning, and without assuming a single format across columns that don't
    share one.
    """
    df = pd.read_csv(path)
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", errors="coerce")
    return df


def load_reference_codes(path: Path = RAW_DIR / "reference_codes.csv") -> pd.DataFrame:
    """Load the controlled vocabulary for categorical fields."""
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Record-type accessors
# ---------------------------------------------------------------------------

def get_observations(df: pd.DataFrame, pillar: str | None = None) -> pd.DataFrame:
    """Return observation rows, optionally filtered to a single pillar (e.g. 'ACCESS')."""
    out = df[df["record_type"] == "observation"]
    if pillar:
        out = out[out["pillar"] == pillar]
    return out


def get_events(df: pd.DataFrame) -> pd.DataFrame:
    """Return event rows (policies, launches, milestones). `pillar` is intentionally empty."""
    return df[df["record_type"] == "event"]


def get_impact_links(df: pd.DataFrame, pillar: str | None = None) -> pd.DataFrame:
    """Return impact_link rows, optionally filtered by the pillar of the affected indicator."""
    out = df[df["record_type"] == "impact_link"]
    if pillar:
        out = out[out["pillar"] == pillar]
    return out


def get_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Return official policy target rows."""
    return df[df["record_type"] == "target"]


def link_events_to_impacts(df: pd.DataFrame, pillar: str | None = None) -> pd.DataFrame:
    """
    Join impact_link rows to their parent event, so you get event details
    alongside the estimated effect on a given indicator.

    Note: both `event` and `impact_link` rows have a `category` column, so
    after the merge you'll get `category_impact` / `category_event`, not a
    bare `category` -- same for every other shared column name.
    """
    impacts = get_impact_links(df, pillar=pillar)
    events = get_events(df)
    merged = impacts.merge(
        events,
        left_on="parent_id",
        right_on="record_id",
        suffixes=("_impact", "_event"),
    )
    return merged


# ---------------------------------------------------------------------------
# Task 1 "Explore the Data" helpers
# ---------------------------------------------------------------------------

def summarize_counts(df: pd.DataFrame) -> dict[str, pd.Series]:
    """
    Counts by record_type, pillar, source_type, and confidence --
    Task 1 step 2, bullet 1.
    """
    return {
        "record_type": df["record_type"].value_counts(dropna=False),
        "pillar": df["pillar"].value_counts(dropna=False),
        "source_type": df["source_type"].value_counts(dropna=False),
        "confidence": df["confidence"].value_counts(dropna=False),
    }


def get_temporal_range(df: pd.DataFrame) -> pd.Series:
    """Min/max observation_date for observation rows -- Task 1 step 2, bullet 2."""
    obs = get_observations(df)
    return obs["observation_date"].agg(["min", "max"])


def get_indicator_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each indicator_code found in observation rows: how many records,
    and what date range they span -- Task 1 step 2, bullet 3.
    """
    obs = get_observations(df)
    coverage = obs.groupby("indicator_code").agg(
        n_records=("record_id", "count"),
        first_observed=("observation_date", "min"),
        last_observed=("observation_date", "max"),
    )
    return coverage.sort_values("n_records", ascending=False)


def get_events_catalog(df: pd.DataFrame) -> pd.DataFrame:
    """Events with their category and date, sorted chronologically -- Task 1 step 2, bullet 4."""
    events = get_events(df)
    cols = ["record_id", "indicator", "category", "observation_date", "source_name"]
    cols = [c for c in cols if c in events.columns]
    return events[cols].sort_values("observation_date")


def review_impact_links(df: pd.DataFrame) -> pd.DataFrame:
    """
    Every impact_link joined to its parent event, showing what relationship
    is being claimed -- Task 1 step 2, bullet 5.
    """
    merged = link_events_to_impacts(df)
    cols = [
        "record_id_impact", "indicator_event", "category_event",
        "pillar_impact", "related_indicator_impact", "impact_direction_impact",
        "impact_magnitude_impact", "lag_months_impact", "evidence_basis_impact",
        "confidence_impact",
    ]
    cols = [c for c in cols if c in merged.columns]
    return merged[cols]


def find_schema_violations(df: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows whose categorical values aren't in reference_codes.csv, and
    events that have a pillar filled in (they shouldn't, per the schema's
    core design principle) -- feeds directly into your "corrections" list.
    """
    issues = []

    # Events must NOT have a pillar assigned
    bad_events = get_events(df)[get_events(df)["pillar"].notna()]
    for _, row in bad_events.iterrows():
        issues.append({
            "record_id": row["record_id"],
            "issue": "event has a pillar pre-assigned (should be empty)",
            "value": row["pillar"],
        })

    # Check categorical fields against reference_codes
    if {"field", "code"}.issubset(reference.columns):
        for field in ["record_type", "pillar", "category", "confidence", "source_type"]:
            if field not in df.columns:
                continue
            valid_codes = set(reference.loc[reference["field"] == field, "code"].dropna())
            if not valid_codes:
                continue
            actual = df[field].dropna().unique()
            invalid = [v for v in actual if v not in valid_codes]
            for v in invalid:
                issues.append({
                    "record_id": None,
                    "issue": f"invalid '{field}' value not in reference_codes",
                    "value": v,
                })

    return pd.DataFrame(issues)


def print_schema_report(df: pd.DataFrame, reference: pd.DataFrame) -> None:
    """Human-readable dump of everything Task 1 step 2 asks for."""
    print("=== Record counts ===")
    for name, counts in summarize_counts(df).items():
        print(f"\n-- {name} --")
        print(counts)

    print("\n=== Temporal range (observations) ===")
    print(get_temporal_range(df))

    print("\n=== Indicator coverage ===")
    print(get_indicator_coverage(df))

    print("\n=== Events catalog ===")
    print(get_events_catalog(df).to_string(index=False))

    print("\n=== Impact links ===")
    print(review_impact_links(df).to_string(index=False))

    print("\n=== Potential schema violations / corrections needed ===")
    violations = find_schema_violations(df, reference)
    print(violations.to_string(index=False) if not violations.empty else "None found")


if __name__ == "__main__":
    data = load_unified_data()
    ref = load_reference_codes()
    print_schema_report(data, ref)
