# SharePoint List Dify Plugin Doc Review 2025-12-26

## Problem
Review app/sharepoint_list implementation vs local docs to find mismatches or gaps.

## Research
- Docs: app/sharepoint_list/README.md, app/sharepoint_list/PRIVACY.md,
  docs/03.detail_design/sharepoint_list_list_items_filters.md,
  app/sharepoint_list/tools/*.yaml, review_sharepoint_list_tests.md
- Impl: app/sharepoint_list/internal/*.py, app/sharepoint_list/tools/*.py,
  app/sharepoint_list/provider/sharepoint_list.py
- Example commands:
  - rg --files -g 'app/sharepoint_list/**'
  - nl -ba app/sharepoint_list/internal/filters.py | sed -n '1,140p'

## Solution
- list_url validation requires sharepoint.com host; kept as-is (doc not updated).
- get_item select_fields display-name mapping is intended; no change.
- create/update fields_json display-name mapping is intended; no change.
- filters value remains required in docs; impl does not validate and relies on Graph API errors.
- createdDateTime case sensitivity documented in list_items.yaml.
- operator alias removed; parse_filters now requires op only, tests updated.
- privacy doc updated to describe optional debug logging and metadata scope.
- review_sharepoint_list_tests.md updated to reflect array/object support.
- list_items ordering (createdDateTime desc) documented in README/list_items.yaml.

## Verification
- Evidence collected by direct file inspection.
- Tests: `uv run pytest tests/sharepoint_list/test_filters.py`

## Tags
- sharepoint_list
- dify
- docs
- filters
- privacy

## Examples
```json
[{"field":"Status","op":"eq","value":"InProgress"}]
```
