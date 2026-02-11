---
name: app-security-review
description: "Security review skill for a specified app subdirectory (for example app/sharepoint_list). Use when requests ask for security checks, vulnerability review, hardening validation, release readiness gate, or secure design feedback for Python/Dify-style app modules. Audit code, manifests, provider/tool YAML, dependencies, auth/credential handling, input validation, outbound HTTP safety, and logging hygiene. Return severity-ranked findings with OWASP/NIST/CWE references, concrete remediations, and PASS/FAIL gate."
---

# App Security Review

## Purpose
- Audit one concrete target under `app/<subdir>` with a repeatable, standards-aligned workflow.
- Produce a decision-ready report: findings, evidence, remediation, retest steps, and gate result.
- Prioritize real exploitable risk over style-only concerns.

## Inputs
- Required: `target_app_path` (must be an existing directory under `app/`).
- Optional: `review_profile` in `quick | standard | deep` (default: `standard`).

## Output Contract
- Use the format in `references/report_template.md`.
- Include per finding:
  - `ID`
  - `Severity` (`Critical | High | Medium | Low`)
  - `Standard Refs` (OWASP/NIST/CWE)
  - `Evidence` (`path:line` + observed behavior)
  - `Impact`
  - `Remediation`
  - `Confidence` (`High | Medium | Low`)
- Gate rule:
  - `FAIL` if at least one `Critical` or `High`.
  - Otherwise `PASS with recommendations`.

## Workflow
1. Validate scope and inventory files.
2. Build a trust-boundary map (inputs, credentials, outbound calls, persistence, logs).
3. Run baseline automated checks (if tools exist).
4. Execute manual control checks using `references/security_control_matrix.md`.
5. Assign severity and confidence.
6. Produce report and gate decision.

## Step 1: Scope and Inventory
- Reject targets outside `app/`.
- Gather key files:
  - `manifest.yaml`
  - `provider/*.yaml`
  - `tools/*.yaml`
  - `requirements.txt`
  - `**/*.py`
  - `PRIVACY.md`, `README.md`
- Fast inventory commands:

```bash
eza -1 "$target_app_path"
rg --files "$target_app_path"
```

## Step 2: Trust-Boundary Map
- Identify entrypoints and control paths:
  - runtime credentials access
  - OAuth or API key handling
  - request builders and HTTP client layers
  - debug logging paths
- Identify attacker-controlled inputs and where they flow.

## Step 3: Automated Baseline (Best Effort)
- Run when available; never block the review if unavailable.

```bash
# Code-level security smells
bandit -r "$target_app_path"

# Dependency CVEs
pip-audit -r "$target_app_path/requirements.txt"
```

- If a tool is missing, record `not_executed` with reason and continue manually.

## Step 4: Manual Review Controls
- Use `references/security_control_matrix.md` as the required checklist.
- Always cover these areas:
  - AuthN/AuthZ correctness
  - Credential and secret handling
  - Input validation and injection resistance
  - Outbound HTTP safety and SSRF controls
  - Logging and error-message hygiene
  - Configuration hardening
  - Dependency and supply-chain risk
  - Security test coverage for regressions

## Step 5: Severity Assignment
- `Critical`: immediately exploitable with severe impact (credential leak, privilege bypass, RCE class).
- `High`: likely exploitable and high business impact.
- `Medium`: meaningful weakness requiring remediation, but exploit path is constrained.
- `Low`: defense-in-depth or hardening recommendation.

## Step 6: Report Assembly
- Follow `references/report_template.md` exactly.
- Make every claim evidence-based (`path:line`, command output, or concrete behavior).
- Do not reveal raw secrets or tokens in findings.

## Guardrails
- Prefer facts over speculation.
- Avoid false precision; mark uncertain items with lower confidence and explicit assumptions.
- If data is insufficient, report `Needs verification` instead of guessing.

## References
- `references/security_control_matrix.md`
- `references/report_template.md`
- `references/standards_sources.md`
