# Selected key upstream methods

`gate_a/` preserves the deterministic matching algorithm (R1-VF05, 5-km thinning). It needs the original candidate inventory and design specification; SciPy and a Parquet engine may be needed for upstream execution. `gee/modis/early_policy_v01.js` is the shared MCD12Q2 early-cycle and quality-filter definition. It is a method function, not a complete export task. `gee/GEE_UA_pixel_overlap_v01.js` documents native-cell overlap extraction from author-managed assets. None is invoked by the offline runner.

Repeated partition exports, historical packaging helpers and debugging scripts are omitted. The complete prior author archive remains preserved locally. Main published summaries and plots use the supplied fixed derived inputs through the root entry point.
