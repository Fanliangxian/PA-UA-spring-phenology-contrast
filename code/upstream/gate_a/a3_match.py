"""Deterministic outcome-blind A3 UA-PA matching.

The locked specification is selected before pair production.  Matching is
exact on ecoregion, biome, and PFT tier, respects frozen calipers, and solves
minimum-cost maximum-cardinality assignment on a deterministic capped sparse
candidate graph without replacement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import min_weight_full_bipartite_matching
from scipy.spatial import cKDTree

from gate_a.io import sha256_file


EXACT = ["ecoregion_id", "biome_id", "pft_tier"]
COST_COVARIATES = [
    "latitude", "longitude", "elevation_m", "slope_deg", "mat_c",
    "log_map_mm", "vegetation_fraction",
]
REQUIRED = [
    "support_unit_id", "landscape", "city_id", "pa_id", "longitude",
    "latitude", "pft_tier", "ecoregion_id", "biome_id", "climate_zone",
    "continental_region", "elevation_m", "slope_deg", "mat_c", "map_mm",
    "log_map_mm", "vegetation_fraction", "valid_landcover_years",
    "target_landcover_years",
]
MISSING_SENTINEL = -9999.0
EARTH_RADIUS_KM = 6371.0088


def _stable_jitter(seed: int, ua_id: str, pa_id: str) -> float:
    payload = f"{seed}|{ua_id}|{pa_id}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")
    return (value / 2**64) * 1e-9


def _vectorized_jitter(seed: int, urow: np.ndarray, prow: np.ndarray) -> np.ndarray:
    """Fast deterministic SplitMix64 tie-break jitter for large edge tables."""

    with np.errstate(over="ignore"):
        value = (
            np.asarray(urow, dtype=np.uint64) * np.uint64(0x9E3779B97F4A7C15)
            + np.asarray(prow, dtype=np.uint64) * np.uint64(0xBF58476D1CE4E5B9)
            + np.uint64(seed)
        )
        value = (value ^ (value >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        value = (value ^ (value >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        value = value ^ (value >> np.uint64(31))
    return value.astype(np.float64) / float(2**64) * 1e-9


def match_one_to_one(
    candidates: pd.DataFrame,
    seed: int = 20260819,
) -> pd.DataFrame:
    """Small public deterministic matcher used by analytical tests.

    ``candidates`` must contain ua_id, pa_id, and cost.  The function returns
    a minimum-cost maximum-cardinality matching without UA or PA reuse.
    """

    needed = {"ua_id", "pa_id", "cost"}
    missing = needed.difference(candidates.columns)
    if missing:
        raise ValueError(f"Missing candidate columns: {sorted(missing)}")
    if candidates.empty:
        return pd.DataFrame(columns=["ua_id", "pa_id", "cost"])
    edges = candidates.copy()
    edges["ua_id"] = edges["ua_id"].astype(str)
    edges["pa_id"] = edges["pa_id"].astype(str)
    edges = edges.sort_values(["ua_id", "pa_id", "cost"]).drop_duplicates(["ua_id", "pa_id"])
    ua_ids = sorted(edges["ua_id"].unique())
    pa_ids = sorted(edges["pa_id"].unique())
    ua_pos = {value: i for i, value in enumerate(ua_ids)}
    pa_pos = {value: i for i, value in enumerate(pa_ids)}
    rows = edges["ua_id"].map(ua_pos).to_numpy(np.int64)
    cols = edges["pa_id"].map(pa_pos).to_numpy(np.int64)
    costs = edges["cost"].to_numpy(float)
    costs = np.maximum(costs, 1e-8)
    costs += np.array([_stable_jitter(seed, u, p) for u, p in zip(edges["ua_id"], edges["pa_id"])])
    matched_rows, matched_cols = _min_cost_max_cardinality(len(ua_ids), len(pa_ids), rows, cols, costs)
    lookup = edges.set_index(["ua_id", "pa_id"])["cost"]
    result = pd.DataFrame(
        {
            "ua_id": [ua_ids[i] for i in matched_rows],
            "pa_id": [pa_ids[j] for j in matched_cols],
        }
    )
    result["cost"] = [float(lookup.loc[(u, p)]) for u, p in zip(result["ua_id"], result["pa_id"])]
    return result.sort_values(["ua_id", "pa_id"]).reset_index(drop=True)


def _min_cost_max_cardinality(
    n_ua: int,
    n_pa: int,
    rows: np.ndarray,
    cols: np.ndarray,
    costs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Lexicographically maximize cardinality, then minimize edge cost."""

    if n_ua == 0 or n_pa == 0 or len(rows) == 0:
        return np.array([], dtype=np.int64), np.array([], dtype=np.int64)
    real_cost = np.clip(np.asarray(costs, dtype=float), 1e-8, 1e4)
    dummy_rows = np.arange(n_ua, dtype=np.int64)
    dummy_cols = n_pa + dummy_rows
    dummy_cost = np.full(n_ua, 1e6, dtype=float)
    graph = csr_matrix(
        (
            np.concatenate([real_cost, dummy_cost]),
            (np.concatenate([rows, dummy_rows]), np.concatenate([cols, dummy_cols])),
        ),
        shape=(n_ua, n_pa + n_ua),
    )
    row_ind, col_ind = min_weight_full_bipartite_matching(graph)
    real = col_ind < n_pa
    return row_ind[real].astype(np.int64), col_ind[real].astype(np.int64)


def _read_inputs(input_dir: Path, a2_metadata: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    metadata = json.loads(a2_metadata.read_text(encoding="utf-8"))
    hash_by_file = {item["file"]: item["sha256"] for item in metadata["input_inventory"]}
    frames: list[pd.DataFrame] = []
    for path in sorted(input_dir.glob("*.csv")):
        frame = pd.read_csv(path, usecols=REQUIRED)
        if frame.empty:
            continue
        frame["source_file"] = path.name
        frame["source_file_hash"] = hash_by_file[path.name]
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    numeric = set(COST_COVARIATES + ["map_mm", "valid_landcover_years", "target_landcover_years"])
    for column in numeric:
        data[column] = pd.to_numeric(data[column], errors="coerce")
        data.loc[data[column].eq(MISSING_SENTINEL), column] = np.nan
    return data, hash_by_file


def _robust_parameters(group: pd.DataFrame) -> tuple[dict[str, float], dict[str, float]]:
    medians: dict[str, float] = {}
    scales: dict[str, float] = {}
    for column in COST_COVARIATES:
        values = group[column].to_numpy(float)
        median = float(np.nanmedian(values))
        mad = float(np.nanmedian(np.abs(values - median)))
        scale = 1.4826 * mad
        if not np.isfinite(scale) or scale <= 1e-12:
            q75, q25 = np.nanpercentile(values, [75, 25])
            scale = float((q75 - q25) / 1.349)
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = float(np.nanstd(values, ddof=1))
        if not np.isfinite(scale) or scale <= 1e-12:
            scale = 1.0
        medians[column] = median
        scales[column] = scale
    return medians, scales


def _projected_xy(frame: pd.DataFrame, mean_lat: float) -> np.ndarray:
    return np.c_[
        frame["longitude"].to_numpy(float) * np.cos(np.deg2rad(mean_lat)) * 111.32,
        frame["latitude"].to_numpy(float) * 111.32,
    ]


def _haversine_km(ua_lat: np.ndarray, ua_lon: np.ndarray, pa_lat: np.ndarray, pa_lon: np.ndarray) -> np.ndarray:
    dlat = np.deg2rad(pa_lat - ua_lat)
    dlon = np.deg2rad(pa_lon - ua_lon)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.deg2rad(ua_lat)) * np.cos(np.deg2rad(pa_lat)) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _candidate_edges(
    ua: pd.DataFrame,
    pa: pd.DataFrame,
    calipers: dict[str, float],
    neighbor_cap: int,
    medians: dict[str, float],
    scales: dict[str, float],
    seed: int,
) -> pd.DataFrame:
    if ua.empty or pa.empty:
        return pd.DataFrame()
    mean_lat = float(pd.concat([ua["latitude"], pa["latitude"]]).mean())
    tree = cKDTree(_projected_xy(pa, mean_lat))
    distance, index = tree.query(
        _projected_xy(ua, mean_lat),
        k=min(neighbor_cap, len(pa)),
        distance_upper_bound=calipers["distance_km"] * 1.03,
    )
    if distance.ndim == 1:
        distance = distance[:, None]
        index = index[:, None]
    urow = np.repeat(np.arange(len(ua), dtype=np.int64), distance.shape[1])
    prow = index.reshape(-1).astype(np.int64)
    valid = np.isfinite(distance.reshape(-1)) & (prow < len(pa))
    urow, prow = urow[valid], prow[valid]
    geo = _haversine_km(
        ua["latitude"].to_numpy(float)[urow], ua["longitude"].to_numpy(float)[urow],
        pa["latitude"].to_numpy(float)[prow], pa["longitude"].to_numpy(float)[prow],
    )
    elev = np.abs(ua["elevation_m"].to_numpy(float)[urow] - pa["elevation_m"].to_numpy(float)[prow])
    mat = np.abs(ua["mat_c"].to_numpy(float)[urow] - pa["mat_c"].to_numpy(float)[prow])
    log_map = np.abs(ua["log_map_mm"].to_numpy(float)[urow] - pa["log_map_mm"].to_numpy(float)[prow])
    keep = (
        (geo <= calipers["distance_km"])
        & (elev <= calipers["elevation_m"])
        & (mat <= calipers["mat_c"])
        & (log_map <= calipers["log_map"])
    )
    urow, prow, geo = urow[keep], prow[keep], geo[keep]
    if len(urow) == 0:
        return pd.DataFrame()
    standardized: dict[str, np.ndarray] = {}
    squared = np.zeros(len(urow), dtype=float)
    for column in COST_COVARIATES:
        difference = (
            (ua[column].to_numpy(float)[urow] - medians[column]) / scales[column]
            - (pa[column].to_numpy(float)[prow] - medians[column]) / scales[column]
        )
        difference = np.clip(difference, -20, 20)
        standardized[column] = difference
        squared += difference**2
    cost = np.sqrt(squared)
    # UA and PA are stably sorted by support_unit_id before row numbering, so
    # the row-based hash is reproducible while avoiding millions of SHA calls.
    jitter = _vectorized_jitter(seed, urow, prow)
    result = pd.DataFrame({"urow": urow, "prow": prow, "geographic_distance_km": geo, "cost": cost + jitter})
    for column, values in standardized.items():
        result[f"std_diff_{column}"] = values
    return result


def _spatial_thin(data: pd.DataFrame, distance_km: float) -> pd.DataFrame:
    lon_rad = np.deg2rad(data["longitude"].to_numpy(float))
    lat_rad = np.deg2rad(np.clip(data["latitude"].to_numpy(float), -85, 85))
    x = EARTH_RADIUS_KM * lon_rad
    y = EARTH_RADIUS_KM * np.log(np.tan(np.pi / 4 + lat_rad / 2))
    work = data.assign(
        _cell_x=np.floor(x / distance_km).astype(np.int64),
        _cell_y=np.floor(y / distance_km).astype(np.int64),
    ).sort_values("support_unit_id")
    return work.drop_duplicates(["landscape", "_cell_x", "_cell_y"]).drop(columns=["_cell_x", "_cell_y"])


def apply_sensitivity(data: pd.DataFrame, name: str) -> pd.DataFrame:
    if name == "primary":
        return data
    if name == "tier1_only":
        return data[data["pft_tier"] == "Tier1"]
    if name == "tier2_only":
        return data[data["pft_tier"] == "Tier2"]
    if name == "tier2_tree40":
        # GEE exports vegetation_fraction on the 0--1 scale; the definition is
        # named for the equivalent 40% threshold.
        return data[(data["pft_tier"] == "Tier2") & (data["vegetation_fraction"] >= 0.40)]
    if name == "stability85":
        return data[data["target_landcover_years"] / data["valid_landcover_years"] >= 0.85]
    if name == "stability90":
        return data[data["target_landcover_years"] / data["valid_landcover_years"] >= 0.90]
    if name.startswith("thin"):
        return _spatial_thin(data, float(name.removeprefix("thin").removesuffix("km")))
    raise ValueError(f"Unknown sensitivity: {name}")


def run_matching(
    data: pd.DataFrame,
    spec: dict,
    seed: int,
    script_hash: str,
    config_hash: str,
    source_manifest_hash: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required_complete = EXACT + COST_COVARIATES + ["map_mm"]
    usable = data.dropna(subset=required_complete).copy()
    pair_frames: list[pd.DataFrame] = []
    scaling_rows: list[dict[str, object]] = []
    stratum_rows: list[dict[str, object]] = []
    calipers = spec["calipers"]
    neighbor_cap = int(spec["candidate_graph"]["pa_neighbors_per_ua"])
    for key, group in usable.groupby(EXACT, sort=True, dropna=False):
        ua = group[group["landscape"] == "UA"].sort_values("support_unit_id").reset_index(drop=True)
        pa = group[group["landscape"] == "PA"].sort_values("support_unit_id").reset_index(drop=True)
        if ua.empty or pa.empty:
            continue
        medians, scales = _robust_parameters(group)
        for column in COST_COVARIATES:
            scaling_rows.append(
                {
                    "ecoregion_id": key[0], "biome_id": key[1], "pft_tier": key[2],
                    "covariate": column, "median": medians[column], "scale": scales[column],
                }
            )
        edges = _candidate_edges(ua, pa, calipers, neighbor_cap, medians, scales, seed)
        if edges.empty:
            stratum_rows.append(
                {"ecoregion_id": key[0], "biome_id": key[1], "pft_tier": key[2], "ua_units": len(ua), "pa_units": len(pa), "candidate_edges": 0, "matched_pairs": 0}
            )
            continue
        matched_u, matched_p = _min_cost_max_cardinality(
            len(ua), len(pa), edges["urow"].to_numpy(np.int64), edges["prow"].to_numpy(np.int64), edges["cost"].to_numpy(float)
        )
        edge_lookup = edges.set_index(["urow", "prow"])
        chosen = edge_lookup.loc[list(zip(matched_u, matched_p))].reset_index()
        u = ua.iloc[matched_u].reset_index(drop=True)
        p = pa.iloc[matched_p].reset_index(drop=True)
        out = pd.DataFrame(
            {
                "ua_support_unit_id": u["support_unit_id"].astype(str),
                "pa_support_unit_id": p["support_unit_id"].astype(str),
                "city_id": u["city_id"].to_numpy(),
                "pa_id": p["pa_id"].to_numpy(),
                "ecoregion_id": key[0], "biome_id": key[1], "pft_tier": key[2],
                "ua_continental_region": u["continental_region"].to_numpy(),
                "pa_continental_region": p["continental_region"].to_numpy(),
                "ua_climate_zone": u["climate_zone"].to_numpy(),
                "pa_climate_zone": p["climate_zone"].to_numpy(),
                "geographic_distance_km": chosen["geographic_distance_km"].to_numpy(),
                "matching_cost": chosen["cost"].to_numpy(),
                "pair_weight": 1.0,
                "ua_source_file": u["source_file"].to_numpy(),
                "pa_source_file": p["source_file"].to_numpy(),
                "ua_source_file_hash": u["source_file_hash"].to_numpy(),
                "pa_source_file_hash": p["source_file_hash"].to_numpy(),
            }
        )
        for column in COST_COVARIATES + ["map_mm"]:
            out[f"ua_{column}"] = u[column].to_numpy()
            out[f"pa_{column}"] = p[column].to_numpy()
        for column in COST_COVARIATES:
            out[f"std_diff_{column}"] = chosen[f"std_diff_{column}"].to_numpy()
        out["configuration_hash"] = config_hash
        out["source_table_manifest_hash"] = source_manifest_hash
        out["matching_script_hash"] = script_hash
        pair_frames.append(out)
        stratum_rows.append(
            {"ecoregion_id": key[0], "biome_id": key[1], "pft_tier": key[2], "ua_units": len(ua), "pa_units": len(pa), "candidate_edges": len(edges), "matched_pairs": len(out)}
        )
    pairs = pd.concat(pair_frames, ignore_index=True) if pair_frames else pd.DataFrame()
    if not pairs.empty:
        pairs = pairs.sort_values(EXACT + ["ua_support_unit_id", "pa_support_unit_id"]).reset_index(drop=True)
        pairs.insert(0, "pair_id", [f"pair_{i:09d}" for i in range(1, len(pairs) + 1)])
    return pairs, pd.DataFrame(scaling_rows), pd.DataFrame(stratum_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--a2-metadata", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sensitivity", action="append", default=[])
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    script_hash = sha256_file(Path(__file__))
    config_hash = spec["configuration_sha256"]
    source_manifest_hash = sha256_file(args.a2_metadata)
    runs = [] if args.inventory_only else ["primary", *args.sensitivity]
    data = pd.DataFrame()
    if runs:
        data, _ = _read_inputs(args.input_dir, args.a2_metadata)
    summary_rows: list[dict[str, object]] = []
    for name in runs:
        selected = apply_sensitivity(data, name)
        pairs, scaling, strata = run_matching(selected, spec, int(spec["candidate_graph"]["tie_break_seed"]), script_hash, config_hash, source_manifest_hash)
        suffix = "primary" if name == "primary" else f"sensitivity_{name}"
        pairs.to_parquet(args.output_dir / f"a3_pairs_{suffix}.parquet", index=False)
        scaling.to_csv(args.output_dir / f"a3_scaling_{suffix}.csv", index=False)
        strata.to_csv(args.output_dir / f"a3_matching_strata_{suffix}.csv", index=False)
        summary_rows.append(
            {
                "run": name, "input_units": len(selected), "matched_pairs": len(pairs),
                "unique_cities": int(pairs["city_id"].nunique()) if len(pairs) else 0,
                "unique_pas": int(pairs["pa_id"].nunique()) if len(pairs) else 0,
                "continental_regions": int(pairs["ua_continental_region"].nunique()) if len(pairs) else 0,
                "climate_zones": int(pairs["ua_climate_zone"].nunique()) if len(pairs) else 0,
                "status": "available",
            }
        )
    # Rebuild the inventory from all extant pair tables so incremental runs do
    # not erase previously completed sensitivity summaries.
    summary_rows = []
    for pair_path in sorted(args.output_dir.glob("a3_pairs_*.parquet")):
        pair_table = pd.read_parquet(
            pair_path,
            columns=["city_id", "pa_id", "ua_continental_region", "ua_climate_zone"],
        )
        suffix = pair_path.stem.removeprefix("a3_pairs_")
        run_name = "primary" if suffix == "primary" else suffix.removeprefix("sensitivity_")
        summary_rows.append(
            {
                "run": run_name,
                "input_units": np.nan,
                "matched_pairs": len(pair_table),
                "unique_cities": int(pair_table["city_id"].nunique()),
                "unique_pas": int(pair_table["pa_id"].nunique()),
                "continental_regions": int(pair_table["ua_continental_region"].nunique()),
                "climate_zones": int(pair_table["ua_climate_zone"].nunique()),
                "status": "available",
            }
        )
    summary_rows.append(
        {"run": "tier2_tree20", "input_units": np.nan, "matched_pairs": np.nan, "unique_cities": np.nan, "unique_pas": np.nan, "continental_regions": np.nan, "climate_zones": np.nan, "status": "unavailable_from_frozen_tree30_support_table"}
    )
    pd.DataFrame(summary_rows).to_csv(args.output_dir / "a3_matching_summary.csv", index=False)
    metadata = {
        "schema_version": "gate-a3-match-1.0",
        "matching_spec_hash": sha256_file(args.spec),
        "matching_script_hash": script_hash,
        "a2_support_metadata_hash": source_manifest_hash,
        "runs": [row["run"] for row in summary_rows if row["status"] == "available"],
        "outcome_blind": True,
    }
    (args.output_dir / "a3_matching_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary_rows, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
