# Qwen3-1.7B paired-run recovery, without fresh model calls

Original evaluation: GitHub Actions run **42342242561**, released from main
commit dbd7636a936f8090a11031debf685dea40a1d91c.

Both pinned Qwen models completed genuine Inspect Evals prompts. The
custom post-processing audit failed because it selected the *first
12 recorded answers* from the 24-question baseline rather than
matching the **12 actual candidate sample identifiers**. Inspect
results can be recorded in completion order, not dataset order.

Original official files:
https://github.com/chadkhalil21-svg/Plenum-Scientific-Intelligence/actions/runs/42342242561

The recovery workflow never invokes a model. It downloads the
original four evaluation files, checks their separately reviewed SHA-256
digests, verifies the original frozen 0.6B benchmark archive, reads
official Inspect scores, compares source questions and scoring targets,
and pairs only exact IDs. No GPU, model provider API, training, shell
execution of generated code or deployment.

Direct source-file reconciliation before the automated audit:

| Same 12 original questions | Qwen3-0.6B | Qwen3-1.7B |
|---|---:|---:|
| ARC Challenge | 8/12 | 10/12 |
| GSM8K | 4/12 | 1/12 |
| HellaSwag | 5/12 | 7/12 |
| MMLU zero-shot | 1/12 | 3/12 |
| Total | 18/48 | 21/48 |

Eight errors were corrected, five correct answers regressed. These
original-score totals await automated independent audit and permanent
append-only archive. Historic failed audit logs remain intact.

The results are tiny and public and could have appeared in pretraining:
a three-question gain does not establish reliable improvement, AGI,
new knowledge, or learning. The poorer mathematics result cautions
against automatically promoting the larger model.

The recovery archive uses the ORIGINAL run ID 42342242561 and source
release SHA for scientific provenance, with the recovery code commit
identified separately. No new inference run is disguised as original.
