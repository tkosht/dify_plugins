# SharePoint List Consistency Review (2026-01-12)

Scope (explicit)
- Docs: app/sharepoint_list/README.md, docs/03.detail_design/sharepoint_list_list_items_filters.md
- Tool specs: app/sharepoint_list/tools/*.yaml, app/sharepoint_list/provider/sharepoint_list.yaml
- Code: app/sharepoint_list/internal/*, app/sharepoint_list/tools/*.py
- Tests: tests/sharepoint_list/* (see evidence list below)

Summary
- Core tool contracts (create/update/get/list/get_choices), filters specification, select_fields handling, pagination behavior, and Prefer header logic are consistent across docs, code, and tests within the scoped files.
- No direct doc↔code or code↔tests contradictions found in the scoped evidence.
- Some doc claims are not explicitly covered by tests (not a mismatch, but a coverage gap).

Consistency Checks (high level)
1) Tool catalog & parameters: MATCH
   - Docs list tool names and parameters; YAML specs match; tool implementations consume the same fields.
2) list_url parsing & list_id resolution: MATCH
   - README guidance aligns with validators.parse_list_url + operations.resolve_list_id; tests cover AllItems URL + GUID.
3) select_fields: MATCH
   - README rules (quote removal, unknown field error, missing field fill) align with operations + tests.
4) filters spec: MATCH
   - README + design doc align with filters.py + operations.list_items + tests (operators, JSON form, createdDateTime top-level, fields/<name>, datetime quoting, and-join, Prefer header).
5) list_items pagination & ordering: MATCH
   - createdDateTime desc, page_size cap, page_token/next_page_token behavior align with code and tests.
6) get_choices: MATCH
   - YAML + code + tests agree on field_identifier, display/internal name resolution, and non-choice errors.

Coverage Gaps (docs/code claims not directly asserted in tests)
- created_after/created_before deprecation handling is documented and implemented, but no direct test assertion was found in the scoped tests.
- Error type mapping in README (GraphError/AuthenticationError/AuthorizationError/RateLimitError) is implemented in code; no direct test coverage was found in the scoped tests for these error branches.

Out of Scope (not evaluated)
- docs/dsl/*.yml, docs/note_sharepoint_list_devlog.md
- Runtime OAuth flows and provider behaviors outside the scoped evidence (e.g., refresh flows)

Evidence (file:line)
- Tools list + params in README: app/sharepoint_list/README.md:12-17
- list_url guidance: app/sharepoint_list/README.md:21-24
- select_fields rules: app/sharepoint_list/README.md:31-36
- filters spec & rules: app/sharepoint_list/README.md:38-85
- deprecated params: app/sharepoint_list/README.md:86-88
- error types + debug env vars: app/sharepoint_list/README.md:104-112
- filters design doc: docs/03.detail_design/sharepoint_list_list_items_filters.md:7-73
- tool YAML specs: app/sharepoint_list/tools/*.yaml (create_item.yaml:12-34, update_item.yaml:13-44, get_item.yaml:13-44, list_items.yaml:8-96, get_choices.yaml:13-34)
- select_fields parsing + validation + missing fields fill: app/sharepoint_list/internal/operations.py:346-361, 386-421, 908-951
- list_items filters/order/prefer/pagination: app/sharepoint_list/internal/operations.py:760-798, 1007-1063
- filters parsing/value formatting: app/sharepoint_list/internal/filters.py:7-67, 70-106
- list_url parsing: app/sharepoint_list/internal/validators.py:35-68
- get_choices behavior: app/sharepoint_list/internal/operations.py:485-629
- list_items tool handling: app/sharepoint_list/tools/list_items.py:49-83
- tests for list_url: tests/sharepoint_list/test_validators_list_url.py:7-31
- tests for filters: tests/sharepoint_list/test_filters.py:8-85
- tests for filters + Prefer header: tests/sharepoint_list/test_operations_filters.py:156-418
- tests for select_fields: tests/sharepoint_list/test_operations_select.py:50-501
- tests for get_choices: tests/sharepoint_list/test_operations_choices.py:45-103
- tests for pagination/page_size: tests/sharepoint_list/test_operations_crud.py:176-301
- tests for request builders: tests/sharepoint_list/test_requests.py:58-218
