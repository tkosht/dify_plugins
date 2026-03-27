# Parent Score Summary

- generated_at: 2026-03-27T16:10:59.792945+00:00
- run_count: 60

## Alias Metrics
- arm_alpha: mean=4.725, median=5.0, runs=30
- arm_beta: mean=4.846, median=5.0, runs=30

## Added Metrics
- arm_alpha: review_recall=0.133, review_precision_hint=0.5, package_pass_rate=1.0, one_pass_pass_rate=1.0
- arm_beta: review_recall=0.667, review_precision_hint=0.5, package_pass_rate=1.0, one_pass_pass_rate=1.0

## Task Medians
- BUG-01: arm_alpha=5.0, arm_beta=5.0
- BUG-02: arm_alpha=5.0, arm_beta=5.0
- DEV-01: arm_alpha=5.0, arm_beta=5.0
- OPS-01: arm_alpha=5.0, arm_beta=5.0
- RES-01: arm_alpha=5.0, arm_beta=5.0
- REV-01: arm_alpha=3.2, arm_beta=4.075

## Verdict
- {"baseline_alias": "arm_alpha", "candidate_alias": "arm_beta", "hard_fail_ok": true, "mean_ok": true, "median_ok": true, "gate_ok": true, "review_ok": true, "non_inferior": true, "better_or_equal": true, "strictly_better": true, "strict_wins": ["mean_overall", "review_recall"], "strict_losses": [], "note": "Strict superiority now requires non-inferiority plus no losses on mean/package/one-pass/review and at least two strict wins."}
- tiebreaker_triggered=False

## Alias Mapping
- arm_alpha -> main
- arm_beta -> docs/agent-instructions-simplify
