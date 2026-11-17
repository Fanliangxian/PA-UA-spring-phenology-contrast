# Third-party notices

Source terms were checked on 13 November 2026. This notice preserves upstream rights alongside the confirmed MIT license for author-written code and CC BY 4.0 license for author-generated derived data. Their scopes are recorded in [DATA_LICENSE.md](DATA_LICENSE.md).

A table can contain author-generated outputs and source-derived covariates. The author license grants preserve the exceptions below.

## Source terms

| Source | Terms and treatment |
|---|---|
| MODIS MCD12Q2.061, MCD12Q1.061 and MOD44B.061 | The official catalog states that LP DAAC MODIS products have no restrictions on subsequent use, sale or redistribution. Preserve product identifiers and data citations. [MCD12Q2](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q2), [MCD12Q1](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD12Q1), [MOD44B](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD44B). |
| MERIT DEM v1.0.3 | Dual licensing: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) or [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). The producer distinguishes derived data from produced artwork; the ODbL route has conditions for derived databases. Do not replace these terms with a blanket author-data license. No original full DEM is distributed. [Official catalog terms](https://developers.google.com/earth-engine/datasets/catalog/MERIT_DEM_v1_0_3). |
| WorldClim V1 BIO and MONTHLY | The official catalogs identify [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Retain attribution and applicable share-alike terms for extracted/adapted climate data. [BIO](https://developers.google.com/earth-engine/datasets/catalog/WORLDCLIM_V1_BIO), [MONTHLY](https://developers.google.com/earth-engine/datasets/catalog/WORLDCLIM_V1_MONTHLY). |
| RESOLVE Ecoregions 2017 | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), as identified by the [official catalog](https://developers.google.com/earth-engine/datasets/catalog/RESOLVE_ECOREGIONS_2017). Preserve attribution for ecoregion, biome and realm attributes and their recoding. |
| Natural Earth | [Public domain](https://www.naturalearthdata.com/about/terms-of-use/). The supplied contextual basemap may be used and redistributed. Source identification and file hashes are retained for reproducibility. |
| WDPA / Protected Planet | Original vectors, source-attribute datasets and downloadable PA-domain rasters/arrays are not included. [Protected Planet terms](https://www.protectedplanet.net/en/legal) restrict redistribution and sublicensing of source data, including source material within derivative works; they separately permit publication subject to attribution and no downloadable underlying data. |
| GUB2000 and archived UA domain | Original vectors and downloadable domain rasters are not included. Cite [Li et al. (2020)](https://doi.org/10.1088/1748-9326/ab9be3). Historical input-license metadata is pending; no license is inferred from the article's open-access status or a newer dataset record. |

## Column-level source exceptions

This mapping applies wherever these fields occur, including paired-site tables. Standardized differences retain the provenance of the quantities from which they were computed.

| Fields or field families | Source and applicable notice |
|---|---|
| `ua_elevation_m`, `pa_elevation_m`, `ua_slope_deg`, `pa_slope_deg`; terrain standardized differences | MERIT DEM. Retain the dual-license notice; these columns are not relabeled as unrestricted author-only CC BY data. |
| `ua_mat_c`, `pa_mat_c`, `ua_map_mm`, `pa_map_mm`, `ua_log_map_mm`, `pa_log_map_mm`; climate standardized differences | WorldClim V1 BIO. Retain the CC BY-SA notice, including for the logarithmic precipitation transformation. |
| `ua_climate_zone`, `pa_climate_zone` and corresponding grouped climate fields | Author classification derived from WorldClim V1 monthly normals and BIO annual temperature; retain WorldClim provenance and applicable terms. |
| `ecoregion_id`, `biome_id`, `ua_continental_region`, `pa_continental_region` and realm labels | RESOLVE Ecoregions 2017, including author recoding; CC BY 4.0 attribution applies to source material. |
| Tree-cover fractions, their pairwise differences, and vegetation-tier fields | MOD44B.061 and MCD12Q1.061, with author aggregation/classification; preserve MODIS source citations. |
| Phenology sums, means, counts, quantiles, support indicators and sensitivity summaries | Author analysis of MCD12Q2.061; distinguish these outputs from extracted terrain/climate attributes. The original author-generated derived data are licensed under CC BY 4.0 as specified in DATA_LICENSE.md. |
| Sampling coordinates, grid identifiers and author pair identifiers | Author-generated sampling records. They are not distributed as substitutes for original UA/PA polygon datasets. |
| Landscape identifiers such as `city_id` and `pa_id`, if retained | Record identifiers used to link study objects; their source and attribution remain separate from author-created pair IDs. Their presence does not grant rights to the upstream boundary databases. |

The notices do not declare every result that used a source covariate to be the source dataset itself. They also do not remove applicable upstream terms from copied or directly transformed source fields.

## Figure 1 and map attribution

Only a composed static Figure 1 reference image is supplied, with its plotting code. The archive does not supply the UA/PA display GeoTIFF, classification arrays, downloadable boundary layers or a geographic data service. The map is excluded from any blanket license for original code.

Protected-area attribution: **UNEP-WCMC and IUCN, Protected Planet, World Database on Protected Areas; 2026.** Source: [Protected Planet](https://www.protectedplanet.net/). The source year is supplied by the author; “before 2001” is the establishment-date filter.

Urban-boundary attribution: **Li et al. (2020), GUB2000**, [publication DOI](https://doi.org/10.1088/1748-9326/ab9be3). Contextual basemap: **Natural Earth**, public domain.

## Software and fonts

Python dependencies retain their own licenses. No Arial font file is distributed. Font fallback can affect appearance without changing plotted values. See the environment and reproduction documentation for the dependencies used.

