# Claude Fable elicitation: instruction and rubric

I did not save the exact prompt text. I queried Claude Fable around July 23rd 2026. I asked it to classify each of the 332 O*NET Intermediate Work Activities against the rubric below, assessing the share of an activity that AI could perform or substantially assist with mid-2026 language, multimodal, and software-agent capabilities.

| Score | Rubric interpretation |
| --- | --- |
| 0.90–1.00 | Near end-to-end capability under the rubric's assumptions |
| 0.70–0.85 | Most work can be assisted or performed, with human review |
| 0.45–0.65 | Substantial assistance, with human execution central |
| 0.15–0.40 | Limited assistance, often sensing or diagnosis |
| 0.00–0.10 | Little exposure, typically embodied or manual activity |

The CSV also contains activity channels: INFO (information), ANLY (analysis), CRTV (creative), TECH (technical), SOCL (social), MGMT (management), CARE (care), PHYS (physical), or MACH (machinery).

The scores in [iwa_exposure_scores.csv](iwa_exposure_scores.csv) are the model's responses. I did not record sampling settings or do repeated runs.
