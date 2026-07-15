"""
Utilities for loading the unified Ethiopia financial inclusion dataset.

The dataset uses one shared schema across four record types:
    observation, event, impact_link, target
See README.md at the project root for the full field-by-field description.
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"


def load_unified_data(path: Path = RAW_DIR / "ethiopia_fi_unified_data.csv") -> pd.DataFrame:
    """Load the unified dataset (observations + events + impact_links + targets)."""
    # Specify format to avoid the warning
    df = pd.read_csv(
        path, 
        parse_dates=["observation_date", "period_start", "period_end", "collection_date"],
        date_format="%Y-%m-%d %H:%M:%S"  # This tells pandas the exact format
    )
    return df


def load_reference_codes(path: Path = RAW_DIR / "reference_codes.csv") -> pd.DataFrame:
    """Load the controlled vocabulary for categorical fields."""
    return pd.read_csv(path)


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


if __name__ == "__main__":
    data = load_unified_data()
    print(f"Loaded {len(data)} records")
    print(data["record_type"].value_counts())