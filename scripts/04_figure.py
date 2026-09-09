"""Plot my task exposure estimates against Felten AIOE on matched occupations."""

import csv
from pathlib import Path
from statistics import correlation, linear_regression

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
with (ROOT / "results/hybrid/comparison_occupation.csv").open(newline="") as source:
    rows = list(csv.DictReader(source))
x = [float(row["task_exposure"]) for row in rows]
y = [float(row["AIOE"]) for row in rows]


def ranks(values):
    """Assign average ranks to ties for the Spearman correlation."""
    ordered = sorted(values)
    return [(ordered.index(value) + len(values) - ordered[::-1].index(value) + 1) / 2
            for value in values]


pearson = correlation(x, y)
spearman = correlation(ranks(x), ranks(y))
slope, intercept = linear_regression(x, y)
fig, ax = plt.subplots(figsize=(8, 6), facecolor="white", layout="constrained")
ax.set_facecolor("white")
ax.scatter(x, y, s=12, color="#888888", alpha=0.55, linewidths=0)
limits = [min(x), max(x)]
ax.plot(limits, [intercept + slope * value for value in limits],
        color="#333333", linewidth=1)
ax.text(0.03, 0.97, f"Spearman = {spearman:.4f}\nPearson = {pearson:.4f}",
        transform=ax.transAxes, va="top", fontsize=10)

# Short labels and point offsets keep the eight largest rank disagreements legible.
labels = {
    "Models": ("Models", (20, -25)),
    "Exercise Trainers and Group Fitness Instructors": ("Fitness instructors", (-15, -28)),
    "Choreographers": ("Choreographers", (-90, -18)),
    "Gambling Change Persons and Booth Cashiers": ("Gambling cashiers", (-100, -24)),
    "Meter Readers, Utilities": ("Meter readers", (24, 3)),
    "Marriage and Family Therapists": ("Family therapists", (-105, 24)),
    "Desktop Publishers": ("Desktop publishers", (-95, -18)),
    "Manicurists and Pedicurists": ("Manicurists", (-25, 28)),
}
for row in sorted(rows, key=lambda row: abs(float(row["rank_gap"])), reverse=True)[:8]:
    label, offset = labels.get(row["title"], (row["title"], (8, 8)))
    ax.annotate(label, (float(row["task_exposure"]), float(row["AIOE"])),
                xytext=offset, textcoords="offset points", fontsize=9,
                arrowprops={"arrowstyle": "-", "color": "#777777", "lw": 0.6})
ax.set(xlabel="Claude-derived task exposure (0 to 1)", ylabel="Felten et al. AIOE",
       xlim=(0, 1), ylim=(min(y) - 0.45, max(y) + 0.35))
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(labelsize=9)
output = ROOT / "results/reports/exposure_vs_aioe.png"
output.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output, dpi=200, facecolor="white")
plt.close(fig)
print(f"Saved {output}")
