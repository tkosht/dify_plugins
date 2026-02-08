# GPT-5 Agent Strategies Plugin

This plugin provides GPT-5 oriented agent strategies for Dify.

## Strategies
- `gpt5_function_calling`
- `gpt5_react`

## Design
- Keeps agent persistence and context-gathering policies in a centralized prompt policy module.
- Uses the same model selector and tool selector contracts as Dify official strategy plugins.
