"""Gate A-R1 outcome-blind constrained one-to-one matching."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from gate_a.a3_match import (
    COST_COVARIATES,
    EXACT,
    _candidate_edges,
    _min_cost_max_cardinality,
    _read_inputs,
    _robust_parameters,
    _spatial_thin,
)
from gate_a.io import sha256_file


DESIGNS = {"R1-VF05": 0.05, "R1-VF10": 0.10, "R1-VF15": 0.15}


def filter_vf_edges(edges: pd.DataFrame, ua: pd.DataFrame, pa: pd.DataFrame, caliper: float) -> pd.DataFrame:
    """Apply the frozen pairwise hard vegetation-fraction caliper."""

    if edges.empty:
        return edges.assign(delta_vf=pd.Series(dtype=float), abs_delta_vf=pd.Series(dtype=float))
    delta = (
        ua["vegetation_fraction"].to_numpy(float)[edges["urow"].to_numpy(np.int64)]
        - pa["vegetation_fraction"].to_numpy(float)[edges["prow"].to_numpy(np.int64)]
    )
    result = edges.assign(delta_vf=delta, abs_delta_vf=np.abs(delta))
    return result[result["abs_delta_vf"] <= caliper + 1e-12].reset_index(drop=True)


def run_r1_design(
    data: pd.DataFrame,
    spec: dict,
    design: str,
    vf_caliper: float,
    thinning_km: float,
    design_lock_hash: str,
    script_hash: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    thinned = _spatial_thin(data, thinning_km)
    usable = thinned.dropna(subset=EXACT + COST_COVARIATES + ["map_mm"]).copy()
    pair_frames: list[pd.DataFrame] = []
    strata_rows: list[dict[str, object]] = []
    scaling_rows: list[dict[str, object]] = []
    base_calipers = spec["base_calipers"]
    calipers = {
        "distance_km": float(base_calipers["distance_km"]),
        "elevation_m": float(base_calipers["elevation_m"]),
        "mat_c": float(base_calipers["mat_c"]),
        "log_map": float(base_calipers["log_map"]),
    }
    cap = int(spec["candidate_graph"]["pa_neighbors_per_ua"])
    seed = int(spec["candidate_graph"]["tie_break_seed"])
    for key, group in usable.groupby(EXACT, sort=True, dropna=False):
        ua = group[group.landscape.eq("UA")].sort_values("support_unit_id").reset_index(drop=True)
        pa = group[group.landscape.eq("PA")].sort_values("support_unit_id").reset_index(drop=True)
        if ua.empty or pa.empty:
            continue
        medians, scales = _robust_parameters(group)
        for column in COST_COVARIATES:
            scaling_rows.append(
                {"design": design, "ecoregion_id": key[0], "biome_id": key[1], "pft_tier": key[2], "covariate": column, "median": medians[column], "scale": scales[column]}
            )
        base_edges = _candidate_edges(ua, pa, calipers, cap, medians, scales, seed)
        edges = filter_vf_edges(base_edges, ua, pa, vf_caliper)
        if edges.empty:
            strata_rows.append(
                {"design": design, "ecoregion_id": key[0], "biome_id": key[1], "pft_tier": key[2], "ua_units": len(ua), "pa_units": len(pa), "base_edges": len(base_edges), "vf_edges": 0, "matched_pairs": 0}
            )
            continue
        matched_u, matched_p = _min_cost_max_cardinality(
            len(ua), len(pa), edges.urow.to_numpy(np.int64), edges.prow.to_numpy(np.int64), edges.cost.to_numpy(float)
        )
        chosen = edges.set_index(["urow", "prow"]).loc[list(zip(matched_u, matched_p))].reset_index()
        u = ua.iloc[matched_u].reset_index(drop=True)
        p = pa.iloc[matched_p].reset_index(drop=True)
        out = pd.DataFrame(
            {
                "design": design,
                "thinning_km": thinning_km,
                "vf_caliper": vf_caliper,
                "ua_support_unit_id": u.support_unit_id.astype(str),
                "pa_support_unit_id": p.support_unit_id.astype(str),
                "city_id": u.city_id.to_numpy(),
                "pa_id": p.pa_id.to_numpy(),
                "ecoregion_id": key[0],
                "biome_id": key[1],
                "pft_tier": key[2],
                "ua_continental_region": u.continental_region.to_numpy(),
                "pa_continental_region": p.continental_region.to_numpy(),
                "ua_climate_zone": u.climate_zone.to_numpy(),
                "pa_climate_zone": p.climate_zone.to_numpy(),
                "geographic_distance_km": chosen.geographic_distance_km.to_numpy(),
                "matching_cost": chosen.cost.to_numpy(),
                "delta_vf": chosen.delta_vf.to_numpy(),
                "abs_delta_vf": chosen.abs_delta_vf.to_numpy(),
                "pair_weight": 1.0,
                "ua_source_file": u.source_file.to_numpy(),
                "pa_source_file": p.source_file.to_numpy(),
                "ua_source_file_hash": u.source_file_hash.to_numpy(),
                "pa_source_file_hash": p.source_file_hash.to_numpy(),
                "r1_design_lock_hash": design_lock_hash,
                "r1_matching_script_hash": script_hash,
            }
        )
        for column in COST_COVARIATES + ["map_mm"]:
            out[f"ua_{column}"] = u[column].to_numpy()
            out[f"pa_{column}"] = p[column].to_numpy()
        for column in COST_COVARIATES:
            out[f"std_diff_{column}"] = chosen[f"std_diff_{column}"].to_numpy()
        pair_frames.append(out)
        strata_rows.append(
            {"design": design, "ecoregion_id": key[0], "biome_id": key[1], "pft_tier": key[2], "ua_units": len(ua), "pa_units": len(pa), "base_edges": len(base_edges), "vf_edges": len(edges), "matched_pairs": len(out)}
        )
    pairs = pd.concat(pair_frames, ignore_index=True) if pair_frames else pd.DataFrame()
    if not pairs.empty:
        pairs = pairs.sort_values(EXACT + ["ua_support_unit_id", "pa_support_unit_id"]).reset_index(drop=True)
        pairs.insert(1, "pair_id", [f"{design}_pair_{i:08d}" for i in range(1, len(pairs) + 1)])
    return pairs, pd.DataFrame(strata_rows), pd.DataFrame(scaling_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--a2-metadata", type=Path, required=True)
    parser.add_argument("--design-lock", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--design", action="append", choices=sorted(DESIGNS))
    parser.add_argument("--thinning-km", type=float, default=5.0)
    args = parser.parse_args()
    spec = json.loads(args.design_lock.read_text(encoding="utf-8"))
    if spec["protocol_status"] != "PREANALYSIS_LOCKED_BEFORE_R1_MATCHING":
        raise ValueError("R1 design lock is not frozen")
    data, _ = _read_inputs(args.input_dir, args.a2_metadata)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selected = args.design or list(DESIGNS)
    design_lock_hash = sha256_file(args.design_lock)
    script_hash = sha256_file(Path(__file__))
    summary = []
    suffix = f"{int(args.thinning_km)}km"
    for design in selected:
        vf_caliper = DESIGNS[design]
        pairs, strata, scaling = run_r1_design(data, spec, design, vf_caliper, args.thinning_km, design_lock_hash, script_hash)
        pair_name = f"GateA_R1_match_{suffix}_{design.removeprefix('R1-')}.csv"
        pairs.to_csv(args.output_dir / pair_name, index=False)
        strata.to_csv(args.output_dir / f"GateA_R1_strata_{suffix}_{design.removeprefix('R1-')}.csv", index=False)
        scaling.to_csv(args.output_dir / f"GateA_R1_scaling_{suffix}_{design.removeprefix('R1-')}.csv", index=False)
        summary.append(
            {
                "design": design,
                "thinning_km": args.thinning_km,
                "vf_caliper": vf_caliper,
                "pairs": len(pairs),
                "cities": int(pairs.city_id.nunique()) if len(pairs) else 0,
                "PAs": int(pairs.pa_id.nunique()) if len(pairs) else 0,
                "ecoregions": int(pairs.ecoregion_id.nunique()) if len(pairs) else 0,
                "regions": int(pairs.ua_continental_region.nunique()) if len(pairs) else 0,
                "climate_zones": int(pairs.ua_climate_zone.nunique()) if len(pairs) else 0,
            }
        )
    metadata = {
        "schema_version": "gate-a-r1-match-1.0",
        "design_lock_hash": design_lock_hash,
        "matching_script_hash": script_hash,
        "a2_metadata_hash": sha256_file(args.a2_metadata),
        "runs": summary,
        "outcome_blind": True,
    }
    (args.output_dir / f"GateA_R1_matching_metadata_{suffix}.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
