# Candidate validation (2026-11-13)

**Local implementation tested; stock Dify plugin non-operational/fail-closed; Dify integration, representative quality and production security NOT accepted.** Exact commands and supported scope are in README.md. No Dify deployment, global network/model/log change, external OCR/API/storage or PDF change was performed.

Evidence: `pytest-deps-final.txt` (local tests, including test doubles), `real-ocr-deps-final.json` (one actual synthetic Japanese OCR input under Docker network-none), `source-release-sha256.txt` (candidate identities), `package.txt` (actual CLI package check), `image.json` (container identity), `environment.md`, `security.md`, `failed-ocr-attempt.md`. Mock adapter tests inject trusted context outside tool arguments; this is not stock Dify runtime evidence. Each table distinguishes local observations from complete requirement acceptance.

| Requirement | Local observation | Whole requirement |
|---|---|---|
| F01 | PNG/JPEG normalization/API registration tests; actual Japanese PNG overview | Local tested; deployment unperformed |
| F02 | Overview JSON/page metadata returned by adapter mock | Agent delivery unperformed |
| F03 | Strict flat/nested region contracts and service path tested | Actual Agent call unperformed |
| F04 | Original stored PNG used for every request; deterministic crop tests | Local tested |
| F05 | Decimal floor/ceil/scale/output bounds and metadata tests | Local tested |
| F06 | Actual jpn+eng OCR + transformed polygon unit tests | Local tested; representative data unperformed |
| F07 | no_text/unreadable/low-score/truncation semantics tested | Local tested; Agent interpretation unperformed |
| F08 | Atomic call/image/pixel/TTL budgets, bounded response, kill deadline tested | Local tested; target timing unperformed |
| F09 | request/image/page/geometry/engine identifiers in response | Local tested; Dify trace unperformed |
| F10 | Delete/TTL/restart/active-OCR race tests | Local tested; real Chatflow abnormal-end path unperformed |
| F11 | Structured input/auth/availability/OCR errors tested | Local tested; full deployment paths unperformed |
| F12 | Unique image IDs and page/order metadata in service and adapter | Local tested; target multi-page chain unperformed |

| Requirement | Observation / status |
|---|---|
| N01 | Offline real OCR succeeds; native attempted connections and target plugin/LLM paths unperformed; not accepted |
| N02 | Local app/run isolation, races and guarded resolver tested; target trusted context unresolved; not accepted |
| N03 | Strict argument rejection and local log canaries tested; Dify/provider/proxy logs unperformed |
| N04 | Local MIME/size/dimension/traversal/URL/number/unknown-key tests; target endpoints unperformed |
| N05 | Self-service lifecycle documented/tested; Dify/LLM/observability retention unknown |
| N06 | Dependency/model locks, source hashes and actual package/image recorded; current vulnerability audit separately recorded |
| N07 | Isolated branch/clone, loopback setup and rollback; actual deployment unperformed |
| N08 | One synthetic manually selected region proxy only; B0/full Agent T/representative ground truth unperformed; not accepted |

| Tests | Status and evidence |
|---|---|
| T01–T09 | Local tests pass (real PNG OCR separately); T07 deterministic source/crop proof |
| T10–T13 | Local tests pass; actual native output has validated TSV headers/rows; malformed exit-zero output is OCR_FAILED |
| T14 | Local unique/page/scope tests pass; live Dify page flow unperformed |
| T15 | Adapter has no OSD; input/output dimensions and inverse mapping tested. Native internal resolution sampling not instrumented; partially unperformed |
| D01–D10 | All real Dify tests unperformed, including optional D08 image reinjection. No DSL supplied; guarded plugin fails closed |
| S-T01–S-T05 | Local auth/scope/strict args/URL and image defensive tests pass; deployment paths unperformed |
| S-T06 | Actual OCR success with Docker external network unavailable; native attempt tracing unperformed; partial |
| S-T07 | Local missing/hash/version preparation checks fail closed; offline model preparation/read works; full startup/failure/restart packet tracing unperformed |
| S-T08 | Local canary test passes; all deployed log layers unperformed; partial |
| S-T09–S-T11 | Local deletion/TTL/race/restart/single-owner/call tests pass; actual deployment abnormal completion unperformed |
| S-T12 | Tool paths only treat OCR as text; arbitrary URL/code arguments rejected. Actual adversarial document/Agent test unperformed |
| S-T13 | Locked hashes/licenses/build recorded; update/regression workflow documented; vulnerability audit status in audit artifact |
| S-T14 | Target LLM/observability destination/retention/approval inventory unperformed |

Quality: `real-ocr-deps-final.json` is one non-secret synthetic20px Japanese field. Both local overview and manually cropped2x output `温度\n-12.5\nmm`; strict CER2/11 from whitespace/newline differences; important numeric string matched in both. No demonstrated text accuracy improvement; confidence/status difference is not correctness evidence. Runtime and calls are measured per one run only, not latency percentiles. No Agent model or external model was called; B0/current application, B1/Agent-comparable T and representative30-page proposal remain unperformed.

Draft-to-ready conditions: a separately authorized, reviewed trusted per-run transport integration; real P0 file/context/JSON validation including duplicate/concurrent turns and injected arguments; all required Dify/security cases with actual host/model/retention evidence; representative approved ground truth and B0/B1/T comparison; dependency/container vulnerability disposition; installation and rollback rehearsal. Current local test/package success does not satisfy these conditions.

Per-ID machine-readable statuses and scope: [acceptance.json](acceptance.json). Final local dependency audit reports no known advisories for the final service lock and plugin lock; initial52reported findings (including aliases) in Pillow12.3.0/python-multipart0.0.22 were repaired with13.0.0/0.0.31. No container OS vulnerability audit is claimed.
