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

## Run

Use Python 3.12 with the provided dependency snapshot:

```sh
python -m pip install -r requirements.txt
python reproduce.py --mode all --output reproduced
```

Use a new or empty output directory. `--mode figures`, `--mode summaries` and `--mode overlap` can run the respective parts separately. Seven analytical figures are regenerated; Figure 1 is copied as an archived reference by default. Its plotting source supports authorized external domain-display inputs through `--domain-inputs`; see ASSET_ACCESS.md.

Main pair statistics, support counts and overlap-threshold summaries are reproduced from packaged derived inputs. Strict-filter and annual distributions are checked/rendered from archived aggregates. GEE queries and upstream matching are not executed. See docs/REPRODUCTION.md for these distinctions.

## Supporting tables

The manuscript no longer uses the broad label “Supplementary Data 1”. SI Table S11 reports cohort composition; S12 and S13 provide six-decimal versions of main Tables 1 and 2. Full machine precision remains in the CSVs. docs/PAPER_DATA_MAP.md gives each citation and its exact supporting file.

Repeated export scripts, duplicate supplement files, private absolute paths and internal review documents are omitted. Scientific inputs needed by the offline runner remain included. The original full archives remain preserved by the author.

## Reuse and citation

Author-written code: [MIT](LICENSE). Author-generated derived data: [CC BY 4.0](DATA_LICENSE.md). Mixed-source columns and third-party map material retain the terms in THIRD_PARTY_NOTICES.md. Source polygons/domain-display rasters are external inputs. See CITATION.cff for the software author and version. Repository: https://github.com/Fanliangxian/ua-pa-spring-phenology. Archive content version: slim-v03. A tagged release has not yet been created.
