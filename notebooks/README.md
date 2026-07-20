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

## Exploratory Data Analysis

*Overview.* `notebooks/eda.ipynb` summarizes the enriched dataset (73 records) by
record_type/pillar/source_type, builds a temporal coverage heatmap (indicator × year) to
show exactly where the data is thin, plots the confidence-level distribution, and explicitly
lists the 21 of 29 indicators that have only a single observation — no trend possible for those
without further enrichment.

*Access.* Plots the account ownership trajectory (2014–2024) and the growth rate between each
survey round. Investigates the 2021→2024 slowdown (+3pp despite tens of millions of new mobile
money accounts) using the registered-vs-active gap from Task 1: ~90M registered mobile accounts
(≈120 per 100 adults) against Findex's 9.45% active-use figure... Gender gap is charted
(56%/36%, 2024), with an explicit caveat that a second source reports 57%/42% for the same
round — flagged, not resolved. Urban/rural comparison is called out as **not possible**: every
record has `location = "national"`.

*Usage.* Mobile money penetration and digital payment adoption trends (2 data points each —
directional, not fitted), plus a cross-sectional payment-use-cases snapshot.

*Infrastructure.* Surfaces a "funnel" pattern — broad 4G coverage vs. lagging smartphone
penetration (16%) and phone ownership (41%) — and flags that no true infrastructure-density
indicator exists yet.

*Events.* Full timeline + Access overlay, with an explicit note that Findex's 3-year survey
cadence means Telebirr/Safaricom/M-Pesa's individual effects can't be separated.

*Correlation.* Deliberately skips a full correlation heatmap (mathematically meaningless with
only 2 shared years per pair) in favor of a co-movement table and an impact_link evidence
summary.

*6 key findings + a ranked data quality assessment* — see notebook for full detail.

**Run time:** ~15 seconds.

## Event Impact Modeling

*Understand the impact data.* `notebooks/impact_modeling.ipynb` loads all 17
`impact_link` records and joins each one back to its parent `event` via `parent_id`,
producing a single event → indicator → direction/magnitude/lag/evidence summary. Modeling
logic lives in `src/impact_model.py`, not the notebook itself, so Task 4 can import and reuse
it directly.

*Model design.* Each event's effect on an indicator is a **linear ramp** — 0 at the event
date, full estimated magnitude at `event_date + lag_months`, flat afterward — and effects on
the same indicator from different events combine **additively**. Categorical magnitude
(`low/medium/high`) maps to `2/5/10` percentage points, an explicit starting assumption, not
something fit from data.

*Comparable-country evidence.* 7 of 17 impact_links already cite a comparable country. A real
gap was found and closed here: no link connected Telebirr's launch to `ACC_MM_ACCOUNT`. Added
one, sourced from Jack & Suri's NBER paper on Kenya's M-Pesa (~65% household adoption within
3 years) — deliberately left un-calibrated at first.

*Validation.* Tested the naive model against the brief's own case: Telebirr → `ACC_MM_ACCOUNT`,
2021→2024. **The naive, Kenya-calibrated model overshot badly** — predicted 18.6%, actual was
9.45%, about 2x too high. Used the miss as the finding, not something to hide.

*Refinement.* Solved for the dampening factor that makes the model match reality exactly
(**0.342**), applied only to comparable-country effects — Ethiopia-specific empirical effects
keep full weight. Documented as calibrated from a single data point, not a proven constant.

*Deliverables.* Association matrix (heatmap + CSV, initial + refined, saved to
`data/processed/`), full methodology writeup, and a calibration summary CSV for Task 4.

**Run time:** ~10 seconds.