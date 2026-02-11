# Task Spec: openai_responses_provider

## Objective
Create a Dify model provider plugin `openai_responses_provider` supporting OpenAI Responses API.

## Required outputs
- app/openai_responses_provider/**
- tests/openai_responses_provider/**
- subagent_report.json (root)

## Runtime/contract requirements
- Dify runtime entrypoint with Plugin(DifyPluginEnv(...)).
- Provider integration via ModelProvider.
- LLM implementation with `_invoke` and `_invoke_error_mapping` and no unresolved abstract methods.
- Chunk helper behavior (`_chunk` or equivalent stream helper).
- strict bool coercion: invalid values must raise ValueError.
- response_format=json_schema without schema must fail.

## Packaging/docs requirements
- manifest/provider YAML consistency.
- README.md / PRIVACY.md / .env.example / requirements.txt / icon.svg.

## Tests
- schema/runtime/payload/strictness/chunk/stream focused tests.

