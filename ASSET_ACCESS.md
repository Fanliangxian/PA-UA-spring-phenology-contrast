# Asset access and reconstruction

The archive separates reproducible analytical inputs from upstream geographic source assets. No private account access is needed for the packaged derived-statistics workflows and seven analytical figures. Original UA/PA polygons and their downloadable display rasters are not distributed.

## Included and external components

| Component | Access in this archive | Reconstruction scope |
|---|---|---|
| Frozen paired-site records, support summaries and phenological sufficient statistics | Packaged analytical tables | Reproduce the supported descriptive summaries using the supplied inputs; see the reproduction documentation for aggregate-only checks. |
| Figures 2–4 and S1–S4 | Code and analytical inputs supplied, with the Natural Earth contextual basemap | Seven figures can be rebuilt offline within the documented input scope. |
| Figure 1 | Static reference image and plotting source | Exact map reconstruction additionally requires the corresponding archived domain display inputs. Those inputs are not packaged. |
| GUB2000 and the study's 1 km buffered UA domain | External source and author-held historical asset | Obtain upstream data from the producer under the applicable terms. Current products need not reproduce the archived domain exactly. |
| WDPA-based PA domain | External source and author-held historical asset | Obtain data from Protected Planet under its terms. Matching the historical database release and study filter is necessary for exact reconstruction. |
| MODIS, MERIT, WorldClim and RESOLVE products | Public upstream services; identifiers in DATA_SOURCES.md | Independent upstream extraction requires access to the source products and the specified preprocessing, not just the derived tables. |

See [DATA_SOURCES.md](DATA_SOURCES.md) for product identifiers and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the terms that follow particular columns.

## Figure 1 external inputs

The study-domain display layers are renderings of the archived UA and PA domains. They are not exact vector-boundary replacements. The public package includes neither the GeoTIFF/array inputs nor compressed archives containing those inputs.

The Figure 1 source documents how the reference image is drawn. Users who have lawfully obtained the necessary matching domain inputs can provide them separately. Source access is available through [Protected Planet](https://www.protectedplanet.net/) and the [GUB producer-associated data page](https://www.scl.hku.hk/data). These links do not grant access to an author's private Earth Engine collection.

The author identifies the WDPA source year as 2026; no month is specified. The filter selecting protected areas established before 2001 must not be used as a substitute for that metadata. Source updates are not silently substituted for the frozen study domain.

## Sampling records and spatial results

The source scripts record these author-managed Earth Engine asset identifiers:

| Identifier | Role |
|---|---|
| `projects/ee-liangxianfan0/assets/pheno/UA_2000_north_buf_1000m` | Archived UA sampling domain used by the overlap analysis |
| `projects/ee-liangxianfan0/assets/pheno/PA_pre2001_north` | PA sampling domain |
| `projects/ee-liangxianfan0/assets/pheno/GateB_R1F_primary_endpoints` | Frozen endpoint geometries used for MODIS extraction |
| `projects/ee-liangxianfan0/assets/pheno/E1_boundary_frozen_UA_v04` | Frozen UA coordinate/support-cell table used by the spatial checks |
| `projects/ee-liangxianfan0/assets/UA` | Supplied unbuffered comparison collection |

These identifiers document the inputs; they do not confer public access. Offline reproduction uses the provided analytical tables and returned records and therefore does not require these asset permissions.

For the optional exact Figure 1 redraw, the external directory must contain `E1_study_domain_display_mosaic_v01.tif`, `domain_quicklook_aggregate_v01.npz`, `frozen_design_record.json` and `verification_v01.json`. The code checks the archived pair and mosaic hashes. With authorized matching inputs, run:

```sh
python reproduce.py --mode figures --domain-inputs /path/to/domain_inputs --output reproduced_with_domain
```

The packaged point coordinates are author-selected sampling-grid locations. Pairwise phenology statistics and calculated pixel–domain overlap values are analytical outputs. Their distribution does not distribute the original polygon geometries or grant a new license to the upstream databases. Extracted covariates retain the source-specific treatment listed in THIRD_PARTY_NOTICES.md.

## Reproduction levels

The archive rebuilds supported summaries from packaged paired-site statistics and checks other results against archived aggregate summaries. It does not claim to rebuild every annual date, every strict-filter pairwise sum or the upstream matching and extraction from scratch.

The seven analytical figures inherit those input levels. Figure 1 is the explicit external-input exception: the static reference image can be viewed without the restricted source layers, while exact regeneration requires those layers. Code availability and source-data accessibility are documented separately.

