from __future__ import annotations

from app.gpt5_agent_strategies.prompt.template import (
    CONTEXT_GATHERING_POLICY,
    PERSISTENCE_POLICY,
    TOOL_PREAMBLE_POLICY,
    UNCERTAINTY_POLICY,
)


def build_system_instruction(base_instruction: str) -> str:
    instruction = (base_instruction or "").strip()
    if not instruction:
        instruction = "You are a helpful GPT-5 agent."

    blocks = [
        instruction,
        PERSISTENCE_POLICY,
        CONTEXT_GATHERING_POLICY,
        UNCERTAINTY_POLICY,
        TOOL_PREAMBLE_POLICY,
    ]
    return "\n\n".join(blocks)
