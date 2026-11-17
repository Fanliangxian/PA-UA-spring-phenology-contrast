"""Visualize period means from the archived complete-record cohort."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.patches import Rectangle
import numpy as np

root = Path(__file__).resolve().parents[2]
data = root / "data"
source = data / "complete_pair_periods.csv"
with source.open(encoding="utf-8-sig", newline="") as file:
    rows = list(csv.DictReader(file))
assert len(rows) == len({r["pair_id"] for r in rows}) == 14180
early = np.array([float(r["mean_early_days"]) for r in rows])
recent = np.array([float(r["mean_recent_days"]) for r in rows])
change = np.array([float(r["recent_minus_early_days"]) for r in rows])
assert np.isfinite([early, recent, change]).all()
assert np.allclose(change, recent - early, atol=1e-12, rtol=0)

def tied_ranks(values):
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    return (np.cumsum(counts) - (counts - 1) / 2)[inverse]

rho = np.corrcoef(tied_ranks(early), tied_ranks(recent))[0, 1]
signs = [-1, 0, 1]
matrix = np.array([[np.count_nonzero((np.sign(early) == i) & (np.sign(recent) == j))
                    for j in signs] for i in signs])
with (data / "Table_S5_sign_transitions.csv").open(encoding="utf-8-sig", newline="") as file:
    expected = {(int(r["early_sign"]), int(r["recent_sign"])): int(r["count"])
                for r in csv.DictReader(file)}
assert matrix.tolist() == [[expected[i, j] for j in signs] for i in signs]
same = int(matrix[0, 0] + matrix[2, 2])
opposite = int(matrix[0, 2] + matrix[2, 0])
zero = len(rows) - same - opposite
lo, median, hi = np.quantile(change, [.05, .5, .95], method="linear")
assert (round(rho, 3), same, opposite, zero) == (.811, 11423, 2540, 217)
assert tuple(np.round([lo, median, hi], 2)) == (-5.97, -.10, 5.62)

mpl.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.linewidth": .65,
    "axes.spines.top": False, "axes.spines.right": False,
    "svg.fonttype": "none", "pdf.fonttype": 42, "savefig.dpi": 600,
})
blue, ink, gray = "#4260CF", "#24364E", "#7C858E"
width_in = 183 / 25.4
height_in = 136 / 25.4
fig = plt.figure(figsize=(width_in, height_in), facecolor="white")
a = fig.add_axes([.10, .44, .34, .46])
b = fig.add_axes([.62, .47, .31, .39])
c = fig.add_axes([.10, .105, .83, .20])
bar = fig.add_axes([.443, .515, .013, .25])
limit = 10 * np.ceil(np.abs([early, recent]).max() / 10)
hex_colors = LinearSegmentedColormap.from_list("hex_counts", mpl.colormaps["Blues"](np.linspace(.13, 1, 256)))
hexes = a.hexbin(early, recent, gridsize=59, mincnt=1,
                 extent=(-limit, limit, -limit, limit),
                 cmap=hex_colors, norm=LogNorm(), linewidths=0)
assert int(hexes.get_array().sum()) == len(rows)
a.plot([-limit, limit], [-limit, limit], color="#343F4E", lw=.65, ls="--")
a.axhline(0, color=gray, lw=.6)
a.axvline(0, color=gray, lw=.6)
a.set(xlim=(-limit, limit), ylim=(-limit, limit), aspect="equal",
      xlabel="2003–2012 mean contrast (days)", ylabel="2013–2024 mean contrast (days)")
fig.text(.10, .94, "a  Pairwise means across periods", fontsize=9, fontweight="bold")
a.text(.05, .95, f"n = {len(rows):,}\nSpearman ρ = {rho:.3f}", transform=a.transAxes,
       va="top", color=ink, bbox={"fc": "white", "ec": "none", "alpha": .92, "pad": 2})
cb = fig.colorbar(hexes, cax=bar, ticks=[1, 10, 100], format="%d")
cb.set_label("Pairs per hexagon", labelpad=3, fontsize=7)
cb.ax.tick_params(labelsize=6, length=2)
cb.ax.minorticks_off()

b.imshow(matrix, cmap="Blues", vmin=0, vmax=matrix.max() * 1.15)
for i in range(3):
    for j in range(3):
        b.text(j, i, f"{matrix[i, j]:,}", ha="center", va="center",
               color="white" if matrix[i, j] > 3000 else ink, fontsize=9)
for i in (0, 2):
    b.add_patch(Rectangle((i-.48, i-.48), .96, .96, fill=False, ec=ink, lw=1))
categories = ["UA earlier", "Zero", "UA later"]
b.set(xticks=range(3), xticklabels=categories, yticks=range(3), yticklabels=categories,
      xlabel="2013–2024 direction", ylabel="2003–2012 direction")
b.tick_params(length=0, pad=4)
for spine in b.spines.values():
    spine.set_visible(False)
fig.text(.63, .94, "b  Direction transitions", fontsize=9, fontweight="bold")
fig.text(.63, .89, f"{same / len(rows):.2%} same nonzero direction", color=ink, fontsize=7.5)

edges = np.arange(np.floor(change.min()) - .5, np.ceil(change.max()) + 1.5)
counts, _, _ = c.hist(change, bins=edges, color=blue, alpha=.85,
                      edgecolor="white", linewidth=.25, zorder=2)
assert int(counts.sum()) == len(rows)
c.axvspan(lo, hi, color="#DAE4FC", alpha=.7, zorder=0)
c.axvline(0, color=gray, lw=.7, ls="--", zorder=3)
c.axvline(median, color=ink, lw=1, zorder=4)
c.set(xlabel="Within-pair change, recent minus early (days)", ylabel="Pairs",
      xlim=(edges[0], edges[-1]))
c.set_title("c  Change in each pair’s mean contrast", loc="left", fontweight="bold", pad=8)
c.text(.985, .95, "Median −0.10 days\n5th–95th percentiles: −5.97 to 5.62 days",
       transform=c.transAxes, ha="right", va="top", color=ink, fontsize=7.5)
import os
out = Path(os.environ.get('PHENOLOGY_OUTPUT', str(root/'reproduced'))).resolve() / 'figures' / 'Figure4'
out.mkdir(parents=True,exist_ok=True)
fig.savefig(out / "Figure4_cross_period.png", dpi=600)
fig.savefig(out / "Figure4_cross_period.svg")
fig.savefig(out / "Figure4_cross_period.pdf")
fig.savefig(out / "Figure4_cross_period.tiff", dpi=600, pil_kwargs={"compression": "tiff_lzw"})
plt.close(fig)
(out / "Figure4_verification.json").write_text(json.dumps({
    "cohort": "14,180 matched pairs with complete 22-year main-filter records",
    "claim": "Observed pairwise contrasts often retain direction and ordering, with changes in magnitude.",
    "source": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "panel_a": {"x": "mean_early_days", "y": "mean_recent_days", "hex_grid": 59,
                "scale": "logarithmic count color scale", "rho": rho, "n": len(rows)},
    "panel_b": {"rows": signs, "columns": signs, "counts": matrix.tolist(),
                "same_nonzero": same, "opposite_nonzero": opposite, "any_zero": zero},
    "panel_c": {"variable": "recent_minus_early_days", "bin_width_days": 1,
                "quantile_method": "linear", "q05": lo, "median": median, "q95": hi},
    "width_mm": 183, "height_mm": 136, "raster_dpi": 600,
    "plotted_rows": len(rows), "excluded_rows": 0
}, indent=2) + "\n", encoding="utf-8")
