# Data sources

Source files are preserved without modification. Derived tables belong in `../results/`.

| Folder | Source and role |
| --- | --- |
| `onet/` | O*NET 30.3, May 2026. Original workbook release and its Read Me. [Release archive](https://www.onetcenter.org/db_releases.html), [30.3 dictionary](https://www.onetcenter.org/dictionary/30.3/excel/). |
| `felten/` | Local snapshot of [AIOE-Data/AIOE](https://github.com/AIOE-Data/AIOE), including its original README. Download date and upstream commit were not recorded. |
| `rubric/` | `iwa_exposure_scores.csv`: saved judgments elicited from Claude Fable for 332 unique IWA identifiers, with exposure scores and channel labels. Model provenance was supplied by the project owner. These are LLM-generated assessments, not human analyst ratings. |

## Claude judgment provenance

Claude Fable was asked to judge the AI exposure of each activity. The exact model version/API identifier, elicitation date, prompt, sampling settings, raw responses, and repeated runs are not archived in this folder. The original methodology describes a mid-2026 capability scope; this does not establish the query date. The saved CSV supports reproducing the aggregation and comparison, but not independently reproducing the elicitation. The `rubric` folder name refers to the scoring scale and saved model judgments.

## Inputs used by the scripts

O*NET: `GWAs to IWAs to DWAs.xlsx`, `Tasks to DWAs.xlsx`, `Task Statements.xlsx`, `Task Ratings.xlsx`, `Abilities to Work Activities.xlsx`, and `Job Zones.xlsx`. The remaining workbooks are retained as the complete local source release.

Felten: `AIOE_DataAppendix.xlsx` (Appendix A for occupation scores; Appendix E for ability scores) and `Language Modeling AIOE and AIIE.xlsx` (LM AIOE sheet). The image-generation workbook is retained but not used. Local `Input/`, `Generative AI/`, and the paper PDF are reference materials, excluded from Git and unnecessary for the Python analysis. Upstream Stata scripts remain with their source snapshot; they are not the project's estimation scripts.

If restoring inputs, download O*NET version **30.3**, not the latest release, and extract its workbook contents directly into `onet/`. Obtain the two required AIOE workbooks from the authors' repository and place them directly in `felten/`. An updated upstream file may change the results because the original download did not record a commit identifier.

## Attribution and redistribution

O*NET data are supplied under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); see the [database license](https://www.onetcenter.org/license_db.html) and the attribution in the project README. The original O*NET Read Me is retained.

The AIOE README requests citation to Felten, Raj, and Seamans (2021). No explicit license file is present in this local snapshot. Public availability alone does not establish redistribution permission. Resolve terms for the included AIOE workbooks and derived outputs before public release; the project does not assign them a new license.
