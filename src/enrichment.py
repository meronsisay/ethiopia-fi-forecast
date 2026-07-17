"""
Helpers for dataset enrichment: adding new observation / event /
impact_link rows to the unified schema, and logging each addition in the
format data_enrichment_log.md expects.

Both add_record() and append_log_entry() are idempotent: running the same
notebook cell twice will NOT create duplicate rows or duplicate log entries.
"""
from pathlib import Path
from datetime import date
import pandas as pd

LOG_PATH = Path(__file__).resolve().parents[1] / "data_enrichment_log.md"

REQUIRED_FIELDS = {
    "observation": ["pillar", "indicator", "indicator_code", "value_numeric",
                     "observation_date", "source_name", "source_url", "confidence"],
    "event": ["category", "indicator", "observation_date", "source_name"],
    "impact_link": ["parent_id", "pillar", "related_indicator", "impact_direction",
                     "impact_magnitude", "lag_months", "evidence_basis"],
}

# Which fields define "this is the same fact" for each record_type, used to
# detect duplicates before inserting.
DEDUP_KEYS = {
    "observation": ["indicator_code", "observation_date", "value_numeric"],
    "event": ["indicator", "observation_date"],
    "impact_link": ["parent_id", "related_indicator", "pillar"],
}


def next_record_id(df: pd.DataFrame, record_type: str) -> str:
    """Generate the next sequential ID (REC_/EVT_/IMP_) for a given record_type."""
    prefix = {"observation": "REC", "target": "REC", "event": "EVT", "impact_link": "IMP"}[record_type]
    existing = df.loc[df["record_id"].str.startswith(prefix), "record_id"]
    nums = existing.str.extract(r"(\d+)")[0].dropna().astype(int)
    next_num = (nums.max() + 1) if len(nums) else 1
    return f"{prefix}_{next_num:04d}"


DATE_LIKE_FIELDS = {"observation_date", "period_start", "period_end"}
NUMERIC_LIKE_FIELDS = {"value_numeric", "lag_months"}


def _is_duplicate(df: pd.DataFrame, record: dict) -> bool:
    """
    Check whether a record with the same defining fields already exists.

    Date fields need special handling: after a save-to-CSV + reload cycle,
    df's observation_date is a pandas Timestamp, but a freshly-written record
    dict still has a plain string. Comparing str(Timestamp) to str("2024-10-24")
    fails (Timestamp's str includes "00:00:00"), so date-like keys are
    normalized through pd.to_datetime before comparing, everything else
    compares as a string.
    """
    record_type = record["record_type"]
    keys = DEDUP_KEYS.get(record_type)
    if not keys:
        return False
    subset = df[df["record_type"] == record_type]
    if subset.empty:
        return False
    mask = pd.Series(True, index=subset.index)
    for k in keys:
        if k not in record or record[k] is None:
            continue
        if k in DATE_LIKE_FIELDS:
            mask &= (pd.to_datetime(subset[k]) == pd.to_datetime(record[k]))
        elif k in NUMERIC_LIKE_FIELDS:
            # Compare as floats (with tolerance), not strings -- a CSV
            # round-trip turns 90_000_000 (int) into 90000000.0 (float),
            # and str(90000000) != str(90000000.0), which would otherwise
            # make every numeric-keyed duplicate check silently fail.
            mask &= pd.to_numeric(subset[k], errors="coerce").sub(float(record[k])).abs().lt(1e-9)
        else:
            mask &= (subset[k].astype(str) == str(record[k]))
    return bool(mask.any())


def add_record(df: pd.DataFrame, record: dict) -> tuple[pd.DataFrame, bool]:
    """
    Append one new row to the unified dataset, unless an equivalent row
    already exists (see DEDUP_KEYS) -- in which case df is returned
    unchanged. Returns (df, added) so callers know whether to log it.
    """
    record_type = record.get("record_type")
    if record_type not in REQUIRED_FIELDS:
        raise ValueError(f"record_type must be one of {list(REQUIRED_FIELDS)}, got {record_type!r}")

    missing = [f for f in REQUIRED_FIELDS[record_type] if not record.get(f)]
    if missing:
        raise ValueError(f"Missing required fields for {record_type}: {missing}")

    if record_type == "event" and record.get("pillar"):
        raise ValueError("Events must NOT have a pillar assigned (see README schema design principle)")

    if _is_duplicate(df, record):
        return df, False

    record = dict(record)  # don't mutate caller's dict
    record.setdefault("record_id", next_record_id(df, record_type))

    # Normalize date-like fields to pd.Timestamp so the new row's dtype
    # matches df's (which load_unified_data already parsed as datetime).
    # Without this, concatenating a plain string into a Timestamp column
    # silently degrades the whole column to dtype=object, which then
    # breaks downstream groupby/min/max calls (e.g. get_indicator_coverage).
    for field in DATE_LIKE_FIELDS:
        if record.get(field):
            record[field] = pd.to_datetime(record[field])

    new_row = pd.DataFrame([record])
    return pd.concat([df, new_row], ignore_index=True), True


def append_log_entry(record_id: str, record_type: str, description: str,
                      source_url: str, original_text: str, confidence: str,
                      collected_by: str, notes: str,
                      collection_date: str | None = None) -> bool:
    """
    Append one formatted entry to data_enrichment_log.md, unless a matching
    entry (same record_id AND description) is already logged. Returns True
    if it wrote a new entry, False if it skipped a duplicate.
    """
    collection_date = collection_date or date.today().isoformat()
    header = f"### `{record_id}` — `{record_type}` — {description}"

    if LOG_PATH.exists():
        existing_text = LOG_PATH.read_text()
        if header in existing_text:
            return False

    entry = f"""
{header}

- **source_url:** {source_url}
- **original_text:** "{original_text}"
- **confidence:** {confidence}
- **collected_by:** {collected_by}
- **collection_date:** {collection_date}
- **notes:** {notes}
"""
    with open(LOG_PATH, "a") as f:
        f.write(entry)
    return True
