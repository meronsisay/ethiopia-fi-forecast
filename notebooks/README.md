# Notebooks

## Data Exploration and Enrichment

*Exploration.* `notebooks/data_exploration_enrichment.ipynb` loads all three raw files
and reports record counts by type/pillar/source/confidence, the temporal range of
observations, per-indicator coverage, the full event catalog, and every impact_link joined
back to its parent event. Also runs an automated check against `reference_codes.csv` and the
schema's core rule that events never get a pillar pre-assigned.

*Corrections.* One dating error found by inspection (`REC_0004`/`REC_0005` were labeled 2021
but match 2024 Findex figures) was corrected and sourced. A second issue — two secondary
sources reporting different numbers for the same 2024 gender gap (56/36 vs 57/42) — was
flagged as unresolved rather than silently picking one, pending a primary-source check.

*Enrichment.* Dataset grew from 57 → 73 records:
- **15 new observations**, including closing a gap where `USG_DIGITAL_PAYMENT` — one of the
  two indicators this whole project forecasts — previously had zero data points; plus new
  income- and gender-disaggregated figures for both Access and Usage, and two infrastructure
  enablers (smartphone penetration, phone ownership).
- **1 new event**: an NBE mobile money transaction-limit directive (Oct 2023) missing from
  the starter catalog.
- **3 new impact_links** connecting events to indicators not previously captured, including
  linking Telebirr's launch to agent-network growth.

Every addition is logged in `data_enrichment_log.md` with source URL, exact quote,
confidence rating, and the reasoning for why it's useful. `add_record()` and
`append_log_entry()` in `src/enrichment.py` are idempotent, so the notebook can be re-run
top to bottom without ever creating duplicate rows or duplicate log entries.

**Run time:** ~30 seconds