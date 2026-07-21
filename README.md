# Ethiopia Financial Inclusion — Forecasting System

## The Problem

Ethiopia is in the middle of a fast digital financial transformation. Telebirr has grown to
over 54 million users since 2021. M-Pesa entered the market in 2023 and already has 10+
million users. Interoperable P2P digital transfers have overtaken ATM cash withdrawals for
the first time. And yet, per the 2024 Global Findex survey, only **49%** of Ethiopian adults
have a financial account — just 3 percentage points higher than in 2021.

Selam Analytics was engaged by a consortium of development finance institutions, mobile money
operators, and the National Bank of Ethiopia to answer three questions:

1. **What drives financial inclusion in Ethiopia?**
2. **How do events** — product launches, policy changes, infrastructure investments — **affect
   inclusion outcomes?**
3. **How did inclusion change in 2025, and where is it headed in 2026-2027?**

This repo builds a forecasting system that answers all three, using the World Bank's Global
Findex framework's two core dimensions:

- **Access** — Account Ownership Rate
- **Usage** — Digital Payment Adoption Rate

## Approach

Rather than a flat spreadsheet of numbers, the dataset uses a unified `observation` / `event`
/ `impact_link` / `target` schema, so that policies, product launches, and infrastructure
milestones can be modeled as *drivers* of Access and Usage, not just listed alongside them.
Events deliberately never get a pillar (Access/Usage/etc.) pre-assigned — Telebirr's launch,
for example, affects both, so labeling it as one up front would bias the analysis before it
starts. `impact_link` records carry that interpretation instead, each one joined back to its
parent event via `parent_id`, with a direction, magnitude, lag, and evidence basis.

### Schema at a glance

| record_type   | `category` filled? | `pillar` filled? | What it represents |
|---------------|---------------------|-------------------|---------------------|
| `observation` | no                  | yes               | A measured value (survey/operator/infra data) |
| `event`       | yes                 | **no** (never pre-assigned) | A policy/launch/milestone |
| `impact_link` | no                  | yes               | Modeled effect of an event (via `parent_id`) on an indicator |
| `target`      | no                  | yes               | An official policy goal |

## What Was Done

Starting from a 57-record starter dataset, the project moved through five stages — data
enrichment, exploratory analysis, event-impact modeling, forecasting, and a dashboard — each
building directly on the last. The dataset grew to **75 records** along the way, every
addition sourced and logged in `reports/data_enrichment_log.md`.

### 1. Data Exploration and Enrichment

Loaded and validated the starter dataset against `reference_codes.csv` and the schema's core
rule (events never get a pillar). Found and corrected one dating error (`REC_0004`/`REC_0005`
were labeled 2021 but match 2024 Findex figures), and flagged — rather than silently
resolved — a real conflict between two secondary sources reporting different numbers for the
same 2024 gender gap (56%/36% vs. 57%/42%).

Enriched the dataset with 15 new sourced observations, closing the biggest gap: `USG_DIGITAL_PAYMENT`
— one of the two indicators this whole project forecasts — had **zero** data points before
enrichment. Also added income- and gender-disaggregated figures for both Access and Usage, two
infrastructure enablers (smartphone penetration, phone ownership), one new regulatory event
(an NBE mobile money transaction-limit directive), and new impact_links. `add_record()` and
`append_log_entry()` in `src/enrichment.py` are idempotent, so the enrichment notebook can be
re-run top to bottom without ever duplicating a row or log entry.

### 2. Exploratory Data Analysis

**Key findings:**
- **21 of 29 indicators have only 1 observation** — no trend possible without further data.
- Account ownership: 22% (2014) → 35% (2017) → 46% (2021) → **49% (2024)** — only **+3pp**
  most recently, despite Telebirr and M-Pesa launching in between.
- **Best-supported explanation for the slowdown**: ~90M *registered* mobile money accounts
  (≈120 per 100 adults) vs. only **9.45%** *active*, Findex-reported use — a large
  registered-vs-active gap. Most new mobile accounts likely belong to people who were already
  banked, not new-to-finance users.
- **Gender gap**: ~20pp in Access (56% men vs. 36% women, 2024 — flagged as contested, see
  above), **13pp** in Usage (26% men vs. 13% women).
- **Agent network** grew from only 200k → 216k agents (2022-2024) — far slower than account
  growth, a plausible capacity bottleneck on genuinely reaching new users.
- **Infrastructure "funnel"**: broad 4G coverage vs. only 41% phone ownership and 16%
  smartphone penetration — the device layer, not the network, looks like the binding
  constraint on further digital Usage growth.
- Correlation analysis intentionally **skips a full heatmap** — most indicators share only 2
  time points, making Pearson correlation statistically meaningless there — using a
  co-movement table and `impact_link` evidence summary instead.

### 3. Event Impact Modeling

Joined all `impact_link` records back to their parent events, producing a full event →
indicator → direction/magnitude/lag/evidence summary. Modeled each event's effect as a
**linear ramp** (0 at the event date, full magnitude at `event_date + lag_months`, flat
after), with effects from multiple events combining **additively**.

Found and closed a real gap: no link connected Telebirr's launch to `ACC_MM_ACCOUNT`, despite
Telebirr being the product that created Ethiopia's mobile money market. Added one, sourced
from comparable-country evidence (Kenya's M-Pesa: ~65% household adoption within 3 years).

**Validated against the brief's own test case** (Telebirr → `ACC_MM_ACCOUNT`, 2021-2024): the
naive, Kenya-calibrated model overshot badly — predicted 18.6%, actual was 9.45%, ~2x too
high. Rather than hide the miss, used it as the finding: Ethiopia's mobile money adoption pace
runs at roughly a third of Kenya's, consistent with Task 2's own evidence (pre-existing
banking, stalled agent growth, later/fragmented competition).

**Refined** by solving for the dampening factor that matches the actual value exactly
(**0.342**), applied only to comparable-country-sourced effects — Ethiopia-specific empirical
effects (e.g. Telebirr → `USG_TELEBIRR_USERS`) keep full weight, since nothing in the
validation cast doubt on those specifically.

> **In plain terms, for stakeholders:** I tested the model against one real historical
> outcome before trusting it with a forecast. Our first attempt overestimated Ethiopia's
> mobile money growth by roughly 2x. We corrected for that gap and now apply the correction
> consistently — but because it's based on a single test case, treat every event-driven number
> in this project as a reasonable estimate, not a precise prediction.

**How to read the association matrix:**
- **Rows** are events, **columns** are indicators. **Green cells** mean the event is estimated
  to *increase* that indicator; a **blank cell** means no modeled relationship was found —
  not that the effect is zero, just that no evidence links them (yet).
- **Darker shading = larger estimated effect**, in percentage points, after calibration.
- Confidence isn't shown directly on the matrix — pair it with the confidence table below.
  Telebirr and Fayda are the two largest calibrated Access drivers; **nothing currently links
  any event to Usage directly**, which is why the Usage forecast (Section 4) has no
  event-driven component at all.

### 4. Forecasting Access and Usage (2025-2027)

> **Plain-language summary:** I expect Access (account ownership) to reach roughly **59% by
> 2027**, with moderate confidence — it's backed by 5 real data points and a validated
> event-impact model. Our Usage (digital payment) forecast of **~19% by 2027** is much less
> reliable: it's based on only 2 data points, and no event in our model — not Telebirr, not
> M-Pesa — is currently linked to it directly, so this number is closer to a rough guess than
> a solid prediction. Read the technical detail below before quoting either number externally.

Closed one more gap first: added the missing 2011 Access data point (14%, Global Findex), so
the trend regression spans the full "5 points over 13 years" the brief describes.

Combined a trend regression (linear-in-years, chosen over log-linear because Access's growth
is *decelerating* — +8pp, +13pp, +11pp, +3pp between rounds) with Task 3's calibrated
event-effect model, and produced three scenarios (pessimistic/base/optimistic) by varying the
calibrated dampening factor — the project's single largest, most explicit source of
uncertainty.

**Forecast (base case):**

| Year | Access (Account Ownership) | Usage (Digital Payment) |
|------|------------------------------|----------------------------|
| 2025 | ~53% | ~20% |
| 2026 | ~56% | ~20% |
| 2027 | ~59% | ~19% |

**Limitations**
- `USG_DIGITAL_PAYMENT`'s statistical confidence interval correctly comes back **undefined
  (NaN)** — 2 historical points give zero residual degrees of freedom. Its scenario range is
  the only real uncertainty measure available for that indicator.
- **Zero `impact_link` records target `USG_DIGITAL_PAYMENT` directly** — existing links target
  related sub-indicators (P2P count, M-Pesa activity), not this aggregate code. Usage's
  forecast therefore gets no event-driven boost at all, and its downward slope should be
  treated with real skepticism, not confidence.
- The Access trend's own statistical CI (47%-74% by 2027) is mathematically valid but too wide
  to be decision-useful — the scenario range is the more practically useful band.

### 5. Dashboard

`dashboard/app.py` — a 4-page Streamlit app (Overview, Trends, Forecasts, Inclusion
Projections) reading directly from the tracked dataset and Task 3/4's saved outputs in
`data/processed/`, with 4+ interactive Plotly visualizations, a model selector (trend CI vs.
event-augmented scenario range), a scenario selector, and CSV downloads. Explicitly surfaces
this project's open data-quality conflicts (the gender gap and digital-payment discrepancies)
on the dashboard itself rather than hiding them behind clean-looking metric cards. The
Inclusion Projections page shows both the brief's referenced 60% milestone *and* the dataset's
actual official target (NFIS-II, 70%) side by side, since they're genuinely different numbers.

## Project Structure

```
ethiopia-fi-forecast/
├── .github/workflows/unittests.yml   # CI: runs pytest on every push/PR
├── .streamlit/config.toml            # Cream/whitish dashboard theme
├── data/
│   ├── raw/                          # Only ethiopia_fi_unified_data.csv is tracked (enriched dataset)
│   └── processed/                    # Task 3/4 output: association matrices, calibration, forecast table (tracked)
├── notebooks/
│   ├── data_exploration_enrichment.ipynb   # Task 1
│   ├── eda.ipynb                           # Task 2
│   ├── impact_modeling.ipynb               # Task 3
│   └── forecasting.ipynb                   # Task 4
├── src/
│   ├── data_loader.py                 # Load + explore the unified dataset
│   ├── enrichment.py                  # Idempotent add_record() / append_log_entry() helpers
│   ├── impact_model.py                # Event-effect ramp model, association matrix, validation
│   └── forecast.py                    # Trend regression + event-augmented + scenario forecasting
├── dashboard/app.py                   # Streamlit dashboard (Task 5)
├── tests/
├── models/                            # Saved model artifacts (gitignored, regenerable)
├── reports/
│   ├── figures/                       # Exported charts — tracked (small, stated deliverable)
│   └── data_enrichment_log.md         # Source, quote, confidence for every added/corrected record
└── requirements.txt
```

- `data/raw/ethiopia_fi_unified_data.csv` is the only file under `data/` tracked in git,
  since it's the record being actively enriched — its commit history is itself part of the
  Task 1 deliverable. `reference_codes.csv` and the enrichment guide are kept locally,
  gitignored.

## Environment Setup (Python 3.11)

```bash
# 1. Clone
git clone https://github.com/meronsisay/ethiopia-fi-forecast.git
cd ethiopia-fi-forecast

# 2. Create & activate a virtual environment (python3.11 required)
python3.11 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

**Run the notebooks**: `data/raw/ethiopia_fi_unified_data.csv` is already the enriched
(75-record) version — nothing needs to run before any notebook to reproduce it. Run them
in order (01 → 04) only if you want to verify or extend the enrichment/modeling yourself; all
are idempotent, so re-running is always safe.

**Run the dashboard**:
```bash
streamlit run dashboard/app.py
```
Run this from the project root (not from inside `dashboard/`) so `.streamlit/config.toml` is
picked up correctly. Then open the local URL Streamlit prints (usually http://localhost:8501).
