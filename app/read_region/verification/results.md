# Validation scope — 0.2.0

The dedicated Agent strategy completed the controlled standard-Dify1.18.0 path. The independent Tool package retains its unsupported-context guard. The PR remains Draft because another deployment, production rollout, representative quality and complete production-security acceptance are not established.

Current evidence is [release-validation.json](release-validation.json), [release-validation.json](release-validation.json) and `release-source.sha256`. Older dated reports/packages record earlier candidates; their previous unperformed statuses are not current sandbox conclusions.

- Start → Agent → Answer completed through the standard SDK configured local fake model provider and real Tesseract OCR. No Dify core/SDK patch or paid model API was used.
- The same app/run scope was observed across signed file fetch200, register201, region read200 and delete200. Model-visible tools contained only read_region's six arguments. The next model response consumed real OCR, and its answer matched the observed OCR payload hash.
- Spoofed context/extra arguments, foreign-image, repeated-condition and over-budget model-output probes were rejected as expected. The model-output rejection probes use422; this does not change the service's429 budget contract. Fixed cleanup and private-canary checks are recorded in the sanitized report.
- The public report's `blocked_external_probe_payload_bytes` describes blocked external probes only, not all application traffic. No whole-system zero-traffic claim is made.
- The strategy uses fixed programmatic preparation/cleanup outside model choices. This differs from the original separate pre/post-node placement. Native execution metadata is distinct from private credentials/capabilities; no blanket statement that all Dify logs contain no content is made.

Local validation:98 tests passed; clean staged-candidate Ruff/Black passed; both category-exclusive packages passed official CLI construction, SDK registration/schema checks and canonical-source payload checks. Published Agent Python payloads match the tested candidate; final package changes are guide/privacy documents only.

| Requirement group | Current conclusion |
|---|---|
| F01–F09,F11,F12 | Local tests plus bounded synthetic sandbox orchestration evidence; target compatibility remains separate |
| F10 | Normal/error cleanup evidence and local TTL/restart/race tests; production retention not accepted |
| N01–N07 | Bounded local/sandbox observations only; no production security certification or all-layer retention acceptance |
| N08 | Representative B0/B1/T comparison unperformed; deterministic fake-model orchestration is not real-model accuracy evidence |
| D01 and six-argument dispatch | Controlled sandbox path verified; another deployment unperformed |
| D08 | Crop-image reinjection excluded and unperformed |
| T15 / S-T06–S-T14 deployment portions | Preserve limits in environment/security notes; no universal native-network, log or future-update guarantee |

The [Chatflow template](verified-chatflow.template.json) is modified and not import-tested. It is not a successful official export: export returned400, authenticated draft retrieval returned200. It contains placeholders rather than live deployment identities or credentials.

No accuracy improvement is claimed. Real-model reasoning, representative ground truth, production model/provider/observability retention, managed-plugin private-configuration deployment and production rollback rehearsal remain explicit next acceptance work. Service cleanup does not delete Dify/model/observability copies.
