# Data sources

I preserve source files without modification and save derived tables in `../results/`.

| Folder | Source and role |
| --- | --- |
| `onet/` | O*NET 30.3, May 2026. I keep the six required workbooks and Read Me at the top level, and the remainder of the O*NET 30.3 release in `onet/unused/` for possible later work. [Release archive](https://www.onetcenter.org/db_releases.html), [30.3 dictionary](https://www.onetcenter.org/dictionary/30.3/excel/). |
| `felten/` | Local snapshot of [AIOE-Data/AIOE](https://github.com/AIOE-Data/AIOE), including its original README. I downloaded this snapshot in early July 2026. |
| `rubric/` | `iwa_exposure_scores.csv`: saved judgments elicited from Claude Fable for 332 unique IWA identifiers, with exposure scores and channel labels. I document the elicitation in [PROMPT.md](rubric/PROMPT.md). |

## Claude judgments

I asked Claude Fable to classify work activities using the exposure rubric. [PROMPT.md](rubric/PROMPT.md) records the model, approximate query date, and scoring approach. The CSV contains the model's responses, which I use to reproduce the aggregation and comparison.

## Inputs used by the scripts

O*NET: `GWAs to IWAs to DWAs.xlsx`, `Tasks to DWAs.xlsx`, `Task Statements.xlsx`, `Task Ratings.xlsx`, `Abilities to Work Activities.xlsx`, and `Job Zones.xlsx`. I keep the remaining workbooks in `onet/unused/` for possible later work.

Felten: `AIOE_DataAppendix.xlsx` (Appendix A for occupation scores; Appendix E for ability scores) and `Language Modeling AIOE and AIIE.xlsx` (LM AIOE sheet). The image-generation workbook is retained but not used. Local `Input/`, `Generative AI/`, and the paper PDF are reference materials, excluded from Git and unnecessary for the Python analysis. Upstream Stata scripts remain with their source snapshot; I use the Python scripts for estimation.

If restoring inputs, download O*NET version **30.3**, not the latest release, and place only the six required workbooks listed above and `Read Me.txt` directly in `onet/`. Put all remaining workbooks in `onet/unused/`. Obtain the two required AIOE workbooks from the authors' repository and place them directly in `felten/`. A later upstream revision may change the results, so compare against the July 2026 snapshot if estimates differ.

## Attribution and redistribution

O*NET data are supplied under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); see the [database license](https://www.onetcenter.org/license_db.html) and the attribution in the project README. The original O*NET Read Me is retained.

The code and rubric are [MIT licensed](../LICENSE). I include the Felten, Raj and Seamans workbooks as downloaded from the authors' public repository, which requests citation to Felten, Raj, and Seamans (2021). They remain under the authors' terms.
