from __future__ import annotations

from app.gpt5_agent_strategies.internal.loop import should_continue
from app.gpt5_agent_strategies.internal.policy import build_system_instruction


def test_build_system_instruction_contains_policy_sections() -> None:
    text = build_system_instruction(base_instruction="You are a coding agent")

    assert "<persistence>" in text
    assert "<context_gathering>" in text
    assert "<uncertainty_and_ambiguity>" in text


def test_should_continue_stops_at_max_iterations() -> None:
    assert should_continue(iteration=1, maximum_iterations=3, has_tool_call=True)
    assert not should_continue(iteration=3, maximum_iterations=3, has_tool_call=True)


def test_should_continue_stops_without_tool_call() -> None:
    assert not should_continue(iteration=1, maximum_iterations=5, has_tool_call=False)
