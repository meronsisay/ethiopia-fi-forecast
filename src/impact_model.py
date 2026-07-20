"""
Event Impact Modeling.

Translates impact_link records (event, indicator, direction, magnitude, lag) into a
predictive model: given a baseline value and a set of events, estimate an indicator's
trajectory over time.

Functional form (documented in full in notebooks/impact_modeling.ipynb):
- Each event's effect on an indicator ramps up LINEARLY from 0 (at the event date) to
  its full magnitude (at event_date + lag_months), then holds constant (no decay).
- Effects from multiple events on the same indicator combine ADDITIVELY.
- Categorical magnitude (low/medium/high) is converted to a numeric percentage-point
  value via MAGNITUDE_TO_PP -- an explicit, documented assumption, not derived from data.
- A `dampening` multiplier can down-weight comparable-country-derived estimates
  (evidence_basis in {'literature','theoretical'}) relative to Ethiopia-specific
  empirical evidence. Calibrated in the notebook via the Telebirr validation case.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

from src.data_loader import get_impact_links, get_events, get_observations

MAGNITUDE_TO_PP = {"low": 2.0, "medium": 5.0, "high": 10.0}
DIRECTION_SIGN = {"increase": 1, "decrease": -1}

# Evidence bases that rely on comparable-country evidence rather than Ethiopia-specific
# empirical data -- these are the ones a dampening factor should apply to.
COMPARABLE_COUNTRY_BASES = {"literature", "theoretical"}


@dataclass
class EventEffect:
    event_id: str
    event_name: str
    event_date: pd.Timestamp
    lag_months: float
    magnitude_pp: float          # signed: positive = increase, negative = decrease
    evidence_basis: str
    confidence: str
    comparable_country: str | None


def get_effects_for_indicator(df: pd.DataFrame, indicator_code: str) -> list[EventEffect]:
    """All event effects (from impact_link records) that target a given indicator."""
    links = get_impact_links(df)
    links = links[links["related_indicator"] == indicator_code]
    events = get_events(df).set_index("record_id")

    effects = []
    for _, link in links.iterrows():
        if link["parent_id"] not in events.index:
            continue
        event = events.loc[link["parent_id"]]
        sign = DIRECTION_SIGN.get(link["impact_direction"], 1)
        magnitude_pp = sign * MAGNITUDE_TO_PP.get(link["impact_magnitude"], 0.0)
        effects.append(EventEffect(
            event_id=link["parent_id"],
            event_name=event["indicator"],
            event_date=event["observation_date"],
            lag_months=float(link["lag_months"]) if pd.notna(link["lag_months"]) else 12.0,
            magnitude_pp=magnitude_pp,
            evidence_basis=link["evidence_basis"],
            confidence=link["confidence"],
            comparable_country=link.get("comparable_country"),
        ))
    return effects


def ramp(t: pd.Timestamp, event_date: pd.Timestamp, lag_months: float) -> float:
    """Linear ramp: 0 before the event, rising to 1.0 at event_date + lag_months, then flat."""
    months_elapsed = (t.year - event_date.year) * 12 + (t.month - event_date.month) \
        + (t.day - event_date.day) / 30.44
    if months_elapsed <= 0:
        return 0.0
    if lag_months <= 0:
        return 1.0
    return min(1.0, months_elapsed / lag_months)


def dampening_for(effect: EventEffect, dampening: float) -> float:
    """Apply the dampening factor only to comparable-country-derived effects."""
    return dampening if effect.evidence_basis in COMPARABLE_COUNTRY_BASES else 1.0


def predicted_change(effects: list[EventEffect], t0: pd.Timestamp, t1: pd.Timestamp,
                      dampening: float = 1.0) -> float:
    """
    Predicted change (in percentage points) in an indicator between t0 and t1, summing
    each event's INCREMENTAL ramp contribution over that window (ramp(t1) - ramp(t0)),
    not the full ramp value -- effects already "baked into" the t0 baseline shouldn't be
    double-counted.
    """
    total = 0.0
    for e in effects:
        r0 = ramp(t0, e.event_date, e.lag_months)
        r1 = ramp(t1, e.event_date, e.lag_months)
        total += e.magnitude_pp * (r1 - r0) * dampening_for(e, dampening)
    return total


def validate_indicator(df: pd.DataFrame, indicator_code: str, t0: pd.Timestamp, t1: pd.Timestamp,
                        actual_t0: float, actual_t1: float, dampening: float = 1.0) -> dict:
    """Compare model-predicted change against the actually-observed change."""
    effects = get_effects_for_indicator(df, indicator_code)
    predicted_delta = predicted_change(effects, t0, t1, dampening=dampening)
    predicted_t1 = actual_t0 + predicted_delta
    actual_delta = actual_t1 - actual_t0
    return {
        "indicator_code": indicator_code,
        "t0": t0, "t1": t1,
        "actual_t0": actual_t0, "actual_t1": actual_t1, "actual_delta": actual_delta,
        "predicted_delta": predicted_delta, "predicted_t1": predicted_t1,
        "error_pp": predicted_t1 - actual_t1,
        "n_events": len(effects),
    }


def build_association_matrix(df: pd.DataFrame, indicators: list[str], dampening: float = 1.0) -> pd.DataFrame:
    """
    Rows = events, columns = indicators, values = signed estimated pp effect (full
    magnitude, not time-dependent) -- the static "which event affects which indicator,
    by how much" summary the project brief asks for.
    """
    events = get_events(df).set_index("record_id")
    matrix = pd.DataFrame(index=events["indicator"], columns=indicators, dtype=float)

    for indicator_code in indicators:
        effects = get_effects_for_indicator(df, indicator_code)
        for e in effects:
            event_name = events.loc[e.event_id, "indicator"]
            d = dampening_for(e, dampening)
            matrix.loc[event_name, indicator_code] = e.magnitude_pp * d

    return matrix
