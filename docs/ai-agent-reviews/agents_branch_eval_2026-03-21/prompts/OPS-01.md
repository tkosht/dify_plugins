Task ID: OPS-01

Goal:
- Audit currentness-sensitive documentation and model catalog claims for the OpenAI GPT-5 Responses plugin.

Allowed local files:
- `app/openai_gpt5_responses/README.md`
- `app/openai_gpt5_responses/models/llm/_position.yaml`
- `app/openai_gpt5_responses/models/llm/*.yaml`
- `app/openai_gpt5_responses/.env.example`

External source policy:
- Use official OpenAI sources only.
- If a claim cannot be verified from official sources, mark it `unknown`.

Constraints:
- Read-only task. Do not modify any file.
- Do not open or quote any real `.env` file.
- Do not use non-official domains.

Deliverable expectations:
- Identify which local claims look current, stale, or unknown.
- Include the official URLs you relied on.
- Recommend the smallest follow-up update for each stale/unknown item.

Return JSON only, matching the provided schema.
