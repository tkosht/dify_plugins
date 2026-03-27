# REV-01 Recall Analysis (2026-03-27)

## Scope
- Candidate change: [AGENTS.md](/home/devuser/workspace/AGENTS.md) review-specific bullet added in commit `5de1b5b` (`docs: tighten review finding specificity`)
- Baseline snapshot: [results_full_2026-03-27](/home/devuser/workspace/docs/ai-agent-reviews/agents_branch_eval_2026-03-21/results_full_2026-03-27)
- Rerun snapshot: live [results](/home/devuser/workspace/docs/ai-agent-reviews/agents_branch_eval_2026-03-21/results)

## Aggregate Effect
- Before rerun, the full snapshot reported `non_inferior: false` because `REV-01` recall was the dominant loss for `arm_beta`.
- After rerunning `REV-01` with the review-specific AGENTS rule, live summary moved to `non_inferior: true` and `strictly_better: true`.
- Parent summary delta:
  - `arm_alpha mean_overall`: `4.669 -> 4.622`
  - `arm_beta mean_overall`: `4.735 -> 4.822`
  - `arm_alpha review_recall`: `0.467 -> 0.267`
  - `arm_beta review_recall`: `0.133 -> 0.533`
- Task median delta:
  - `REV-01 arm_alpha`: `4.075 -> 3.725`
  - `REV-01 arm_beta`: `3.2 -> 4.075`

## Per-Run Candidate Audit
| run | before | after | note |
| --- | --- | --- | --- |
| `arm_beta r1` | `0/3`, overall `3.2` | `2/3`, overall `4.075` | `None` contract regression and empty-select builder regression were split into separate findings with exact symbol/test wording. |
| `arm_beta r2` | `0/3`, overall `3.2` | `1/3`, overall `3.725` | The rerun explicitly named the contract failure, but still did not cleanly separate the request-builder regression. |
| `arm_beta r3` | `0/3`, overall `3.2` | `0/3`, overall `3.2` | Still misses all evaluator signals. The output stays semantically close to the contract issue but does not emit exact signal phrases. |
| `arm_beta r4` | `1/3`, overall `3.725` | `2/3`, overall `4.075` | The rerun now names both the `None` contract regression and the empty-select builder regression. |
| `arm_beta r5` | `1/3`, overall `3.725` | `3/3`, overall `4.6` | Full hit. The rerun explicitly names the resolver contract plus both request-builder entrypoints. |

## What Changed
- The new AGENTS rule pushed review outputs to separate distinct findings instead of collapsing multiple regressions into one paragraph.
- The biggest gain came from naming the affected contract and touched symbols directly:
  - test contract names such as `test_none_input_returns_none`
  - request-builder symbols such as `build_get_item_request()` and `build_list_items_request()`
- File references were already good before the rerun and remained good after it.
- Severity labels were still absent on both arms, so severity was not the differentiator here.

## Remaining Weakness
- `arm_beta r3` still scored `0/3`.
- This remaining miss looks lexical rather than purely semantic: the review still identified the contract inconsistency, but it did not surface the exact symbol/test names that the scorer expects.
- Because of that, the evaluator is still somewhat brittle, even though the AGENTS change materially improved the candidate.

## Conclusion
- The review-specific AGENTS bullet produced a real improvement in `REV-01`, not just formatting churn.
- That improvement was large enough to flip the live 60-run aggregate from a failed non-inferiority result to `strictly_better: true`.
- The remaining gap is concentrated in one candidate run and appears to be about naming precision, not broad review failure.
