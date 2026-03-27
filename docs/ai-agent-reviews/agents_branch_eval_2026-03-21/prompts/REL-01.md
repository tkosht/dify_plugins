Task ID: REL-01

Goal:
- Restore the seeded release-readiness regression for the `openai_gpt5_responses` plugin.
- Keep the fix minimal and make the packaging contract explicit in tests.

Read scope:
- `app/openai_gpt5_responses/manifest.yaml`
- `app/openai_gpt5_responses/provider/openai_gpt5.yaml`
- `tests/openai_gpt5_responses/test_provider_schema.py`

Write scope:
- `app/openai_gpt5_responses/manifest.yaml`
- `app/openai_gpt5_responses/provider/openai_gpt5.yaml`
- `tests/openai_gpt5_responses/test_provider_schema.py`

Constraints:
- Touch no other files.
- Prefer the smallest fix that restores packaging and schema consistency.
- Parent will run authoritative `ruff`, `pytest`, `dify plugin package`, `dify signature sign`, and `dify signature verify` gates after you finish.

Success criteria:
- `manifest.yaml` references only real provider YAML paths.
- provider Python source paths point to real runtime files.
- `test_provider_schema.py` covers the repaired packaging-critical contract.
- The diff stays limited to the declared files.

Return JSON only, matching the provided schema.
