"""Export current manuscript Tables 1/2 and S10 with explicit reproduction levels."""
from pathlib import Path
import argparse
import json
import os

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = Path(os.environ.get("PHENOLOGY_OUTPUT", str(ROOT / "reproduced"))).resolve()
STAT_KEYS = ["mean", "q05", "q25", "median", "q75", "q95"]
DERIVED = "derived_from_pair_statistics"
AGGREGATE = "aggregate_only"


def read_csv(path):
    return pd.read_csv(path, float_precision="round_trip")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal(value, expected, label):
    require(np.isclose(float(value), float(expected), rtol=0, atol=1e-10),
            f"Reference mismatch: {label}: {value!r} != {expected!r}")


def stats(values):
    values = np.asarray(values, dtype=float)
    require(values.size > 0 and np.isfinite(values).all(), "Non-finite or empty distribution.")
    return dict(zip(STAT_KEYS, [float(values.mean()),
                               *np.quantile(values, [.05, .25, .5, .75, .95], method="linear").tolist()]))


def display(value, digits=2):
    rounded = round(float(value), digits)
    if rounded == 0:
        rounded = 0.0
    return f"{rounded:.{digits}f}".replace("-", "−")


def interval(row, low, high):
    return f"{display(row[low])} to {display(row[high])}"


def main_tables(destination):
    previous_check = read_json(destination / "table_checks.json")
    require(previous_check.get("all_passed") is True, "Run check_tables.py successfully before exporting main tables.")
    w = read_csv(DATA / "pair_window_summaries.csv")
    support = read_csv(DATA / "summary/FigS3_support_source_v01.csv")
    require(w.pair_id.is_unique and support.pair_id.is_unique and set(w.pair_id) == set(support.pair_id),
            "Pair/support rosters differ.")
    complete = w.loc[w.complete22 == 1]
    require((complete.n_full == 22).all() and (complete.n_recent == 12).all(), "Complete-period denominators differ.")
    zero = set(support.loc[support.n_strict == 0, "pair_id"])
    reference1 = read_csv(DATA / "summary/Table1_descriptive_support.csv").set_index("group")
    reference2 = read_csv(DATA / "summary/Table2_sensitivity_contrasts.csv").set_index("contrast")
    aggregate_json = read_json(DATA / "summary/figure_source_data_v01.json")
    for frame, rows, key in [(reference1, aggregate_json["groups"], "group"),
                             (reference2, aggregate_json["contrasts"], "contrast")]:
        for row in rows:
            for field, value in row.items():
                if field != key:
                    equal(frame.loc[row[key], field], value, f"archived {row[key]}/{field}")
    settings = [
        ("main_all", "Main filter, all pairs", w, "n_full", "sum_full_days"),
        ("main_complete22", "Main filter, complete 22-year records", complete, "n_full", "sum_full_days"),
        ("main_incomplete", "Main filter, incomplete records", w.loc[w.complete22 == 0], "n_full", "sum_full_days"),
        ("strict_native", "Strict filter, supported pairs", None, None, None),
        ("main_on_strict_roster", "Main filter, strict-supported roster", w.loc[~w.pair_id.isin(zero)], "n_full", "sum_full_days"),
        ("recent_native", "Recent window, all pairs", w, "n_recent", "sum_recent_days"),
        ("recent_complete22", "Recent window, complete-record cohort", complete, "n_recent", "sum_recent_days"),
    ]
    rows1 = []
    for key, label, subset, n_col, sum_col in settings:
        reference = reference1.loc[key]
        if subset is None:
            values = {field: float(reference[field]) for field in STAT_KEYS}
            pairs, pair_years, level = int(reference.pairs), int(reference.pair_years), AGGREGATE
        else:
            values = stats(subset[sum_col] / subset[n_col])
            pairs, pair_years, level = len(subset), int(subset[n_col].sum()), DERIVED
        equal(pairs, reference.pairs, key + "/pairs")
        equal(pair_years, reference.pair_years, key + "/pair_years")
        for field in STAT_KEYS:
            equal(values[field], reference[field], key + "/" + field)
        rows1.append(dict(group=key, analysis_setting=label, pairs=pairs,
                          pair_years=pair_years, **values, reproduction_level=level))
    pd.DataFrame(rows1).to_csv(destination / "Table1_current.csv", index=False)
    formatted1 = [{"Analysis setting": row["analysis_setting"], "Pairs": f'{row["pairs"]:,}',
                   "Pair-years": f'{row["pair_years"]:,}', "Mean": display(row["mean"]),
                   "Median": display(row["median"]), "25th–75th": interval(row, "q25", "q75"),
                   "5th–95th": interval(row, "q05", "q95")} for row in rows1]
    pd.DataFrame(formatted1).to_csv(destination / "Table1_current_formatted.csv", index=False)

    rows2 = []
    comparisons = [
        ("strict_vs_main", "Strict minus main filter", None),
        ("recent_vs_full", "Recent minus full window, all pairs", w),
        ("recent_vs_full_complete22", "Recent minus full window, complete-record cohort", complete),
    ]
    for key, label, subset in comparisons:
        reference = reference2.loc[key]
        expected = {"mean": reference.same_pair_mean_change,
                    **{field: reference["paired_change_" + field] for field in STAT_KEYS if field != "mean"}}
        values = expected.copy() if subset is None else stats(subset.sum_recent_days / subset.n_recent - subset.sum_full_days / subset.n_full)
        pairs = int(reference.paired_roster) if subset is None else len(subset)
        equal(pairs, reference.paired_roster, key + "/shared_pairs")
        for field in STAT_KEYS:
            equal(values[field], expected[field], key + "/" + field)
        rows2.append(dict(contrast=key, comparison=label, shared_pairs=pairs, **values,
                          reproduction_level=AGGREGATE if subset is None else DERIVED))

    # The non-overlapping comparison is already part of the archived analysis.
    # Derive it from the same complete cohort, and compare both archived and freshly
    # generated references; do not relabel the nested recent-minus-full contrast.
    changes = complete.sum_recent_days / 12 - (complete.sum_full_days - complete.sum_recent_days) / 10
    recent_early = stats(changes)
    archived_revision = read_json(DATA / "revision_results.json")
    generated_revision = read_json(destination / "revision_results.json")
    for revision, source in [(archived_revision, "archived"), (generated_revision, "generated")]:
        equal(len(complete), revision["recent_minus_early"]["n"], source + "/recent_minus_early/n")
        for field in STAT_KEYS:
            equal(recent_early[field], revision["recent_minus_early"][field], source + "/recent_minus_early/" + field)
    generated_pairs = read_csv(destination / "complete_pair_periods.csv").set_index("pair_id")
    require(generated_pairs.index.is_unique and set(generated_pairs.index) == set(complete.pair_id),
            "Generated cross-period roster differs.")
    expected_change = pd.Series(changes.to_numpy(), index=complete.pair_id).sort_index()
    require(np.allclose(generated_pairs.recent_minus_early_days.sort_index().to_numpy(),
                        expected_change.to_numpy(), atol=1e-12, rtol=0), "Cross-period pair changes differ.")
    rows2.append(dict(contrast="recent_vs_early_complete22",
                      comparison="Recent (2013–2024) minus early (2003–2012), complete-record cohort",
                      shared_pairs=len(complete), **recent_early, reproduction_level=DERIVED))
    pd.DataFrame(rows2).to_csv(destination / "Table2_current.csv", index=False)
    formatted2 = [{"Comparison B minus A": row["comparison"], "Shared pairs": f'{row["shared_pairs"]:,}',
                   "Mean change": display(row["mean"]), "Median change": display(row["median"]),
                   "25th–75th": interval(row, "q25", "q75"), "5th–95th": interval(row, "q05", "q95")}
                  for row in rows2]
    pd.DataFrame(formatted2).to_csv(destination / "Table2_current_formatted.csv", index=False)
    return [dict(table="Table1", row=row["group"], level=row["reproduction_level"], reference_match=True) for row in rows1] + [
        dict(table="Table2", row=row["contrast"], level=row["reproduction_level"], reference_match=True) for row in rows2]


def overlap_table(destination):
    reference_dir = DATA / "overlap/reference"
    current_dir = OUTPUT / "overlap"
    for name in ["sensitivity_by_threshold.csv", "overlap_distributions.csv"]:
        current, reference = read_csv(current_dir / name), read_csv(reference_dir / name)
        require(list(current.columns) == list(reference.columns), f"Column mismatch: {name}")
        require(current["group"].is_unique and reference["group"].is_unique, f"Duplicate groups: {name}")
        pd.testing.assert_frame_equal(current.sort_values("group").reset_index(drop=True),
                                      reference.sort_values("group").reset_index(drop=True),
                                      check_dtype=False, check_exact=False, atol=1e-10, rtol=1e-12)
    current = read_csv(current_dir / "sensitivity_by_threshold.csv").set_index("group")
    group_order = ["frozen_full", "f_ua_ge_0.25", "f_ua_ge_0.50"]
    require(set(current.index) == set(group_order), "Unexpected S10 cohorts.")
    current = current.loc[group_order].copy()
    current["reproduction_level"] = "derived_from_pair_statistics_and_archived_GEE_overlap"
    current.reset_index().to_csv(destination / "Table_S10_current.csv", index=False)
    metrics = [
        ("Matched pairs", "pairs", "integer"),
        ("Supported pair-years", "pair_years", "integer"),
        ("Complete-record pairs", "complete_pairs", "integer"),
        ("Original roster retained (%)", "retained_pct", "number"),
        ("Mean UA minus PA (days)", "mean_days", "number"),
        ("Interquartile range (days)", None, "range"),
        ("UA earlier (%)", "earlier_pct", "number"),
        ("UA later (%)", "later_pct", "number"),
        ("Exact zero (%)", "zero_pct", "number"),
        ("Cross-period Spearman ρ", "spearman_rho", "rho"),
        ("Same nonzero direction (%)", "same_nonzero_pct", "number"),
        ("Opposite nonzero directions (%)", "opposite_nonzero_pct", "number"),
        ("Nearctic (%)", "nearctic_pct", "number"),
        ("Palearctic (%)", "palearctic_pct", "number"),
        ("Unclassified realm (%)", "unclassified_realm_pct", "number"),
        ("Tier 1 (%)", "tier1_pct", "number"),
        ("Tier 2 (%)", "tier2_pct", "number"),
    ]
    formatted = []
    for label, field, kind in metrics:
        row = {"Metric": label}
        for key, heading in zip(group_order, ["Full roster", "Coverage ≥25%", "Coverage ≥50%"]):
            source = current.loc[key]
            row[heading] = (f"{int(source[field]):,}" if kind == "integer" else
                            interval(source, "q25_days", "q75_days") if kind == "range" else
                            display(source[field], 3 if kind == "rho" else 2))
        formatted.append(row)
    pd.DataFrame(formatted).to_csv(destination / "Table_S10_current_formatted.csv", index=False)
    return [dict(table="TableS10", row=key, level=current.loc[key, "reproduction_level"],
                 reference_match=True) for key in group_order]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--section", choices=["main", "overlap", "all"], default="all")
    args = parser.parse_args()
    destination = OUTPUT / "tables"
    destination.mkdir(parents=True, exist_ok=True)
    checks = []
    if args.section in ["main", "all"]:
        checks.extend(main_tables(destination))
    if args.section in ["overlap", "all"]:
        checks.extend(overlap_table(destination))
    report = dict(status="PASS", section=args.section, checks=checks,
                  uncertainty="Quantiles describe empirical dispersion; no inferential intervals are generated.",
                  temporal_scope="Recent-minus-early uses non-overlapping periods in the complete-record cohort; recent-minus-full remains a nested-window comparison.",
                  overlap_scope="Threshold summaries use archived GEE overlap returns; no geometry query is repeated.")
    (destination / f"current_table_export_{args.section}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(status="PASS", section=args.section, checked_rows=len(checks))))


if __name__ == "__main__":
    main()
