# Dify Plugin Requests CVE Waiver Research (2026-03-28)

date: 2026-03-28
scope:
  - .github/workflows/ci.yml
  - .github/workflows/test-all-subsystems.yml
  - .github/dependabot.yml
  - app/openai_gpt5_responses
  - app/gpt5_agent_strategies
tags: dify-plugin, requests, pip-audit, cve-2026-25645, dependabot, github-actions

## Problem
- GitHub Actions `CI / test (3.11)` and `Test All Subsystems / security-audit`
  failed on `pip-audit`.
- Failing dependency:
  - resolved package: `requests 2.32.5`
  - vulnerability: `CVE-2026-25645`

## Upstream Facts
- PyPI latest `dify-plugin` is `0.7.4` as of 2026-03-28.
- `langgenius/dify-plugin-sdks` latest GitHub release is also `0.7.4`.
- Upstream `python/pyproject.toml` still declares `requests~=2.32.3`.
- `main` of `langgenius/dify-plugin-sdks` matches tag `0.7.4`; no newer fix was
  present at investigation time.

## Vulnerability Facts
- Advisory: `GHSA-gc5v-m9x4-r6x2` / `CVE-2026-25645`
- Severity: `medium`
- Fixed version: `requests 2.33.0`
- Advisory notes that standard Requests usage is not affected; impact is limited
  to applications calling `requests.utils.extract_zipped_paths()` directly.

## Local / Repo Verification
- Current plugin requirements:
  - `app/openai_gpt5_responses/requirements.txt` -> `dify-plugin==0.7.1`
  - `app/gpt5_agent_strategies/requirements.txt` -> `dify-plugin==0.7.1`
- Resolving either requirements file installs `requests 2.32.5`.
- Forcing `dify-plugin==0.7.1` with `requests>=2.33.0` is unsatisfiable because
  upstream constrains `requests>=2.32.3,<2.33.dev0`.
- A temporary patched checkout of `langgenius/dify-plugin-sdks` with the
  `requests~=2.32.3` line removed installs cleanly with `requests 2.33.0`.
- In that patched environment, `tests/openai_gpt5_responses` and
  `tests/gpt5_agent_strategies` passed (`167 passed`).

## Decision
- Keep using official `dify-plugin`.
- Temporarily waive `CVE-2026-25645` alongside the existing Flask waiver.
- Add a stale-waiver gate so CI fails once official `dify-plugin` no longer
  resolves the waived CVE.
- Enable Dependabot for the two plugin `requirements.txt` files so new
  `dify-plugin` releases generate update PRs.

## Removal Criteria
- `dify-plugin` upstream releases a version whose dependency constraints allow
  `requests>=2.33.0`.
- Dependabot or a manual update PR moves this repo to that version.
- The stale-waiver gate confirms that `CVE-2026-25645` is no longer reported
  without ignore flags, at which point the waiver must be deleted.

## Sources
- `https://github.com/advisories/GHSA-gc5v-m9x4-r6x2`
- `https://github.com/psf/requests/releases/tag/v2.33.0`
- `https://github.com/langgenius/dify-plugin-sdks/releases/tag/0.7.4`
- `https://raw.githubusercontent.com/langgenius/dify-plugin-sdks/main/python/pyproject.toml`
- `https://pypi.org/pypi/dify-plugin/0.7.4/json`
