Task ID: BUG-01

Goal:
- Fix `select_fields` empty/blank edge handling so request builders never emit malformed `$expand` values.
- Keep request-building behavior and tests consistent.

Read scope:
- `app/sharepoint_list/internal/validators.py`
- `app/sharepoint_list/internal/request_builders.py`
- `tests/sharepoint_list/test_validators.py`
- `tests/sharepoint_list/test_operations_select.py`

Write scope:
- `app/sharepoint_list/internal/validators.py`
- `app/sharepoint_list/internal/request_builders.py`
- `tests/sharepoint_list/test_validators.py`
- `tests/sharepoint_list/test_operations_select.py`

Constraints:
- Touch no other files.
- Prefer the smallest fix that makes the contract explicit.
- Parent will run authoritative gates after you finish.

Success criteria:
- Empty or blank `select_fields` inputs do not generate `fields($select=)` in request builders.
- The selected behavior is covered by targeted tests.
- The diff stays limited to the declared files.

Return JSON only, matching the provided schema.
