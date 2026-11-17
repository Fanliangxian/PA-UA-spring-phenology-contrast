# UA–PA spring-onset contrasts

Author: **Liangxianfan Fan**. Local package: `v01` (16 November 2026).

Companion to *Spring-onset contrasts vary widely among matched pairs from urban and protected-area sampling domains despite a small overall mean*.

## Start here

This repository contains the figure data, eight plotting scripts and selected key processing methods for the fixed 18,862-pair study. Phenology is MCD12Q2 Collection 6.1 Greenup, 2003–2024, 23.44°N ≤ latitude <66.56°N. Contrasts are UA minus PA in days. The primary table and figure results are unchanged from the prior archive; this version reorganizes supporting material.

| Location | Purpose |
|---|---|
| DATA_SOURCES.md | Product versions, access links and study roles; WDPA source year 2026 |
| data/ | Matched pairs, sufficient statistics, support records, figure inputs and spatial returns |
| data/paper_tables/ | Machine-readable current main and supplementary table exports |
| code/figures/ | Figure 1–4 and S1–S4 plotting sources |
| code/review_descriptives.py, check_tables.py | Descriptive summaries and reference checks |
| code/summarize_overlap.py, export_current_tables.py | Existing coverage sensitivity and current-table exports |
| code/upstream/ | Selected matching, early-cycle selection and cell-overlap source methods |
| docs/ | Data dictionary, reproduction guide and paper-to-data map |
| figures/reference/Figure1.png | Static study-domain reference image |

## Reuse and citation

Author-written code: [MIT](LICENSE). Author-generated derived data: [CC BY 4.0](DATA_LICENSE.md). Mixed-source columns and third-party map material retain the terms in THIRD_PARTY_NOTICES.md. Source polygons/domain-display rasters are external inputs. See CITATION.cff for the software author and version. Repository: https://github.com/Fanliangxian/ua-pa-spring-phenology. Archive content version: slim-v03. A tagged release has not yet been created.
