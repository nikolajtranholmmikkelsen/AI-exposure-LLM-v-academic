"""Compare Claude Fable activity judgments with Felten et al. AIOE and explore a hybrid.

Leaves the original model (01_task_exposure.py, results/task/) untouched.
All outputs go to results/hybrid/.

Two integrations of the published AIOE data (Felten, Raj & Seamans 2021):

A. Occupation-level comparison/ensemble
   Merge our Claude-derived task exposure with their AIOE and Language-Modeling AIOE
   at 6-digit SOC; report correlations, rank gaps, and a z-score ensemble.

B. Hybrid IWA layer
   Their Appendix E ability-level exposure (crowd-survey derived, 52 abilities)
   is mapped onto the 41 GWAs through O*NET's Abilities-to-Work-Activities
   crosswalk (mean over abilities linked to each GWA), linearly rescaled to the
   mean/sd of the Claude rubric's GWA-level means (clipped to [0,1]), and blended with
   the rubric at the IWA level:

       hybrid_iwa = ALPHA * rubric_iwa + (1 - ALPHA) * aioe_gwa(parent)

   The blended scores then run through the same task -> occupation pipeline
   as the original model.

Outputs (results/hybrid/):
  occupation_exposure_hybrid.csv - hybrid occupation scores + original + delta
  comparison_occupation.csv      - our score, AIOE, LM-AIOE, z-scores, ranks (683 SOCs)
  iwa_scores_hybrid.csv          - rubric, AIOE-channel, and blended IWA scores
"""

from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "onet"
AIOE = ROOT / "data" / "felten"
OUT = ROOT / "results" / "hybrid"
OUT.mkdir(parents=True, exist_ok=True)

ALPHA = 0.5  # weight on the Claude judgment channel vs the AIOE ability channel

# --- A. Occupation-level comparison -----------------------------------------
ours = pd.read_csv(ROOT / "results" / "task" / "occupation_exposure.csv")
ours["soc6"] = ours["O*NET-SOC Code"].str[:7]
ours6 = ours.groupby("soc6").agg(
    task_exposure=("exposure", "mean"), title=("Title", "first")
).reset_index()

appx = pd.ExcelFile(AIOE / "AIOE_DataAppendix.xlsx")
aioe = appx.parse("Appendix A").rename(columns={"SOC Code": "soc6"})
lm = pd.ExcelFile(AIOE / "Language Modeling AIOE and AIIE.xlsx").parse("LM AIOE").rename(
    columns={"SOC Code": "soc6", "Language Modeling AIOE": "lm_aioe"}
)[["soc6", "lm_aioe"]]

comp = ours6.merge(aioe[["soc6", "AIOE"]], on="soc6").merge(lm, on="soc6", how="left")
comp["task_z"] = (comp.task_exposure - comp.task_exposure.mean()) / comp.task_exposure.std()
comp["aioe_z"] = (comp.AIOE - comp.AIOE.mean()) / comp.AIOE.std()
comp["ensemble_z"] = (comp.task_z + comp.aioe_z) / 2
comp["task_rank"] = comp.task_exposure.rank(ascending=False).astype(int)
comp["aioe_rank"] = comp.AIOE.rank(ascending=False).astype(int)
comp["rank_gap"] = comp.task_rank - comp.aioe_rank  # + = ability lens ranks it higher
comp = comp.sort_values("ensemble_z", ascending=False)
comp.round(4).to_csv(OUT / "comparison_occupation.csv", index=False)

r_p, _ = pearsonr(comp.task_exposure, comp.AIOE)
r_s, _ = spearmanr(comp.task_exposure, comp.AIOE)
r_lm = spearmanr(comp.dropna(subset=["lm_aioe"]).task_exposure,
                 comp.dropna(subset=["lm_aioe"]).lm_aioe).statistic
print(f"[A] matched SOCs: {len(comp)} | task~AIOE pearson={r_p:.3f} spearman={r_s:.3f} "
      f"| task~LM-AIOE spearman={r_lm:.3f}")

# --- B. AIOE ability channel -> GWA -----------------------------------------
appE = appx.parse("Appendix E").rename(
    columns={"O*NET Abilities": "ability", "Ability-Level AI Exposure": "abil_exp"}
)
appE["ability"] = appE["ability"].str.strip().replace(
    {"Visual Color Determination": "Visual Color Discrimination"}  # typo in appendix
)
a2wa = pd.read_excel(DB / "Abilities to Work Activities.xlsx")
a2wa = a2wa.merge(appE, left_on="Abilities Element Name", right_on="ability", how="inner")
gwa_aioe = a2wa.groupby("Work Activities Element ID")["abil_exp"].mean().rename("gwa_aioe_raw")

rubric = pd.read_csv(ROOT / "data" / "rubric" / "iwa_exposure_scores.csv")
xwalk = pd.read_excel(DB / "GWAs to IWAs to DWAs.xlsx")
iwa = (
    xwalk[["GWA Element ID", "GWA Element Name", "IWA Element ID"]]
    .drop_duplicates("IWA Element ID")
    .merge(rubric, left_on="IWA Element ID", right_on="iwa_id")
)
assert len(iwa) == 332

# rescale the AIOE channel to the rubric's GWA-mean distribution, clip to [0,1]
gwa_rubric_mean = iwa.groupby("GWA Element ID")["exposure"].mean()
g = pd.concat([gwa_rubric_mean.rename("rubric_mean"), gwa_aioe], axis=1)
assert g.notna().all().all(), "GWA missing from abilities crosswalk or rubric"
g["gwa_aioe"] = (
    (g.gwa_aioe_raw - g.gwa_aioe_raw.mean()) / g.gwa_aioe_raw.std()
    * g.rubric_mean.std() + g.rubric_mean.mean()
).clip(0, 1)

iwa = iwa.merge(g[["gwa_aioe"]], left_on="GWA Element ID", right_index=True)
iwa["hybrid"] = ALPHA * iwa["exposure"] + (1 - ALPHA) * iwa["gwa_aioe"]
iwa[["iwa_id", "GWA Element Name", "exposure", "gwa_aioe", "hybrid", "channel"]].round(4).to_csv(
    OUT / "iwa_scores_hybrid.csv", index=False
)
print(f"[B] GWA AIOE channel: corr with rubric GWA means = "
      f"{g.rubric_mean.corr(g.gwa_aioe):.3f}")

# --- C. Re-run the task -> occupation pipeline with hybrid scores -----------
dwa_scores = xwalk.merge(
    iwa[["iwa_id", "hybrid", "channel"]], left_on="IWA Element ID", right_on="iwa_id"
)[["DWA Element ID", "hybrid", "channel"]]

t2d = pd.read_excel(DB / "Tasks to DWAs.xlsx")
task_dwa = t2d.merge(dwa_scores, on="DWA Element ID", how="left")
assert task_dwa["hybrid"].notna().all()
task_exp = task_dwa.groupby(["O*NET-SOC Code", "Task ID"]).agg(
    task_exposure=("hybrid", "mean")
).reset_index()

tasks = pd.read_excel(DB / "Task Statements.xlsx")[
    ["O*NET-SOC Code", "Title", "Task ID", "Task Type"]
]
task_exp = tasks.merge(task_exp, on=["O*NET-SOC Code", "Task ID"], how="inner")

tr = pd.read_excel(DB / "Task Ratings.xlsx")
for sid, col in [("IM", "importance"), ("RT", "relevance")]:
    sub = tr[tr["Scale ID"] == sid][["O*NET-SOC Code", "Task ID", "Data Value"]]
    task_exp = task_exp.merge(
        sub.rename(columns={"Data Value": col}), on=["O*NET-SOC Code", "Task ID"], how="left"
    )
task_exp["importance"] = task_exp["importance"].fillna(3.0)
fallback_rt = task_exp["Task Type"].map({"Core": 100.0, "Supplemental": 50.0}).fillna(75.0)
task_exp["relevance"] = task_exp["relevance"].fillna(fallback_rt)
task_exp["weight"] = task_exp["importance"] * task_exp["relevance"] / 100.0

occ_h = (
    task_exp.assign(ws=task_exp.weight * task_exp.task_exposure)
    .groupby(["O*NET-SOC Code", "Title"])
    .agg(hybrid_exposure=("ws", "sum"), wsum=("weight", "sum"))
    .reset_index()
)
occ_h["hybrid_exposure"] = occ_h.hybrid_exposure / occ_h.wsum
occ_h = occ_h.drop(columns="wsum")
occ_h = occ_h.merge(
    ours[["O*NET-SOC Code", "exposure"]].rename(columns={"exposure": "original_exposure"}),
    on="O*NET-SOC Code",
)
occ_h["delta"] = occ_h.hybrid_exposure - occ_h.original_exposure
occ_h["hybrid_pctile"] = occ_h.hybrid_exposure.rank(pct=True).round(3)
occ_h["original_pctile"] = occ_h.original_exposure.rank(pct=True).round(3)
occ_h = occ_h.sort_values("hybrid_exposure", ascending=False)
occ_h.round(4).to_csv(OUT / "occupation_exposure_hybrid.csv", index=False)

print(f"[C] occupations: {len(occ_h)} | hybrid mean={occ_h.hybrid_exposure.mean():.3f} "
      f"sd={occ_h.hybrid_exposure.std():.3f} | corr(original,hybrid)="
      f"{occ_h.original_exposure.corr(occ_h.hybrid_exposure):.3f}")
print("\nBiggest movers up (hybrid vs original percentile):")
mv = occ_h.assign(pmove=occ_h.hybrid_pctile - occ_h.original_pctile)
print(mv.nlargest(8, "pmove")[["Title", "original_exposure", "hybrid_exposure", "pmove"]]
      .to_string(index=False))
print("\nBiggest movers down:")
print(mv.nsmallest(8, "pmove")[["Title", "original_exposure", "hybrid_exposure", "pmove"]]
      .to_string(index=False))
