Task ID: BUG-02

Goal:
- Close minimal payload strictness gaps around bool coercion and `json_schema.strict`.

Read scope:
- `app/openai_gpt5_responses/internal/payloads.py`
- `tests/openai_gpt5_responses/test_payloads.py`
- `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`

Write scope:
- `app/openai_gpt5_responses/internal/payloads.py`
- `tests/openai_gpt5_responses/test_payloads.py`
- `tests/openai_gpt5_responses/test_payloads_bool_coercion.py`

Constraints:
- Touch no other files.
- Preserve the existing payload structure unless a specific strictness fix requires otherwise.
- Parent will run authoritative gates after you finish.

Success criteria:
- Bool-like parameters remain strict and predictable.
- `json_schema.strict` handling is explicit and tested.
- The patch is minimal and stays within the declared scope.

Return JSON only, matching the provided schema.
