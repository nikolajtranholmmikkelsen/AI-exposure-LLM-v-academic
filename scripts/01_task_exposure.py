"""Claude Fable judgments aggregated to occupational AI exposure using O*NET 30.3.

Pipeline:
  1. Load saved Claude Fable AI exposure judgments for the 332 Intermediate Work
     Activities (IWAs) from iwa_exposure_scores.csv (0 = no exposure,
     1 = current AI can perform the activity end-to-end).
  2. Map every Detailed Work Activity (DWA) to its parent IWA score.
  3. Task exposure = mean score over the DWAs linked to the task
     (Tasks to DWAs covers all 18,796 task statements).
  4. Occupation exposure = weighted mean of task exposures, weighted by
     Importance (IM, 1-5) x Relevance (RT, 0-100) from Task Ratings.
     Tasks without ratings fall back to IM=3, RT=100 (Core) / RT=50 (Supplemental).

Outputs (written to results/task/):
  occupation_exposure.csv  - one row per occupation: exposure, high/low task shares,
                             channel shares of task weight
  task_exposure.csv        - one row per task: score, weight, dominant channel
  gwa_summary.csv          - mean IWA score per Generalized Work Activity
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "onet"
OUT = ROOT / "results" / "task"
OUT.mkdir(parents=True, exist_ok=True)

HIGH_EXPOSURE = 0.70  # task score at/above which a task counts as "high exposure"
LOW_EXPOSURE = 0.30

# --- 1. IWA scores ---------------------------------------------------------
scores = pd.read_csv(ROOT / "data" / "rubric" / "iwa_exposure_scores.csv")
xwalk = pd.read_excel(DB / "GWAs to IWAs to DWAs.xlsx")

iwa_ids = set(xwalk["IWA Element ID"].unique())
score_ids = set(scores["iwa_id"])
missing = iwa_ids - score_ids
extra = score_ids - iwa_ids
if missing or extra:
    raise SystemExit(f"IWA score file mismatch. Missing: {sorted(missing)} Extra: {sorted(extra)}")
assert scores["iwa_id"].is_unique
assert scores["exposure"].between(0, 1).all()

dwa_scores = xwalk.merge(scores, left_on="IWA Element ID", right_on="iwa_id")
dwa_scores = dwa_scores[["DWA Element ID", "GWA Element Name", "exposure", "channel"]]
assert dwa_scores["DWA Element ID"].is_unique, "DWA maps to more than one IWA"

# --- 2. Task exposure ------------------------------------------------------
t2d = pd.read_excel(DB / "Tasks to DWAs.xlsx")
task_dwa = t2d.merge(dwa_scores, on="DWA Element ID", how="left")
assert task_dwa["exposure"].notna().all()

task_exp = task_dwa.groupby(["O*NET-SOC Code", "Task ID"]).agg(
    task_exposure=("exposure", "mean"),
    n_dwas=("exposure", "size"),
).reset_index()

tasks = pd.read_excel(DB / "Task Statements.xlsx")[
    ["O*NET-SOC Code", "Title", "Task ID", "Task", "Task Type"]
]
task_exp = tasks.merge(task_exp, on=["O*NET-SOC Code", "Task ID"], how="left", validate="one_to_one")
assert task_exp["task_exposure"].notna().all(), "Unmapped task"

# Most frequent linked activity channel; alphabetical order breaks ties.
channel_counts = task_dwa.groupby(["O*NET-SOC Code", "Task ID", "channel"]).size().rename("count").reset_index()
dominant = channel_counts.sort_values(
    ["O*NET-SOC Code", "Task ID", "count", "channel"], ascending=[True, True, False, True]
).drop_duplicates(["O*NET-SOC Code", "Task ID"])
task_exp = task_exp.merge(dominant[["O*NET-SOC Code", "Task ID", "channel"]],
                          on=["O*NET-SOC Code", "Task ID"], validate="one_to_one")

# --- 3. Task weights (Importance x Relevance) ------------------------------
tr = pd.read_excel(DB / "Task Ratings.xlsx")
im = tr[tr["Scale ID"] == "IM"][["O*NET-SOC Code", "Task ID", "Data Value"]].rename(
    columns={"Data Value": "importance"}
)
rt = tr[tr["Scale ID"] == "RT"][["O*NET-SOC Code", "Task ID", "Data Value"]].rename(
    columns={"Data Value": "relevance"}
)
task_exp = task_exp.merge(im, on=["O*NET-SOC Code", "Task ID"], how="left")
task_exp = task_exp.merge(rt, on=["O*NET-SOC Code", "Task ID"], how="left")

task_exp["importance"] = task_exp["importance"].fillna(3.0)
fallback_rt = task_exp["Task Type"].map({"Core": 100.0, "Supplemental": 50.0}).fillna(75.0)
task_exp["relevance"] = task_exp["relevance"].fillna(fallback_rt)
task_exp["weight"] = task_exp["importance"] * task_exp["relevance"] / 100.0

task_exp = task_exp[["O*NET-SOC Code", "Title", "Task ID", "Task", "Task Type", "task_exposure", "n_dwas", "channel", "importance", "relevance", "weight"]]

# --- 4. Occupation aggregation ---------------------------------------------
keys = ["O*NET-SOC Code", "Title"]
task_exp["weighted_exposure"] = task_exp["weight"] * task_exp["task_exposure"]
task_exp["high_weight"] = task_exp["weight"].where(task_exp.task_exposure >= HIGH_EXPOSURE, 0)
task_exp["low_weight"] = task_exp["weight"].where(task_exp.task_exposure <= LOW_EXPOSURE, 0)

occ = task_exp.groupby(keys).agg(
    exposure=("weighted_exposure", "sum"),
    n_tasks=("Task ID", "size"),
    share_high=("high_weight", "sum"),
    share_low=("low_weight", "sum"),
    total_weight=("weight", "sum"),
)
assert occ["total_weight"].gt(0).all()
for column in ["exposure", "share_high", "share_low"]:
    occ[column] = occ[column] / occ["total_weight"]

channel_weights = task_exp.groupby(keys + ["channel"])["weight"].sum().unstack(fill_value=0)
channel_shares = channel_weights.div(occ["total_weight"], axis=0).add_prefix("wshare_")
occ = occ.drop(columns="total_weight").join(channel_shares).reset_index()
task_exp = task_exp.drop(columns=["weighted_exposure", "high_weight", "low_weight"])
occ["exposure_pctile"] = occ["exposure"].rank(pct=True).round(3)
occ = occ.sort_values("exposure", ascending=False)

# --- 5. GWA summary ---------------------------------------------------------
gwa = (
    xwalk.merge(scores, left_on="IWA Element ID", right_on="iwa_id")
    .drop_duplicates("IWA Element ID")
    .groupby("GWA Element Name")["exposure"]
    .agg(["mean", "min", "max", "count"])
    .rename(columns={"count": "n_iwas"})
    .sort_values("mean", ascending=False)
    .reset_index()
)

occ.round(4).to_csv(OUT / "occupation_exposure.csv", index=False)
task_exp.round(4).to_csv(OUT / "task_exposure.csv", index=False)
gwa.round(4).to_csv(OUT / "gwa_summary.csv", index=False)

print(f"Occupations scored: {len(occ)}  |  Tasks scored: {len(task_exp)}")
print(f"Exposure  mean={occ['exposure'].mean():.3f}  sd={occ['exposure'].std():.3f}  "
      f"min={occ['exposure'].min():.3f}  max={occ['exposure'].max():.3f}")
print("\nTop 15 most exposed:")
print(occ.head(15)[["O*NET-SOC Code", "Title", "exposure", "share_high"]].to_string(index=False))
print("\nBottom 15 least exposed:")
print(occ.tail(15)[["O*NET-SOC Code", "Title", "exposure", "share_high"]].to_string(index=False))
