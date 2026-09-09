 # AI exposure: early research measures versus modern LLM judgments

This project asks what happens when we assess occupational AI exposure by simply asking a modern large language model, rather than constructing a measure through an earlier research framework. It compares judgments elicited from **Claude Fable** with the AI Occupational Exposure (AIOE) measure of Felten, Raj, and Seamans (2021), developed before the current wave of general-purpose LLMs.

Claude Fable was asked to judge the AI exposure of each of 332 O*NET Intermediate Work Activities. These saved judgments are the rubric input; they are not human analyst ratings. O*NET crosswalks and task weights translate them into exposure scores for 923 occupations. The central comparison is between those LLM-derived scores and Felten's earlier researcher-designed measure, which links AI applications to human abilities using survey-based mappings. Published language-modeling AIOE provides an additional benchmark; a 50/50 hybrid is a secondary exploration of combining the two approaches.

Both approaches address the same broad question—how exposed is an occupation to AI?—but operationalize it differently. Claude judges work activities, whereas Felten's measure works through abilities. The comparison therefore combines differences in judgment source, measurement design, and capability vintage. It does not isolate a pure LLM-versus-human effect or estimate AI's causal labor-market effects.

## Main findings

The Claude-derived task model covers 18,796 tasks. Mean occupational exposure is **0.485** on a 0–1 scale, with a standard deviation of **0.208**. These statistics weight occupations equally, not by employment.

| Result | Estimate | Interpretation |
| --- | ---: | --- |
| Claude-derived–AIOE rank correlation | 0.885 | Strong agreement across 683 matched six-digit SOC occupations |
| Claude-derived–language-modeling AIOE rank correlation | 0.879 | A similar broad ordering under the language-modeling benchmark |
| Claude-derived–AIOE Pearson correlation | 0.889 | Strong linear association within the matched sample |
| Hybrid mean exposure | 0.472 | The 50/50 blend slightly lowers average scores |
| Hybrid standard deviation | 0.179 | The blend compresses the distribution relative to the task model |
| Task–hybrid Pearson correlation | 0.981 | Broad ordering is stable, with meaningful changes for some occupations |

Information-processing occupations rank highly: medical transcriptionists score 0.889, credit analysts 0.843, and bookkeeping clerks 0.842. Physical occupations score much lower: roofers score 0.083, stonemasons 0.051, and dishwashers 0.050.

Average exposure rises from Job Zone 2 (0.324) through Zone 3 (0.470) to Zone 4 (0.656), then falls in Zone 5 (0.601). Job Zones describe occupational preparation requirements. The pattern is consistent with substantial exposure in skilled information work and lower exposure in some highly trained hands-on professions; it does not establish education as a cause of exposure.

The hybrid raises oral and maxillofacial surgeons from 0.194 to 0.398, an increase of about 21.2 percentile points. This illustrates how an ability-based view can assign greater exposure to occupations whose execution still involves substantial physical work. Geographers move down about 15.6 percentile points.

**Significance.** Directly eliciting judgments from Claude Fable produces occupational rankings that broadly resemble those from an earlier, researcher-designed exposure framework: the main rank correlation is 0.885. This suggests that an LLM can reproduce much of that occupational ordering through a comparatively simple elicitation approach. It does not show that Claude is more accurate, or that it independently discovered the same relationships. Disagreements may reflect newer capabilities, activity-versus-ability measurement, or model judgments; this design cannot separate those explanations. Both measures use O*NET, and the available record cannot rule out Claude having encountered the published research in training. No observed adoption, productivity, wage, or employment outcomes are used to test predictive accuracy.

## Methodology

### 1. Elicit Claude Fable judgments of work activities

The project owner identifies the input rubric as the result of asking Claude Fable for its judgment of each of O*NET's 332 Intermediate Work Activities (IWAs). Scores represent the model's assessments of the share of an activity that AI could perform or substantially assist, including language, multimodal, and software-agent capabilities. The existing scoring description frames capability as mid-2026; the exact elicitation date is not recorded in the retained files.

| Score | Rubric interpretation |
| --- | --- |
| 0.90–1.00 | Near end-to-end capability under the rubric's assumptions |
| 0.70–0.85 | Most work can be assisted or performed, with human review |
| 0.45–0.65 | Substantial assistance, with human execution central |
| 0.15–0.40 | Limited assistance, often sensing or diagnosis |
| 0.00–0.10 | Little exposure, typically embodied or manual activity |

These are LLM judgments, not scores estimated from observed AI performance. Claude Fable is the model name supplied by the project owner; an exact version or API identifier, original prompt, sampling settings, raw responses, and repeated runs are not retained here. The table describes the saved scoring scale, not a verified transcript of the prompt. The saved judgments are available in full in [data/rubric/iwa_exposure_scores.csv](data/rubric/iwa_exposure_scores.csv).

### 2. Map activities to tasks and occupations

Each of 2,087 Detailed Work Activities (DWAs) inherits its parent IWA score. A task's score is the arithmetic mean across its linked DWAs. All 18,796 task statements are mapped.

For occupation `o`, exposure is:

```text
task_score(t) = mean(score of each DWA linked to t)
weight(t) = importance(t) × relevance(t) / 100
exposure(o) = sum(weight(t) × task_score(t)) / sum(weight(t))
```

Importance uses O*NET's 1–5 scale and relevance its 0–100 scale. Missing importance defaults to 3. Missing relevance defaults to 100 for Core tasks, 50 for Supplemental tasks, and 75 for other task types. These defaults are assumptions, not imputations estimated from data.

The model also reports the share of task weight with exposure at least 0.70 or at most 0.30. Channel shares describe task weight assigned to each task's most frequent linked DWA channel; alphabetical ordering resolves ties. They are not shares of exposure or worker time.

### 3. Compare LLM-derived exposure with published research measures

O*NET occupation codes are collapsed to six-digit SOC codes by taking the unweighted mean across detailed occupations. An exact code match with Felten's Appendix A yields 683 occupations. The comparison also adds the published language-modeling AIOE measure. This is a matched subset, not the full 923-occupation sample, and no historical SOC crosswalk is applied.

Pearson correlations compare score levels; Spearman correlations compare rankings. An additional `ensemble_z` averages task and AIOE z-scores standardized within the matched sample. This occupation-level ensemble is distinct from the hybrid below. Rank 1 indicates greatest exposure; exported comparison ranks truncate average ranks for ties, preserving the original convention. Correlations use the underlying scores.

### 4. Explore a hybrid of LLM judgments and the research measure

Felten's Appendix E supplies exposure for 52 abilities. O*NET's Abilities to Work Activities crosswalk maps those abilities to 41 Generalized Work Activities (GWAs). Each GWA receives the mean of its linked ability scores. The script harmonizes the Appendix E label “Visual Color Determination” to O*NET's “Visual Color Discrimination.”

The GWA ability scores are linearly rescaled to match the mean and sample standard deviation of the rubric's GWA means, then clipped to [0, 1]. Each IWA receives:

```text
hybrid_iwa = 0.5 × rubric_iwa + 0.5 × rescaled_ability_score(parent_GWA)
```

The same task mapping and importance–relevance aggregation produce hybrid occupational scores. The hybrid is a secondary analysis, not the primary test of agreement between Claude and Felten. The 50/50 weight is a modeling choice, not an estimated optimum. Rescaling aligns numerical scales; it does not calibrate the result as an automation probability.

## Interpretation and limitations

A score of 0.8 is an exposure index under the rubric, not an 80% probability of replacement or a measured 80% reduction in labor hours. The analysis does not distinguish augmentation from substitution, model adoption costs, or estimate net employment effects.

All DWAs within an IWA receive the same score, losing differences in context and difficulty. Task ratings can lag changes in work. Exact SOC matching excludes unmatched occupations and can miss classification changes. The hybrid mixes different capability vintages and partly reflects its imposed scaling. The saved Claude judgments come from an elicitation process whose prompt and settings are not archived. There are no repeated-run stability estimates, comparisons across LLMs, uncertainty intervals, or sensitivity analyses over prompts, activity scores, and blend weights. Archiving the elicitation and testing its reproducibility are central next steps before stronger claims about LLM-based measurement.

## Project structure

```text
data/
  onet/                  O*NET 30.3 source workbooks
  felten/                Published AIOE source material
  rubric/                Saved Claude Fable activity judgments
scripts/
  01_task_exposure.py     Activity-to-task-to-occupation estimates
  02_hybrid_exposure.py   Published-measure comparison and hybrid estimates
  03_results.py          Summary statistics and HTML reports
results/
  task/                  Task model tables and Job Zone summary
  hybrid/                Hybrid scores and matched comparison
  reports/               Two self-contained HTML reports
  summary.csv            Headline statistics
```

See [data/README.md](data/README.md) for source provenance, required inputs, and attribution.

## Reproduce the results

Tested with Python 3.14.6 and the package versions in `requirements.txt`. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/01_task_exposure.py
python scripts/02_hybrid_exposure.py
python scripts/03_results.py
```

On Windows, activate with `.venv\Scripts\activate`. Run scripts in numerical order. Paths are resolved from the script locations, so execution does not otherwise depend on the working directory. The scripts read local inputs and overwrite their corresponding results. They reproduce the downstream analysis from saved Claude Fable judgments; they do not call Claude or reproduce the original elicitation. No API keys or network calls are needed for the analysis. CSV estimates are exported to four decimal places; summary statistics are calculated from those saved estimates and may differ slightly from calculations using full precision.

## Results files

| File | Contents |
| --- | --- |
| [Task occupation scores](results/task/occupation_exposure.csv) | Exposure, task counts, high/low shares, channel shares, percentile |
| [Task scores](results/task/task_exposure.csv) | Task text, exposure, DWA count, channel, importance, relevance, weight |
| [GWA summary](results/task/gwa_summary.csv) | Mean, minimum, maximum, and count of Claude IWA scores within each GWA |
| [Job Zone summary](results/task/job_zone_summary.csv) | Occupation counts and unweighted mean exposure by preparation level |
| [Hybrid occupation scores](results/hybrid/occupation_exposure_hybrid.csv) | Original and hybrid exposure, difference, and percentiles |
| [Matched comparison](results/hybrid/comparison_occupation.csv) | Task, AIOE, LM-AIOE, standardized ensemble, and ranks |
| [Hybrid activity scores](results/hybrid/iwa_scores_hybrid.csv) | Claude score, rescaled ability channel, and blended score |
| [Summary statistics](results/summary.csv) | Coverage, means, standard deviations, and correlations |

The [task report](results/reports/ai-exposure-report.html) and [comparison report](results/reports/exposure-comparison.html) can be downloaded and opened in a browser. GitHub's file view displays HTML source. Reports require no external assets.

Exposure and percentile fields use fractions, with higher values indicating greater exposure. `delta` is hybrid minus original exposure; `rank_gap` is task rank minus AIOE rank, so a positive value means AIOE ranks the occupation higher. Channels are INFO (information), ANLY (analysis), CRTV (creative), TECH (technical), SOCL (social), MGMT (management), CARE (care), PHYS (physical), and MACH (machinery).

## Sources and reuse

Felten, E., Raj, M., & Seamans, R. (2021). Occupational, industry, and geographic exposure to artificial intelligence: A novel dataset and its potential uses. *Strategic Management Journal, 42*(12), 2195–2217. [Article](https://doi.org/10.1002/smj.3286) · [Authors' data repository](https://github.com/AIOE-Data/AIOE).

Felten, E., Raj, M., & Seamans, R. (2023). How will Language Modelers like ChatGPT Affect Occupations and Industries? [Working paper](https://arxiv.org/abs/2303.01157).

This project incorporates information from the O*NET 30.3 Database, U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). O*NET® is a trademark of USDOL/ETA. The exposure scores and aggregations are project adaptations; USDOL/ETA has not approved, endorsed, or tested them.

No license has yet been selected for this project's original code and rubric. Third-party materials retain their own terms. The local AIOE snapshot contains no explicit license file; its README requests citation. Confirm redistribution terms before publishing those workbooks or offering reuse rights for derived AIOE outputs. The reference PDF and unused upstream replication folders are retained locally but excluded from Git.
