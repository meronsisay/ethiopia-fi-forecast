# Data Enrichment Log

Log every record added or corrected during Task 1. One entry per record (or small batch of
closely related records).

## Template

### `<RECORD_ID>` — `<record_type>` — `<short description>`

- **source_url:**
- **original_text:** (exact quote/figure from the source)
- **confidence:** high / medium / low
- **collected_by:**
- **collection_date:**
- **notes:** (why this is useful for forecasting Access/Usage)

---

<!-- Add entries below this line -->

### `REC_0004, REC_0005` — `observation (correction)` — Corrected observation_date from 2021-12-31 to 2024-11-29

- **source_url:** https://digitalfinance.shega.co/insights/articles/findex-2025-and-ethiopia-s-digital-financial-leap-momentum-without-maturity
- **original_text:** "There was also a marked gender gap, with 56% of men owning accounts compared to only 36% of women."
- **confidence:** medium
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** The 56%/36% gender split matches the 2024 Findex round (survey window 2024-10-15 to 2024-11-29), not the 2021 round these rows were originally dated to. NOTE: a conflicting 57%/42% figure for the same 2024 round was found later (see section 3) -- flagged for verification, not resolved here.

### `REC_0004, REC_0005 (flag)` — `data_quality_flag` — Conflicting secondary sources for 2024 gender gap: 56/36 vs 57/42

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "While 57 percent of men in Ethiopia report having an account, only 42 percent of women do."
- **confidence:** low
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Birr Metrics (citing the World Bank Findex 2025 release directly) reports 57%/42%, not 56%/36% as reported by Shega/DFS Ethiopia Hub. Both cite the same underlying survey. Not resolved in this dataset -- flagging for verification against primary Findex microdata before relying on either number in forecasting.

### `REC_0034` — `observation` — Registered Mobile Money Accounts (cumulative) (2024-10-24)

- **source_url:** https://www.gsma.com/newsroom/press-release/ethiopias-digital-economy-to-contribute-etb-1-3-trillion-to-gdp-by-2028-unlocking-jobs-and-growth-through-telecom-and-policy-reforms/
- **original_text:** "Ethiopia has already made significant strides, with over 90 million registered mobile accounts by 2024."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Registered accounts vastly exceed Findex's active-use ACC_MM_ACCOUNT (9.45%). Central to explaining why account ownership stagnated despite mass account opening.

### `REC_0035` — `observation` — Mobile Money Agent Count (2022-09-30)

- **source_url:** https://www.gsma.com/mobilefordevelopment/blog/mobile-money-in-ethiopia-what-we-learnt-from-our-expert-roundtable/
- **original_text:** "mobile money agents grew by 200% in the year to September 2022 to over 200,000."
- **confidence:** medium
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Early agent-network growth point, ~16 months after Telebirr's launch.

### `REC_0036` — `observation` — Mobile Money Agent Count (2024-06-30)

- **source_url:** https://shega.co/news/the-rise-of-mobile-money-in-ethiopia-without-the-agents
- **original_text:** "...had around 216,000 agents as of June 2024."
- **confidence:** medium
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Growth from 200k (2022) to 216k (2024) is much slower than account growth -- candidate explanation for the Access slowdown.

### `IMP_0015` — `impact_link` — Telebirr launch -> ACC_AGENT_COUNT

- **source_url:** https://www.gsma.com/mobilefordevelopment/blog/mobile-money-in-ethiopia-what-we-learnt-from-our-expert-roundtable/
- **original_text:** "mobile money agents grew by 200% in the year to September 2022 to over 200,000."
- **confidence:** medium
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Connects the Telebirr launch event to observed agent-network growth ~16 months later.

### `REC_0037` — `observation` — Digital Payment Adoption Rate (2021-12-31)

- **source_url:** https://shega.co/news/findex-2025-and-ethiopias-digital-financial-leap-momentum-without-maturity
- **original_text:** "Mobile money accounts were at 4.7% and digital payments were used by fewer than one in four adults."
- **confidence:** medium
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Approximate -- source states '<25%', not an exact figure. Fills a previously empty indicator that is one of the two headline forecast targets.

### `REC_0038` — `observation` — Digital Payment Adoption Rate (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "36 percent saved in account with 21 percent using digital payments."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** CONFLICTS with project brief's ~35% figure -- see caveat above. This figure chosen because it cross-checks against other independently known 2024 figures (49% account ownership, 22%->49% trend) reported correctly in the same article.

### `REC_0039` — `observation` — Smartphone Penetration (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "Smartphone penetration stands at only 16 percent, with most users relying on feature or basic phones."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Enabler/proxy variable (Sheet C of the enrichment guide) -- low smartphone penetration caps digital Usage growth even as Access rises.

### `REC_0040` — `observation` — Mobile Phone Ownership (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "only 41 percent of adults own a mobile phone, with stark gender differences -- 50 percent of men compared to just 33 percent of women."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Basic phone ownership is a prerequisite enabler for both Access (mobile money) and Usage (digital payments).

### `REC_0041` — `observation` — Account Ownership, wealthiest 60% (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "account ownership among the wealthiest 60 percent stands at 53 percent, compared with 43 percent among the poorest 40 percent."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Income disaggregation of Access, not previously captured -- Sheet C enabler/equity dimension.

### `REC_0042` — `observation` — Account Ownership, poorest 40% (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "compared with 43 percent among the poorest 40 percent."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Paired with ACC_OWNERSHIP_TOP60 -- a 10pp income gap in Access.

### `REC_0043` — `observation` — Digital Payment Usage, wealthiest 60% (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "26 percent of the wealthiest 60 percent reported digital transactions, compared to 16 percent of the poorest."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Income disaggregation of Usage -- larger relative gap than Access (10pp income gap in Access vs. 10pp here on a smaller base).

### `REC_0044` — `observation` — Digital Payment Usage, poorest 40% (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "compared to 16 percent of the poorest."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Paired with USG_DIGITAL_PAYMENT_TOP60.

### `REC_0045` — `observation` — Digital Payment Usage Gender Gap (2024-11-29)

- **source_url:** https://birrmetrics.com/49-of-ethiopians-are-banked-as-findex-2025-highlights-the-next-inclusion-challenge/
- **original_text:** "Only 26 percent of men and 13 percent of women used digital payments in the past year."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Gender gap in Usage (13pp) is proportionally much larger than the ~15-20pp gap in Access, given the smaller overall base -- worth testing in Task 2.

### `EVT_0011` — `event` — NBE Revised Payment Instrument Issuer Directive, Oct 2023

- **source_url:** https://www.telecomreviewafrica.com/articles/general-news/3842-nbe-enhances-directive-for-mobile-money-services/
- **original_text:** "the daily e-account balance limit has been increased from 30,000 birr ($539) to 75,000 birr ($1,347), and a new daily global transaction limit of 150,000 birr ($2,695) has been implemented."
- **confidence:** high
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Regulatory event missing from the starter catalog. Category='regulation', pillar deliberately left empty since it plausibly affects both ACCESS (banks can launch mobile money subsidiaries) and USAGE (higher transaction limits enable more/larger digital payments).

### `IMP_0016` — `impact_link` — NBE directive -> USG_P2P_VALUE

- **source_url:** https://www.telecomreviewafrica.com/articles/general-news/3842-nbe-enhances-directive-for-mobile-money-services/
- **original_text:** "the daily e-account balance limit has been increased from 30,000 birr to 75,000 birr..."
- **confidence:** medium
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Higher balance/transaction ceilings directly enable larger-value P2P transfers.

### `IMP_0017` — `impact_link` — NBE directive -> ACC_MM_ACCOUNT

- **source_url:** https://www.telecomreviewafrica.com/articles/general-news/3842-nbe-enhances-directive-for-mobile-money-services/
- **original_text:** "the directive allows banks to establish subsidiaries specializing in the provision of mobile money services."
- **confidence:** low
- **collected_by:** Meron Sisay
- **collection_date:** 2026-07-17
- **notes:** Allowing banks to launch mobile-money subsidiaries is a plausible but indirect, slow-moving driver of account growth -- low confidence, no direct evidence yet.

