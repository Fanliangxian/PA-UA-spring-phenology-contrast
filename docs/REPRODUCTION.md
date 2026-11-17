# Reproduction guide

## Inputs and statistical conventions

The frozen roster has 18,862 unique pairs. Each pair contributes equally to the distribution of its mean UA-minus-PA spring-onset contrast. Means within a pair use years jointly supported by its two endpoints. Quantiles use linear interpolation (Hyndman–Fan type 7). A zero count of supported years is distinct from a zero phenological difference.

`sum_full_days / n_full` and `sum_recent_days / n_recent` provide the full-window and recent means. For the complete-record cohort, the early sum is `sum_full_days - sum_recent_days` and its denominator is 10 years. Recent-minus-early changes use 12 recent years and 10 early years. Recent-minus-full is a separate, nested-window contrast.

Main-filter support totals 403,981 pair-years. Strict-filter support totals 382,773 pair-years, with five pairs having zero strict support. Those five pairs are different from the five regional/targeted spatial-query discrepancies retained in Table S9.

## Entry point

`reproduce.py` uses only local packaged inputs. `--output` must name a new or empty directory separate from input/reference folders. Each subprocess has a stdout/stderr log. The final JSON records success or failure, source hashes before and after, output hashes, and figure-generation status. A failure is not converted to a successful partial run.

| Mode | Work performed |
|---|---|
| `summaries` | Recalculate main pair summaries, S4–S7 and support counts; check archived distributions; export current Tables 1 and 2 |
| `overlap` | Validate the eight existing overlap blocks; recompute threshold summaries and distributions; compare archived full-precision references; export S10 |
| `figures` | Regenerate Figs 2–4 and S1–S4; copy the Fig. 1 reference PNG unless authorized display inputs are explicitly supplied |
| `all` | Perform all of the above in one output directory |

`code/review_descriptives.py` produces S4–S7 and complete-record period results. `code/check_tables.py` checks primary tables, support and spatial counts. `code/summarize_overlap.py` combines native-cell coverage returns with the fixed pair statistics. `code/export_current_tables.py` adds the current Table 2 recent-minus-early row and integrates S10 without changing the estimands or cohorts.

## What is recomputed

| Result | Level |
|---|---|
| Main-filter distributions and full/recent paired changes | Recomputed from pair-level sums/counts and checked against archived results |
| Early/recent non-overlapping comparisons; rank correlation; sign transitions | Recomputed for the 14,180 complete-record pairs |
| Direction and ±3/5/7-day proportions; tier/realm summaries; matched balance | Recomputed from supplied pair statistics and covariates |
| Common-support counts and strict-zero identities | Recomputed from supplied pair support records |
| Strict-filter distributions and strict-minus-main change distribution | Archived aggregate agreement checks |
| Annual distributions and published ECDF/histogram summaries | Archived summaries/plotting inputs; annual dates are not provided in this package |
| S8/S9 point-containment and regional/targeted results | Reconciled from existing returned records |
| Cell-coverage thresholds and S10 | Recomputed from existing GEE returns and pair summaries; geometry queries themselves are not repeated |
| Figs 2–4, S1–S4 | Redrawn from packaged derived inputs, subject to the statistical levels above |
| Fig. 1 | Archived static reference by default; conditional redraw with exact display inputs |

## Overlap calculations

The nominal 500-m selection grid has approximately 463.31-m cells in its native projection. Coverage fractions use the area of each selection cell intersecting the archived UA domain. The existing script retains the 0.1 m² floating-point tolerance and clips negligible area excess to the cell area. The 25% and 50% filters are sensitivity cohorts; no minimum fraction was imposed on the original sample. Their retained pair counts are 12,468 and 9,990.

All 18,862 selection cells have positive UA-domain overlap. The 8,807 representative points outside the vector domain therefore do not represent zero-overlap cells. Historical `inside_original`/`buffer_only` labels in returned records concern a comparison asset; they are not a validated urban-core/buffer stratification.

## Environment and output rendering

The tested package versions are pinned in `requirements.txt`; the dependency snapshot is recorded in `requirements.txt`. Installing dependencies may require internet access; the reproduction itself is offline. `PROJ_NETWORK=OFF` avoids remote projection downloads. Natural Earth shapefile components are bundled. System fonts may affect appearance; DejaVu Sans is used or available as fallback. Statistical checks do not depend on rendering byte identity across operating systems.

## Upstream scope

The public MODIS products are identified in DATA_SOURCES. Selected matching, cycle-selection and geometry methods are supplied for methodological inspection in `code/upstream`. Re-extraction needs the corresponding candidate/support assets, manifests and access permissions. The offline entry point starts from the fixed paired data; it does not rerun matching, GEE exports, randomized fitting or sampling.
