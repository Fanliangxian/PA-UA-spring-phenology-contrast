# Data dictionary

This guide accompanies `DATA_DICTIONARY.csv`, which describes each field in the retained scientific CSV files, including the current publication-table exports. A `*` in `dataset_pattern` covers a family of identically structured files: the overlap-query blocks share one schema, and the validated overlap files may appear among reference inputs or reproduced outputs. File-specific definitions take precedence over similar field names in other tables. The historical summary tables retain their original schema and are distinguished from the current manuscript tables below.

### Reading paths in the unified archive and Supplementary Data 1

Paths normally start at the unified archive root. Entries beginning `supplementary_data_1/` identify the delivered data supplement within that tree; when this dictionary accompanies the standalone Supplementary Data 1 ZIP, **remove that prefix**. Thus `data/paper_tables/Table2_current.csv` becomes `tables/Table2_current.csv`. Shared `data/...` entries apply to the same files under the supplement's `data/` directory when present. The supplement intentionally contains a subset of the companion archive, so not every dictionary entry denotes a file in the data-only ZIP.

Overlap-reference files have an explicit location alias: unified `data/overlap/reference/<name>.csv` corresponds to supplement `data/overlap/<name>.csv` for `overlap_distributions`, `sensitivity_by_threshold` and `validated_pixel_overlap`. Both layouts are covered by the CSV dictionary. Current-table definitions also apply to the identical schema generated under the chosen output directory's `tables/`. A `reproduced/tables/...` source in the supplement index denotes that generated output location, not an additional required copy inside the delivered supplement. `FILE_INDEX.csv` identifies the actual delivered data files.

## Core conventions

- **Unit of observation:** one fixed matched UA–PA pair, identified by `pair_id`. The roster has 18,862 pairs. There are 14,180 complete-record pairs and 4,682 incomplete-record pairs under the main filter.
- **Contrast direction:** satellite spring onset at the UA endpoint minus onset at the PA endpoint, in days. Negative means earlier onset at UA. Coordinates locate frozen representative sampling points; they are not polygon centroids.
- **Time windows:** full = 2003–2024 (22 product years); recent = 2013–2024 (12 years); early = 2003–2012 (10 years). Recent is nested in full; early and recent are non-overlapping product-year windows.
- **Common support:** a year contributes to a pair only when both endpoints have usable dates under the specified filter. Main requires both overall and Greenup-specific QA codes 0 or 1; strict requires both codes 0. Both filters use the same selected cycle and event date. The five strict-zero-support pairs have undefined strict means and remain in the main analysis and support-count distributions.
- **Weights and percentiles:** each supported pair contributes equally to a pairwise summary. `q05`, `q25`, `median`, `q75` and `q95` are empirical 5th, 25th, 50th, 75th and 95th percentiles, using linear/type-7 quantiles. These describe a distribution, not uncertainty intervals for a population mean.
- **Fractions versus percentages:** `fraction_of_cohort`, `cumulative_fraction` and `f_ua` use a 0–1 scale. Fields ending `_pct`, and `percent`, use 0–100. Coverage-distribution `p5`, `p25`, etc. contain fractions, not percentages.
- **Missingness and zero:** a blank cell can mean unavailable/not applicable, or an undefined statistic. It is not a zero. The numeric code `-1` marks an unclassified context or a missing raster owner in the relevant fields. Exactly zero date-contrast sums, zero support and zero geometric area are three different quantities.
- **File format:** CSV files have header rows and UTF-8 encoding; some include a UTF-8 byte-order mark. Preserve identifier strings, scientific notation, negative signs and original precision when importing. Decimal coordinates or derived values can appear with more digits than displayed in the paper.

## Files and joins

| File or family | Row meaning and principal use |
| --- | --- |
| `data/frozen_pairs.csv` | One fixed pair; endpoint identifiers, coordinates, matching covariates and provenance. Join by `pair_id`. |
| `data/pair_window_summaries.csv` | One pair; full/recent main-filter support counts, integer contrast sums, means and nested-window changes. |
| `data/complete_pair_periods.csv` | One of 14,180 complete pairs; early/recent sums and means and recent-minus-early change. |
| `data/Table_S4_direction_and_tolerances.csv` | One direction or inclusive tolerance category; denominator 18,862. Tolerance categories overlap. |
| `data/Table_S5_sign_transitions.csv` | One of nine early/recent sign combinations; denominator 14,180. |
| `data/Table_S6_groups.csv` | One realm/tier/all-sample descriptive group; `percent` refers to the full 18,862-pair roster. |
| `data/Table_S7_group_balance.csv` | One covariate within one group; covariate balance rather than date-contrast statistics. |
| `data/summary/Table1_descriptive_support.csv` | One analysis roster/filter/window, with both design count and supported-mean count. |
| `data/summary/Table2_sensitivity_contrasts.csv` | One archived sensitivity contrast; separates native-roster differences, within-pair changes and composition. |
| `data/summary/annual_observed_summary.csv` | One product year; archived annual distributions and valid-pair counts. |
| `data/summary/support_calendar_by_cohort.csv` | One year × completeness cohort; annual supported-pair counts. |
| `data/summary/support_year_distribution.csv` | One exact support-year count; number of pairs in each filter/window. |
| `data/summary/context_composition_and_descriptions.csv` | One recorded category × completeness cohort; composition and descriptive contrasts. |
| `data/summary/FigS3_support_source_v01.csv` and `FigS3_zero_strict_support_v01.csv` | One pair; full-window main/strict support counts and coordinates. The latter contains the five strict-zero-support pairs. |
| `data/figure_inputs/` CSV files | The observations or summaries drawn by each named figure. Some intentionally duplicate an analysis input with a figure-specific schema. |
| `data/spatial/completed_18862_spatial_rows.csv` | One UA endpoint; original regional point/raster-query results. |
| `data/spatial/full_18862_spatial_evidence_annotated_v14.csv` | The same regional records with separately labelled targeted evidence for five cases. |
| `data/spatial/targeted_five_return_v13.csv` | One of the five targeted spatial-query records, including local/shard/expected-feature and 3×3-neighborhood diagnostics. |
| `data/spatial/batch_five_discrepancies_v12.csv` and `five_case_comparison_and_disposition.csv` | The five regional discrepancies and their comparison with targeted returns; original discordant results remain recorded. |
| `data/overlap/incoming/E1_UA_pixel_overlap_v01_B00.csv` through `B07.csv` | Disjoint blocks covering the fixed 18,862 UA sampling cells; archived GEE geometry returns. |
| `data/overlap/incoming/E1_UA_pixel_overlap_v01_PILOT.csv` | Eight pilot records duplicated in the complete return; exclude from concatenation of the full eight blocks. |
| `data/overlap/reference/overlap_distributions.csv` | Coverage-fraction distribution for all, point-inside and point-outside groups. |
| `data/overlap/reference/sensitivity_by_threshold.csv` | Full, ≥25% and ≥50% coverage subsets; date contrasts, support, period correspondence and composition. |
| `validated_pixel_overlap.csv` | Per-pair returned geometry and validated coverage fraction, retaining raw fractions and roundoff flags. |
| `zero_area_rows_for_review.csv` | Same schema as the validated file; the archived file has no data rows because no returned cell had exactly zero area. |

## Current manuscript and supplementary-table exports

The following files are under `tables/` in standalone Supplementary Data 1, or `data/paper_tables/` in the unified tree. They serialize existing results in the current manuscript's arrangement. `code/export_current_tables.py` describes the current main-table and S10 exports; the other exports draw on existing support records or period summaries.

| File | Rows and schema |
| --- | --- |
| `Table1_current.csv` | Seven analysis settings; `group`, `analysis_setting`, `pairs`, `pair_years`, full-precision distribution statistics and `reproduction_level`. |
| `Table2_current.csv` | Four within-pair comparisons; `contrast`, `comparison`, `shared_pairs`, full-precision change-distribution statistics and `reproduction_level`. Includes `recent_vs_early_complete22`. |
| `Table_S10_current.csv` | Three coverage subsets; the same numeric fields as `data/overlap/sensitivity_by_threshold.csv`, plus `reproduction_level`. |
| `Table_S5_period_distributions.csv` | Three rows: `early_complete`, `recent_complete` and `recent_minus_early`. Each has `n=14,180`; the last row summarizes within-pair changes. |
| `Table_S2_support_counts_recomputed.csv` | 23 support-count bins (0–22); schema matches `data/summary/support_year_distribution.csv`. |
| `Table_S3_zero_strict_support_recomputed.csv` | Five pairs; schema matches `data/summary/FigS3_zero_strict_support_v01.csv`. Map labels may serialize as `1.0`–`5.0`. |
| `Table_S8_point_categories_recomputed.csv` | Three regional point-membership categories; `pairs` and `percent` use the full 18,862-pair denominator. |

Current Table 2's `mean` is the **mean of within-pair changes** on `shared_pairs`, including the strict-minus-main row. It is not `native_mean_change_B_minus_A` from the historical summary table. The fourth row uses recent (2013–2024) minus early (2003–2012) on the complete cohort; the two recent-minus-full rows use nested windows.

`reproduction_level` has three meanings: `derived_from_pair_statistics` identifies statistics reconstructed from pair-level sufficient statistics; `aggregate_only` identifies the archived strict-filter distributions supplied as aggregates; `derived_from_pair_statistics_and_archived_GEE_overlap` identifies coverage-subset statistics reconstructed from fixed pair summaries and existing spatial-query returns. These labels describe the source of the delivered values, not an additional scientific conclusion or a new upstream remote-sensing extraction.

Files ending `_formatted.csv` are **presentation strings**, not full-precision numerical inputs. Counts include thousands separators, negative numbers use a Unicode minus sign, and intervals join two endpoints with ` to `. Date statistics and percentages have two decimal places; Spearman correlation has three. Numeric reuse should use the corresponding file without `_formatted`. In `Table1_current_formatted.csv` and `Table2_current_formatted.csv`, range columns contain empirical percentile endpoints in days. In `Table_S10_current_formatted.csv`, columns are cohorts and rows are metrics; the dictionary below resolves each displayed row to its numeric source field.

| S10 display `Metric` | Numeric field | Unit and denominator |
| --- | --- | --- |
| Matched pairs | `pairs` | Pairs in the coverage subset. |
| Supported pair-years | `pair_years` | Sum of main-filter support years in that subset. |
| Complete-record pairs | `complete_pairs` | Complete 22-year pairs in that subset. |
| Original roster retained (%) | `retained_pct` | Percent of 18,862. |
| Mean UA minus PA (days) | `mean_days` | Days; equally weighted retained pairs. |
| Interquartile range (days) | `q25_days`, `q75_days` | Days; pairwise mean distribution. |
| UA earlier (%) | `earlier_pct` | Percent of `pairs`. |
| UA later (%) | `later_pct` | Percent of `pairs`. |
| Exact zero (%) | `zero_pct` | Percent of `pairs`. |
| Cross-period Spearman ρ | `spearman_rho` | Correlation within `complete_pairs`. |
| Same nonzero direction (%) | `same_nonzero_pct` | Percent of `complete_pairs`, including zero-sign cases in the denominator. |
| Opposite nonzero directions (%) | `opposite_nonzero_pct` | Percent of `complete_pairs`. |
| Nearctic (%) | `nearctic_pct` | Percent of `pairs`. |
| Palearctic (%) | `palearctic_pct` | Percent of `pairs`. |
| Unclassified realm (%) | `unclassified_realm_pct` | Percent of `pairs`. |
| Tier 1 (%) | `tier1_pct` | Percent of `pairs`. |
| Tier 2 (%) | `tier2_pct` | Percent of `pairs`. |

The S8 category `inside_original` means containment in the supplied unbuffered comparison collection; `buffer_only` means containment in the archived buffered domain but not the supplied comparison collection; `outside_frozen_buffered_domain` means the representative point lies outside the archived buffered domain. These are recorded point-query categories, not a verified urban-interior/buffer ecological stratification. Sampling-cell coverage is recorded separately.

For Figs. 1–2 and S3–S4, paired endpoint coordinate columns are in degrees east/north. `Figure4_window_changes_source_v01.csv` belongs to **Fig. S4** in the current article and describes recent minus full; `complete_pair_periods.csv` supports current **Fig. 4**, recent minus early.

## Pair-level statistics and denominators

For each pair, `sum_full_days` and `sum_recent_days` are integer sums of supported annual contrasts; `mean_full_days = sum_full_days / n_full` and `mean_recent_days = sum_recent_days / n_recent`. Their signs and inclusive tolerance membership are evaluated from the integer sums. For a tolerance δ, a pair is counted when `abs(sum_full_days) <= δ * n_full`.

In the complete-record file, `sum_early_days = sum_full_days - sum_recent_days`, `mean_early_days = sum_early_days / 10`, and `mean_recent_days = sum_recent_days / 12`. `recent_minus_early_days` is calculated within each pair before summarizing. It differs from `recent_minus_full_days`, which uses nested windows.

The same names `n_main` and `n_strict` have different units by file: in pair-level support/figure-source files they are **years per pair**; in annual tables they are **pairs per year**. `pair_years` is the sum of support years across pairs. Neither unique source-domain IDs nor repeated pair-years define an independent-replicate count.

For S5, `early_sign` and `recent_sign` are −1, 0 and +1 for negative, exact-zero and positive sums. The reported same-nonzero-sign percentage divides by **all 14,180 complete pairs**, including pairs with a zero sign in the denominator. Coverage-restricted cross-period percentages instead divide by that row's `complete_pairs`. Its realm/tier composition and earlier/later percentages divide by that row's `pairs`; `retained_pct` always divides by 18,862.

## Group and context codes

Summary Table 1 groups:

| Code | Definition |
| --- | --- |
| `main_all` | All fixed pairs under the full-window main filter. |
| `main_complete22` | The complete-record subset, with original full-window main means. |
| `main_incomplete` | The remaining incomplete-record subset. |
| `strict_native` | Strict-filter means for pairs with at least one strict-supported year; design roster still contains all fixed pairs. |
| `main_on_strict_roster` | Main-filter means restricted to pairs supported under strict QA. |
| `recent_native` | Recent-window main-filter means. |
| `main_on_recent_roster` | Full-window main means for recent-supported pairs; all pairs have recent support, so this duplicates `main_all`. |
| `recent_complete22` | Recent-window means in the original complete-record subset. |

The Table 2 archive uses `complete22_vs_all` (A=all main pairs; B=complete main pairs), `strict_vs_main` (A=main; B=strict), `recent_vs_full` (A=full; B=recent) and `recent_vs_full_complete22` (same windows on the complete-record cohort). `same_pair_mean_change` averages B−A within shared pairs. `native_mean_change_B_minus_A` subtracts the two native-roster means; its difference from the within-pair component is `composition_component`. `marginal_median_change` subtracts marginal medians and is distinct from `paired_change_median`. The current publication Table 2 also reports recent-minus-early; its sufficient statistics are in `complete_pair_periods.csv`, and the current-table exporter supplies that row.

`pft_tier` distinguishes Tier 1 (MCD12Q1 LC_Type1=4) from additional Tier 2 candidates (LC_Type5=4), subject to the persistence, QA and tree-cover requirements in Methods. `vegetation_fraction` is a tree-cover fraction, despite the broader historical field name.

Recorded realm codes originate from the RESOLVE extraction: 0=N/A; 1=Afrotropic; 2=Antarctic/Antarctica; 3=Australasia; 4=Indomalayan; 5=Nearctic; 6=Neotropic; 7=Oceania; 8=Palearctic. Missing/unclassified extraction is −1. The retained sample uses 5, 8 and −1. Approximate climate-group codes are 1=tropical, 2=dry, 3=temperate, 4=continental and 5=polar, with −1 for unclassified extraction; they were derived by the study's WorldClim rule and are not presented as an independently supplied Köppen classification.

In the cohort-composition table, negative/missing context codes are represented as `UNKNOWN`. Equal endpoint codes appear as one code; unequal endpoint codes are retained as `UA=<code>;PA=<code>`. `climate_match_status` is `MATCH` when the normalized two codes agree, including the case that both are `UNKNOWN`; it does not independently establish a classified climate match. Ecoregion/biome numbers retain the source coding; no new geographic interpretation is assigned.

## Matching scales versus balance statistics

In `frozen_pairs.csv`, `std_diff_*` are pair-level covariate differences standardized using the archived robust candidate scale and clipped to [−20,20]. The scale uses 1.4826 × MAD, with IQR/1.349, sample SD and finally 1 as fallbacks. The matching cost is the norm of these standardized differences plus the deterministic tie-breaking term recorded by the matching code.

Table S7 uses a different quantity: `smd = (ua_mean - pa_mean) / matched_pooled_sd`, where `matched_pooled_sd = sqrt((sample_variance_UA + sample_variance_PA)/2)` within that group. Do not equate `std_diff_*` with the reported group-level SMD. Elevation is in metres, slope in degrees, mean annual temperature in °C, precipitation in mm yr⁻¹, and `log_map_mm = ln(max(MAP in mm, 1))`.

## Spatial returns and coverage

`longitude`/`latitude` and frozen-coordinate fields identify the frozen representative UA point. Uploaded or `_remote_geometry_*` fields retain the geometry stored in the endpoint asset; their small differences are not silently replaced. `native_col`/`native_row` identify the MCD12Q1 native sinusoidal sampling cell, approximately 463.31 m per side. Native transform text is preserved as returned; WKT is not a numeric affine-transform list.

Point containment, raster ownership and cell-area coverage are separate outputs. A point outside the UA polygon may belong to a sampling cell that intersects the UA domain. `*_owner` fields contain the minimum intersecting source-feature identifier used in the relevant query (UA `TARGET_FID`, PA `SITE_ID`), or −1 if that query returned none. A suffix such as `_−1_0` in the conceptual offset notation corresponds to the literal ASCII field suffix `_-1_0`: it identifies a cell in the 3×3 native-grid neighborhood. These fields do not measure urbanization intensity.

The five spatial-query disagreements are different pairs from the five strict-zero-support pairs. Regional and targeted results remain separate in the annotated table; flags identify their differing outcomes. The targeted query supports the geometric owner assignment for the frozen cell without resolving the specific cause of the regional discrepancy or rerunning the full historical sampling workflow.

For overlap outputs, `intersection_area_m2` is the **union** area of UA polygon pieces clipped to the native cell. Incoming `f_ua` is that area divided by `cell_area_m2`. Validation preserves it as `f_ua_raw`, records `area_excess_m2 = max(intersection_area_m2 - cell_area_m2, 0)`, and caps `f_ua` at 1 only after checking the excess is at most 0.1 m². `upper_roundoff_clamped` records that handling. The geometry's `tolerance_m = 0.1` is in **metres**, a different quantity from the **0.1 m²** roundoff allowance. Very small positive intersections remain positive returned values, with the interpretation limits described in Supplementary Methods S2.

`center_offset_m` compares the frozen point with the native-cell centre. It is **not** distance to the UA-domain boundary. `point_inside_buffered` is a point test; `f_ua >= 0.25` or `>= 0.50` is an inclusive cell-coverage threshold used to retain whole original pairs.

## Provenance and reproduction level

Hash and source-file fields retain identifiers of their original upstream exports. A historical hash may refer to the unchanged internal source rather than a repackaged public copy; current package manifests identify the latter. Asset IDs describe access routes, not public access grants or supplied immutable vector snapshots.

The pair-level main-filter summaries support deterministic reconstruction of descriptive means, quantiles, signs, operational tolerance counts and cross-period comparisons. Support records support count summaries. Strict-filter difference distributions and annual distributions are supplied as archived aggregates. Spatial-query returns support offline reconciliation and coverage-threshold summaries; the geometry queries themselves require their upstream assets. The README specifies the output-specific procedures. The dictionary does not add raw annual dates, new analyses, or new interpretation to the archived fields.
