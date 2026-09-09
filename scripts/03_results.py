"""Summarize the saved estimates and rebuild the two browser-readable reports."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
REPORTS = RESULTS / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# 1. Read estimates and occupational preparation levels.
occupations = pd.read_csv(RESULTS / "task" / "occupation_exposure.csv")
tasks = pd.read_csv(RESULTS / "task" / "task_exposure.csv")
comparison = pd.read_csv(RESULTS / "hybrid" / "comparison_occupation.csv")
hybrid = pd.read_csv(RESULTS / "hybrid" / "occupation_exposure_hybrid.csv")
zones = pd.read_excel(ROOT / "data" / "onet" / "Job Zones.xlsx")
zone_summary = occupations.merge(
    zones[["O*NET-SOC Code", "Job Zone"]], on="O*NET-SOC Code", validate="one_to_one"
).groupby("Job Zone").agg(occupations=("exposure", "size"), mean_exposure=("exposure", "mean"))
zone_summary.round(4).to_csv(RESULTS / "task" / "job_zone_summary.csv")

# 2. Compare rankings on the matched sample and distributions on all occupations.
statistics = pd.Series({
    "occupations": len(occupations),
    "tasks": len(tasks),
    "matched_soc6": len(comparison),
    "matched_lm_soc6": comparison.lm_aioe.notna().sum(),
    "task_mean": occupations.exposure.mean(),
    "task_sd": occupations.exposure.std(),
    "hybrid_mean": hybrid.hybrid_exposure.mean(),
    "hybrid_sd": hybrid.hybrid_exposure.std(),
    "task_aioe_pearson": comparison.task_exposure.corr(comparison.AIOE),
    "task_aioe_spearman": comparison.task_exposure.corr(comparison.AIOE, method="spearman"),
    "task_lm_spearman": comparison.task_exposure.corr(comparison.lm_aioe, method="spearman"),
    "task_hybrid_pearson": hybrid.original_exposure.corr(hybrid.hybrid_exposure),
}, name="value")
statistics.round(6).to_csv(RESULTS / "summary.csv", index_label="statistic")
hybrid["percentile_change"] = hybrid.hybrid_pctile - hybrid.original_pctile

# 3. Render compact, self-contained reports directly from the result tables.
style = """<style>
body{font:16px/1.6 system-ui,sans-serif;color:#20252b;max-width:1000px;margin:48px auto;padding:0 24px}
h1,h2{line-height:1.25}h2{margin-top:40px}p{max-width:85ch}a{color:#245d83}
table{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}
th,td{padding:8px 12px;border-bottom:1px solid #ddd;text-align:right}
th:first-child,td:first-child{text-align:left}nav{margin-bottom:32px}
.table{overflow-x:auto}
</style>"""
columns = ["Title", "exposure", "share_high", "share_low"]
move_columns = ["Title", "original_exposure", "hybrid_exposure", "percentile_change"]
reports = [
    ("ai-exposure-report.html", "AI exposure from Claude Fable judgments", [
        ("Most exposed occupations", occupations.nlargest(15, "exposure")[columns]),
        ("Least exposed occupations", occupations.nsmallest(15, "exposure")[columns]),
        ("Exposure by Job Zone", zone_summary.reset_index()),
        ("General work activities", pd.read_csv(RESULTS / "task" / "gwa_summary.csv")),
    ]),
    ("exposure-comparison.html", "Claude Fable judgments versus Felten AIOE", [
        ("Comparison statistics", statistics.to_frame().reset_index(names="statistic")),
        ("Ability measure ranks higher", comparison.nlargest(10, "rank_gap")[["title", "task_rank", "aioe_rank", "rank_gap"]]),
        ("Task measure ranks higher", comparison.nsmallest(10, "rank_gap")[["title", "task_rank", "aioe_rank", "rank_gap"]]),
        ("Largest hybrid percentile increases", hybrid.nlargest(10, "percentile_change")[move_columns]),
        ("Largest hybrid percentile decreases", hybrid.nsmallest(10, "percentile_change")[move_columns]),
    ]),
]
for filename, title, sections in reports:
    html = f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>{style}<body>'
    html += '<nav><a href="ai-exposure-report.html">Claude-derived exposure</a> · <a href="exposure-comparison.html">Comparison</a> · <a href="../../README.md">Research README</a></nav>'
    html += f"<h1>{title}</h1>"
    html += f"<p>O*NET 30.3; {len(occupations):,} occupations and {len(tasks):,} tasks. Activity scores are saved Claude Fable judgments, as identified by the project owner, using the project’s mid-2026 capability framing. Exposure measures capability overlap, not employment loss or observed adoption.</p>"
    html += "<p>Task scores are importance × relevance weighted means on a 0–1 scale. The main comparison asks how modern LLM judgments compare with Felten’s earlier researcher-designed exposure measure. The secondary hybrid blends Claude judgments and rescaled ability exposure equally. Correlations describe agreement on matched occupations, not predictive accuracy or a pure LLM-versus-human effect: the approaches differ in measurement unit and capability vintage. Percentile changes are fractions of the ranking distribution; 0.10 means ten percentile points.</p>"
    html += "<p>The original Claude prompt, exact version, settings, and raw responses are not archived. These reports reproduce analysis from the saved judgments, not the elicitation. Shared O*NET inputs and possible model familiarity with the research mean agreement is not independent validation.</p>"
    for heading, table in sections:
        html += f'<h2>{heading}</h2><div class="table">'
        html += table.round(3).to_html(index=False, border=0, escape=True)
        html += "</div>"
    html += "<p>Generated by scripts/03_results.py. See the research README for assumptions, source attribution, and output definitions.</p></body></html>"
    (REPORTS / filename).write_text(html, encoding="utf-8")

print(statistics.round(6).to_string())
print("\nJob Zone means:\n", zone_summary.round(4).to_string())
