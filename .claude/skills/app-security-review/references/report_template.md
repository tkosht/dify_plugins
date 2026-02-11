# Security Review Report Template

## 1. Summary
- Target: `<app/subdir>`
- Review profile: `<quick|standard|deep>`
- Review date: `<YYYY-MM-DD>`
- Reviewer: `<agent>`
- Gate result: `<PASS | FAIL>`
- Gate reason: `<one-line reason>`

## 2. Scope and Method
- In-scope files:
  - `<path>`
  - `<path>`
- Out-of-scope or unavailable artifacts:
  - `<path or reason>`
- Executed checks:
  - `manual_matrix`: `<done>`
  - `bandit`: `<done|not_executed:reason>`
  - `pip-audit`: `<done|not_executed:reason>`

## 3. Findings
Use one block per finding. Sort by severity then exploitability.

### `[F-001] <Short title>`
- Severity: `<Critical|High|Medium|Low>`
- Confidence: `<High|Medium|Low>`
- Standard refs: `<OWASP/API/ASVS/SSDF refs>`
- CWE: `<CWE-xxx>`
- Evidence:
  - `<path:line> <observed fact>`
  - `<path:line> <observed fact>`
- Impact:
  - `<who/what is impacted and how>`
- Remediation (minimum viable fix):
  1. `<change>`
  2. `<change>`
- Verification steps:
  - `<command>`
  - `<expected outcome>`

## 4. Positive Controls Observed
- `<control that is correctly implemented>`
- `<control that is correctly implemented>`

## 5. Residual Risks
- `<accepted risk or unknown pending verification>`

## 6. Recommended Next Actions
1. `<highest-priority fix>`
2. `<second fix>`
3. `<test/monitoring follow-up>`

## Gate Evaluation Rule (fixed)
- `FAIL` if any finding severity is `Critical` or `High`.
- Else `PASS with recommendations`.
