"""Test zero exposure for tasks linked to physical O*NET activity categories."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/robustness"
KEYS = ["O*NET-SOC Code", "Task ID"]
RULES = {
    "narrow": {"4.A.3.a.1", "4.A.3.a.2"},
    "broad": {"4.A.3.a.1", "4.A.3.a.2", "4.A.3.a.3", "4.A.3.a.4"},
}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = pd.read_csv(ROOT / "results/task/task_exposure.csv")
    original = pd.read_csv(ROOT / "results/task/occupation_exposure.csv")
    matched = pd.read_csv(ROOT / "results/hybrid/comparison_occupation.csv")
    hierarchy = pd.read_excel(ROOT / "data/onet/GWAs to IWAs to DWAs.xlsx")
    links = pd.read_excel(ROOT / "data/onet/Tasks to DWAs.xlsx")
    rubric = pd.read_csv(ROOT / "data/rubric/iwa_exposure_scores.csv")
    links = links[KEYS + ["DWA Element ID"]].merge(
        hierarchy, on="DWA Element ID", how="left", validate="many_to_one"
    ).merge(rubric, left_on="IWA Element ID", right_on="iwa_id", how="left", validate="many_to_one")
    assert links[["exposure", "GWA Element ID"]].notna().all().all()
    # Reconstruct full-precision means and weights, avoiding rounding in saved task scores.
    baseline = links.groupby(KEYS).exposure.mean().rename("baseline_exposure")
    tasks = tasks.merge(baseline, on=KEYS, validate="one_to_one")
    tasks["weight"] = tasks.importance * tasks.relevance / 100
    grouped = tasks.groupby("O*NET-SOC Code")
    denominators = grouped.weight.sum()
    occupations = original[["O*NET-SOC Code", "Title", "exposure"]].rename(columns={"exposure": "original"})
    rebuilt = (tasks.assign(ws=tasks.weight * tasks.baseline_exposure)
               .groupby("O*NET-SOC Code").ws.sum() / denominators)
    assert np.allclose(occupations.original, occupations["O*NET-SOC Code"].map(rebuilt).round(4), atol=1e-12, rtol=0)
    stats = []
    for rule, codes in RULES.items():
        links[rule + "_flag"] = links["GWA Element ID"].isin(codes)
        flags = links.groupby(KEYS)[rule + "_flag"].any()
        tasks = tasks.merge(flags, on=KEYS, validate="one_to_one")
        tasks[rule + "_exposure"] = tasks.baseline_exposure.mask(tasks[rule + "_flag"], 0)
        scores = (tasks.assign(ws=tasks.weight * tasks[rule + "_exposure"])
                  .groupby("O*NET-SOC Code").ws.sum() / denominators)
        occupations[rule] = occupations["O*NET-SOC Code"].map(scores).round(4)
        flagged_weight = tasks.weight.where(tasks[rule + "_flag"], 0).groupby(tasks["O*NET-SOC Code"]).sum()
        occupations[rule + "_weight_share"] = occupations["O*NET-SOC Code"].map(flagged_weight / denominators)
        occupations[rule + "_delta"] = occupations[rule] - occupations.original
        stats.append({"variant": rule, "overridden_tasks": int(tasks[rule + "_flag"].sum()),
                      "mean_occupation_weight_share": occupations[rule + "_weight_share"].mean(),
                      "mean_exposure": occupations[rule].mean()})
    occupations["soc6"] = occupations["O*NET-SOC Code"].str[:7]
    adjusted6 = occupations.groupby("soc6")[["narrow", "broad"]].mean().round(4)
    comparison = matched[["soc6", "title", "task_exposure", "AIOE"]].rename(columns={"task_exposure": "original"})
    comparison = comparison.merge(adjusted6, on="soc6", how="left", validate="one_to_one")
    assert len(comparison) == 683 and comparison.notna().all().all()
    stats.insert(0, {"variant": "original", "overridden_tasks": 0,
                     "mean_occupation_weight_share": 0, "mean_exposure": occupations.original.mean()})
    for row in stats:
        series = comparison[row["variant"]]
        row.update(matched_occupations=len(comparison), pearson=series.corr(comparison.AIOE),
                   spearman=series.corr(comparison.AIOE, method="spearman"))
    summary = pd.DataFrame(stats)
    links.to_csv(OUT / "activity_audit.csv", index=False)
    tasks.to_csv(OUT / "task_overrides.csv", index=False)
    occupations.to_csv(OUT / "occupation_exposure.csv", index=False)
    comparison.to_csv(OUT / "comparison_occupation.csv", index=False)
    summary.to_csv(OUT / "summary.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharex=True, sharey=True, layout="constrained")
    for ax, row in zip(axes, stats):
        variant = row["variant"]
        x, y = comparison[variant], comparison.AIOE
        ax.scatter(x, y, s=9, color="#888888", alpha=0.5, linewidths=0)
        slope, intercept = np.polyfit(x, y, 1)
        endpoints = np.array([x.min(), x.max()])
        ax.plot(endpoints, intercept + slope * endpoints, color="#333333", lw=1)
        ax.text(0.04, 0.97, f"{variant.capitalize()}\nSpearman = {row['spearman']:.4f}\nPearson = {row['pearson']:.4f}",
                transform=ax.transAxes, va="top", fontsize=10)
        model = comparison.loc[comparison.title.eq("Models")].iloc[0]
        ax.annotate("Models", (model[variant], model.AIOE), xytext=(15, -22), textcoords="offset points",
                    fontsize=9, arrowprops={"arrowstyle": "-", "lw": 0.6, "color": "#777777"})
        ax.set(xlim=(0, 1), xlabel="Claude-derived task exposure (0 to 1)")
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Felten et al. AIOE")
    fig.savefig(OUT / "physical_override_comparison.png", dpi=200, facecolor="white")
    plt.close(fig)
    print(summary.round(6).to_string(index=False))
    print("\nModels:\n", occupations.loc[occupations.Title.eq("Models")].to_string(index=False))


if __name__ == "__main__":
    run()
