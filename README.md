# Ethiopia Financial Inclusion — Forecasting System

A forecasting system for Ethiopia's digital financial transformation, built for a consortium
of development finance institutions, mobile money operators, and the National Bank of Ethiopia.
Forecasts the two core Global Findex dimensions of financial inclusion:

- **Access** — Account Ownership Rate
- **Usage** — Digital Payment Adoption Rate

The project uses a unified `observation` / `event` / `impact_link` / `target` schema, so that
policies, product launches, and infrastructure milestones can be modeled as drivers of Access
and Usage rather than just listed alongside them.

## Project Structure

```
ethiopia-fi-forecast/
├── .github/workflows/unittests.yml   # CI: runs pytest on every push/PR
├── data/
│   ├── raw/                          # Only ethiopia_fi_unified_data.csv is tracked (enriched dataset)
│   └── processed/                    # Cleaned, analysis-ready data (gitignored, regenerable)
├── notebooks/
│   ├── 01_data_exploration_enrichment.ipynb   # Task 1
│   └── 02_eda.ipynb                           # Task 2
├── src/
│   ├── data_loader.py                 # Load + explore the unified dataset
│   └── enrichment.py                  # Idempotent add_record() / append_log_entry() helpers
├── dashboard/app.py                   # Streamlit dashboard
├── tests/
├── models/                            # Saved model artifacts (gitignored, regenerable)
├── reports/
│   ├── figures/                       # Exported charts — tracked (small, stated deliverable)
│   └── data_enrichment_log.md         # Source, quote, confidence for every added/corrected record
└── requirements.txt
```

## Data

- `data/raw/ethiopia_fi_unified_data.csv` — unified schema: `observation`, `event`,
  `impact_link`, and `target` records all in one table (see schema table below). The only file
  under `data/` tracked in git, since it's the record being actively enriched — its commit
  history is itself part of the Task 1 deliverable.
- `data/raw/reference_codes.csv`, `Additional_Data_Points_Guide.xlsx` — kept locally, gitignored.

### Schema at a glance

| record_type   | `category` filled? | `pillar` filled? | What it represents |
|---------------|---------------------|-------------------|---------------------|
| `observation` | no                  | yes               | A measured value (survey/operator/infra data) |
| `event`       | yes                 | **no** (never pre-assigned) | A policy/launch/milestone |
| `impact_link` | no                  | yes               | Modeled effect of an event (via `parent_id`) on an indicator |
| `target`      | no                  | yes               | An official policy goal |

Events deliberately never get a pillar pre-assigned — e.g. Telebirr's launch affects both
Access and Usage, so labeling it as one or the other up front would bias the analysis before
it starts. `impact_link` records carry that interpretation instead, joined back to their
parent event via `parent_id`.

## Setup (Python 3.11)

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

## Progress

### Data Exploration and Enrichment 

- Dataset grew **57 → 73 records**: 15 new observations, 1 new event, 3 new impact_links,
  each sourced and logged in `reports/data_enrichment_log.md`.
- Closed the biggest gap: `USG_DIGITAL_PAYMENT` — one of the two indicators this whole project
  forecasts — had **zero** data points before enrichment; now has 2 (2021: ~23%, 2024: 21%).
- 1 dating error corrected (`REC_0004`/`REC_0005` moved from 2021 to 2024) and 1 conflict
  between secondary sources flagged rather than silently resolved (2024 gender gap reported as
  both 56/36 and 57/42).
- `add_record()`/`append_log_entry()` in `src/enrichment.py` are idempotent — the enrichment
  notebook can be re-run top to bottom without ever duplicating a row or log entry.

### Exploratory Data Analysis 

- **21 of 29 indicators** have only 1 observation — no trend possible without further data.
- Account ownership: 22% (2014) → 35% (2017) → 46% (2021) → **49% (2024)** — only **+3pp**
  most recently, despite Telebirr and M-Pesa launching in between.
- Best-supported explanation: **~90M registered mobile money accounts** (≈120 per 100 adults)
  vs. only **9.45%** active Findex-reported use — a large registered-vs-active gap.
- Gender gap: **~20pp** in Access (56% men vs. 36% women, 2024 — flagged as contested), **13pp**
  in Usage (26% men vs. 13% women).
- Agent network grew from 200k → 216k agents (2022–2024) — far slower than account growth,
  a plausible capacity bottleneck.
- Infrastructure "funnel": broad 4G coverage vs. only 41% phone ownership and 16% smartphone
  penetration — the device layer, not the network, looks like the binding constraint.
- Correlation analysis intentionally **skips a full heatmap** — most indicators share only 2
  time points, making Pearson correlation statistically meaningless there — using a
  co-movement table and `impact_link` evidence summary instead.
- 6 key insights and a 5-point ranked data-quality assessment documented in `eda.ipynb`.





