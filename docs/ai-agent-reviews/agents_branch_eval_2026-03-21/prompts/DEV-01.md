Task ID: DEV-01

Goal:
- Add a new predefined model entry for `gpt-5.3-codex-spark`.
- Keep the change minimal and consistent with the existing `gpt-5.3-codex` model definition.

Read scope:
- `app/openai_gpt5_responses/models/llm/_position.yaml`
- `app/openai_gpt5_responses/models/llm/gpt-5.3-codex.yaml`
- `tests/openai_gpt5_responses/test_provider_schema.py`

Write scope:
- `app/openai_gpt5_responses/models/llm/_position.yaml`
- `app/openai_gpt5_responses/models/llm/gpt-5.3-codex-spark.yaml`
- `tests/openai_gpt5_responses/test_provider_schema.py`

Constraints:
- Touch no other files.
- Do not install tools or edit project-wide configuration.
- Parent will run authoritative gates after you finish.

Success criteria:
- `gpt-5.3-codex-spark.yaml` exists and mirrors the `gpt-5.3-codex` schema shape closely.
- `_position.yaml` includes the new model near the existing codex variants without disturbing the GPT-5.4 and GPT-5.2 priority block.
- `test_provider_schema.py` checks that the new predefined model exists.

Return JSON only, matching the provided schema.
