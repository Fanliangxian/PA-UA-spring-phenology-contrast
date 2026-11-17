"""Validate GEE geometry returns and summarize fixed-pair overlap sensitivity."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
VERSION = "E1_UA_pixel_overlap_v01"
N = 18862
BREAKS = [1, 2359, 4717, 7075, 9433, 11791, 14149, 16507, 18863]
PILOT = {1, 2, 947, 5618, 11172, 9775, 5804, 6451}
AREA = 463.3127165279165 * 463.3127165279167
MAX_AREA_ROUNDOFF_M2 = 0.1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def percent(count, total):
    return 100 * count / total if total else None


def summarize(x, label):
    n = len(x)
    m = x.sum_full_days / x.n_full
    c = x.loc[x.complete22.eq(1)]
    a, b = c.sum_full_days - c.sum_recent_days, c.sum_recent_days
    same = int((np.sign(a).eq(np.sign(b)) & a.ne(0)).sum())
    opposite = int((np.sign(a) * np.sign(b)).eq(-1).sum())
    rho = float(a.rank().corr(b.rank())) if a.nunique() > 1 and b.nunique() > 1 else None
    return {
        "group": label, "pairs": n, "retained_pct": percent(n, N),
        "pair_years": int(x.n_full.sum()), "complete_pairs": len(c),
        "mean_days": float(m.mean()) if n else None,
        "q25_days": float(m.quantile(.25)) if n else None,
        "q75_days": float(m.quantile(.75)) if n else None,
        "earlier_pct": percent(int(x.sum_full_days.lt(0).sum()), n),
        "later_pct": percent(int(x.sum_full_days.gt(0).sum()), n),
        "zero_pct": percent(int(x.sum_full_days.eq(0).sum()), n),
        "spearman_rho": rho, "same_nonzero_n": same, "opposite_nonzero_n": opposite,
        "same_nonzero_pct": percent(same, len(c)),
        "opposite_nonzero_pct": percent(opposite, len(c)),
        "at_least_one_zero_n": len(c) - same - opposite,
        "nearctic_pct": percent(int(x.ua_continental_region.eq(5).sum()), n),
        "palearctic_pct": percent(int(x.ua_continental_region.eq(8).sum()), n),
        "unclassified_realm_pct": percent(int(x.ua_continental_region.eq(-1).sum()), n),
        "tier1_pct": percent(int(x.pft_tier.eq("Tier1").sum()), n),
        "tier2_pct": percent(int(x.pft_tier.eq("Tier2").sum()), n),
    }


def validate(returns, old, pilot):
    suffixes = ["PILOT"] if pilot else [f"B0{i}" for i in range(8)]
    frames = []
    for suffix in suffixes:
        f = pd.read_csv(returns / f"{VERSION}_{suffix}.csv", float_precision="round_trip")
        serial = f.pair_id.str.rsplit("_", n=1).str[-1].astype(int)
        expected = PILOT if pilot else set(range(BREAKS[int(suffix[-1])], BREAKS[int(suffix[-1]) + 1]))
        require(set(serial) == expected and len(f) == len(expected), f"Wrong roster in {suffix}")
        require(f.part.eq(suffix).all(), f"Wrong part label in {suffix}")
        frames.append(f)
    x = pd.concat(frames, ignore_index=True)
    require(x.pair_id.is_unique, "Duplicate returned pair IDs")
    a = x.merge(old, on="pair_id", suffixes=("", "_audit"), validate="one_to_one", how="left")
    for got, expected in [
        ("support_unit_id", "support_unit_id_audit"),
        ("native_col", "native_col_audit"), ("native_row", "native_row_audit"),
        ("ua_asset", "buffered_asset"), ("coordinate_asset", "coordinate_asset_audit"),
        ("source_pairs_sha256", "source_pairs_sha256_audit"), ("native_crs", "native_crs_audit"),
    ]:
        require(a[got].eq(a[expected]).all(), f"Identity mismatch in {got}")
    for field in ("longitude", "latitude"):
        require(np.allclose(a[field], a[f"{field}_audit"], rtol=0, atol=1e-10), f"Frozen coordinate mismatch in {field}")
    require(a.version.eq(VERSION).all() and a.tolerance_m.eq(.1).all(), "Unexpected method or tolerance")
    require(a.center_offset_m.between(0, .25).all(), "Coordinate is not at the expected native cell centre")
    require(np.allclose(a.cell_area_m2, AREA, atol=.1, rtol=0), "Unexpected native cell area")
    require(a.candidate_features.ge(0).all() and (a.candidate_features % 1 == 0).all(), "Invalid candidate counts")
    require(not (a.candidate_features.eq(0) & a.f_ua.gt(0)).any(), "Positive area without a candidate feature")
    require(np.allclose(a.intersection_area_m2 / a.cell_area_m2, a.f_ua, atol=1e-10, rtol=0),
            "Area and fraction disagree")
    excess = a.intersection_area_m2 - a.cell_area_m2
    require(a.f_ua.ge(0).all() and a.intersection_area_m2.ge(0).all()
            and excess.le(MAX_AREA_ROUNDOFF_M2).all(),
            "Intersection area outside physical bounds beyond numerical tolerance")
    x["f_ua_raw"] = a.f_ua
    x["area_excess_m2"] = excess.clip(lower=0)
    x["upper_roundoff_clamped"] = a.f_ua.gt(1)
    x["f_ua"] = a.f_ua.clip(upper=1)
    point = a.point_inside_buffered.astype(str).str.lower().map({"0": 0, "1": 1, "false": 0, "true": 1})
    require(point.notna().all(), "Invalid point containment flag")
    require(point.eq(a.point_inside_buffered_audit).all(), "Point classification differs from archived audit")
    x["point_inside_buffered"] = point
    return x


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=BASE, help="Unified repository root")
    parser.add_argument("--returns", type=Path, default=BASE / "data/overlap/incoming")
    parser.add_argument("--output", type=Path, default=BASE / "reproduced/overlap")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pilot", action="store_true")
    mode.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()
    data = args.base / "data"
    old = pd.read_csv(data / "spatial/completed_18862_spatial_rows.csv", float_precision="round_trip")
    require(len(old) == N and old.pair_id.is_unique and int(old.point_inside_buffered.eq(0).sum()) == 8807,
            "Unexpected archived spatial roster")
    if args.pilot:
        x = validate(args.returns, old, pilot=True)
        print(x[["pair_id", "point_inside_buffered", "f_ua", "area_excess_m2",
                 "upper_roundoff_clamped"]].to_string(index=False))
        return
    w = pd.read_csv(data / "pair_window_summaries.csv")
    f = pd.read_csv(data / "frozen_pairs.csv", usecols=["pair_id", "pft_tier", "ua_continental_region"])
    w = w.merge(f, on="pair_id", validate="one_to_one")
    require(len(w) == N and set(w.pair_id) == set(old.pair_id), "Derived statistics roster mismatch")
    require(w.pft_tier.isin(["Tier1", "Tier2"]).all() and
            w.ua_continental_region.isin([5, 8, -1]).all(), "Unexpected composition codes")
    require(w.n_full.gt(0).all() and w.n_full.eq(22).eq(w.complete22.eq(1)).all()
            and w.loc[w.complete22.eq(1), "n_recent"].eq(12).all(), "Window completeness mismatch")
    base = summarize(w, "frozen_full")
    require(base["pair_years"] == 403981 and base["complete_pairs"] == 14180
            and base["same_nonzero_n"] == 11423 and base["opposite_nonzero_n"] == 2540
            and round(base["mean_days"], 2) == -.99 and round(base["earlier_pct"], 2) == 56.10
            and round(base["spearman_rho"], 3) == .811
            and int(w.pft_tier.eq("Tier1").sum()) == 5896, "Frozen baseline mismatch")
    if args.baseline_only:
        print(json.dumps(base, indent=2))
        return
    x = validate(args.returns, old, pilot=False)
    w = w.merge(x[["pair_id", "f_ua"]], on="pair_id", validate="one_to_one")
    require(len(w) == N, "Join did not retain all frozen pairs")
    groups = [base] + [summarize(w.loc[w.f_ua.ge(t)], f"f_ua_ge_{t:.2f}") for t in (.25, .50)]
    distributions = []
    for label, values in [("all", x.f_ua), ("point_outside", x.loc[x.point_inside_buffered.eq(0), "f_ua"]),
                          ("point_inside", x.loc[x.point_inside_buffered.eq(1), "f_ua"])]:
        distributions.append({"group": label, "n": len(values), "zero_area_n": int(values.eq(0).sum()),
                              **{f"p{q}": float(values.quantile(q / 100)) for q in (0, 5, 25, 50, 75, 95, 100)}})
    args.output.mkdir(parents=True, exist_ok=True)
    x.to_csv(args.output / "validated_pixel_overlap.csv", index=False)
    x.loc[x.f_ua.eq(0)].to_csv(args.output / "zero_area_rows_for_review.csv", index=False)
    pd.DataFrame(groups).to_csv(args.output / "sensitivity_by_threshold.csv", index=False)
    pd.DataFrame(distributions).to_csv(args.output / "overlap_distributions.csv", index=False)
    print("Full roster validated. Review all zero-area rows before interpreting sensitivity results.")


if __name__ == "__main__":
    main()
