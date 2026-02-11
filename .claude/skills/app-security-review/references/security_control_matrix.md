# Security Control Matrix

## Scope
Use this matrix for any `app/<subdir>` review.  
Apply all controls in `standard` profile.  
For `quick`, run Priority `P0` first, then `P1` when time allows.  
For `deep`, run all controls plus architecture-specific extras discovered during review.

## Severity and Priority
- `P0`: Must-check. Missing evidence or failure usually yields High/Critical risk.
- `P1`: Strongly recommended. Missing evidence usually yields Medium/High risk.
- `P2`: Defense-in-depth. Missing evidence usually yields Low/Medium risk.

## Controls
| ID | Priority | What to verify | Typical evidence pattern | Standards mapping | CWE mapping | Default severity if broken |
|---|---|---|---|---|---|---|
| AUTH-001 | P0 | Access control is enforced per operation; no broad default allow for item/resource actions. | Tool or operation handlers with missing authorization path; direct object identifiers accepted without ownership/permission checks. | OWASP API1:2023, API5:2023, OWASP Top10 A01:2021, ASVS Access Control domain | CWE-862, CWE-639 | High |
| AUTH-002 | P0 | Authentication state is validated before privileged actions. | `runtime.credentials` or equivalent is optional but write operations proceed. | OWASP API2:2023, OWASP Top10 A07:2021, ASVS Authentication domain | CWE-287 | High |
| AUTH-003 | P1 | Token refresh and expiry handling are explicit and fail safe. | Token parsing without expiry checks; refresh errors silently ignored. | OWASP API2:2023, ASVS Session/Credential lifecycle domains | CWE-613 | Medium |
| SECR-001 | P0 | No hardcoded credentials or secrets in code, tests, YAML, docs. | Keys/tokens/password patterns in tracked files. | OWASP Top10 A02:2021, ASVS Data Protection domain | CWE-798 | Critical |
| SECR-002 | P0 | Secrets are never logged in plaintext. | Debug log payload includes `Authorization`, API key, bearer token, refresh token. | OWASP Top10 A09:2021, ASVS Logging domain | CWE-532 | High |
| SECR-003 | P1 | Secret sources are centralized and minimally scoped. | Multiple ad-hoc credential reads with inconsistent validation/sanitization. | SSDF PW.4, ASVS Architecture/Data Protection domains | CWE-200 | Medium |
| INPUT-001 | P0 | Untrusted user inputs are validated by type/range/format before use. | ID/URL/filter fields passed downstream without validator functions. | OWASP API8:2023, OWASP Top10 A03:2021, ASVS Input Validation domain | CWE-20 | High |
| INPUT-002 | P0 | No dangerous dynamic execution primitives on untrusted content. | `eval`, `exec`, unsafe `yaml.load`, unsafe deserialization usage. | OWASP Top10 A03:2021, ASVS Input/Deserialization guidance | CWE-94, CWE-502 | Critical |
| INPUT-003 | P1 | Path and resource identifiers are allow-listed or constrained. | User-provided path/URL/identifier used directly in outbound calls or filesystem access. | OWASP API8:2023, OWASP API7:2023, ASVS Input Validation domain | CWE-22, CWE-99 | High |
| HTTP-001 | P0 | Outbound HTTP calls use explicit timeout. | `requests.get/post/...` without `timeout=`. | OWASP Top10 A05:2021, ASVS Communications domain | CWE-400 | Medium |
| HTTP-002 | P0 | Outbound destinations are validated to prevent SSRF-style abuse. | User-controlled full URLs or hostnames sent without origin/domain constraints. | OWASP API7:2023, OWASP Top10 A10:2021, ASVS Communications domain | CWE-918 | High |
| HTTP-003 | P1 | TLS verification remains enabled in production path. | `verify=False`, insecure adapters, disabled certificate checks. | OWASP Top10 A02:2021, ASVS Communications domain | CWE-295 | High |
| HTTP-004 | P1 | Retry logic avoids replaying non-idempotent unsafe operations blindly. | Generic retry wrapping POST/PATCH without idempotency guard. | OWASP API4:2023, ASVS Error/Resilience guidance | CWE-799 | Medium |
| CONF-001 | P1 | Manifest/provider/tool YAML follows least-privilege and secure defaults. | Over-broad permissions, debug defaults enabled, weak credential schemas. | OWASP Top10 A05:2021, ASVS Configuration domain | CWE-16 | Medium |
| CONF-002 | P1 | Debug/log toggles are explicit and safe by default. | Verbose diagnostics enabled by default in production code path. | OWASP Top10 A09:2021, ASVS Logging domain | CWE-489 | Medium |
| ERR-001 | P1 | Error responses avoid leaking internals/secrets. | Raw exception bodies, stack traces, request metadata with sensitive fields returned to users. | OWASP Top10 A09:2021, ASVS Error Handling domain | CWE-209 | Medium |
| DEP-001 | P0 | Dependencies are scanned and known critical CVEs are triaged. | No dependency audit evidence; vulnerable package versions unresolved. | OWASP Top10 A06:2021, SSDF RV.1 | CWE-1104 | High |
| DEP-002 | P2 | Dependency pinning/constraints minimize supply-chain drift. | Wide-open version ranges without review gate. | OWASP Top10 A06:2021, SSDF PS.3 | CWE-1104 | Medium |
| LOG-001 | P1 | Security-relevant actions produce auditable, non-sensitive logs. | Missing audit logs for auth failures / privilege operations. | OWASP Top10 A09:2021, ASVS Logging domain | CWE-778 | Medium |
| TEST-001 | P1 | Security regression tests exist for key controls. | No tests for token redaction, auth failures, validation boundaries, SSRF guards. | SSDF PW.8, RV.1 | CWE-693 | Medium |

## Evidence Collection Commands
Use these patterns as baseline and add target-specific searches:

```bash
rg -n "runtime\\.credentials|access_token|refresh_token|api[_-]?key|secret|Authorization|Bearer" "$target_app_path"
rg -n "requests\\.(get|post|put|patch|delete)\\(" "$target_app_path" --glob '*.py'
rg -n "eval\\(|exec\\(|yaml\\.load\\(|pickle\\.|subprocess\\." "$target_app_path" --glob '*.py'
rg -n "debug|traceback|print\\(|logger\\." "$target_app_path" --glob '*.py'
```

## Mapping Notes
- Map each finding to at least one OWASP reference and one CWE when feasible.
- Use chapter-level ASVS references when exact control IDs are uncertain.
- Avoid fabricated requirement IDs; prefer precise chapter/domain references over guessing.
