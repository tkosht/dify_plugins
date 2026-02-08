from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.openai_gpt5_responses.internal.messages import (
    extract_output_text,
    extract_tool_calls,
    prompt_messages_to_responses_input,
)


@dataclass
class FakeFunction:
    name: str
    arguments: Any


@dataclass
class FakeToolCall:
    id: str
    function: FakeFunction


@dataclass
class FakeMessage:
    role: str
    content: Any = ""
    tool_calls: list[FakeToolCall] | None = None
    tool_call_id: str | None = None


@dataclass
class FakeContentPart:
    data: str


def _part_types(parts: list[dict[str, Any]]) -> set[str]:
    return {str(part["type"]) for part in parts}


def test_prompt_messages_keep_tool_call_context() -> None:
    assistant = FakeMessage(
        role="assistant",
        content="thinking",
        tool_calls=[
            FakeToolCall(
                id="call_1",
                function=FakeFunction(
                    name="lookup", arguments='{"q":"hello"}'
                ),
            )
        ],
    )
    tool = FakeMessage(
        role="tool", content="tool result", tool_call_id="call_1"
    )

    payload = prompt_messages_to_responses_input([assistant, tool])

    assert payload[0]["role"] == "assistant"
    assistant_parts = payload[0]["content"]
    assert _part_types(assistant_parts) == {"output_text", "function_call"}

    function_call_part = next(
        part for part in assistant_parts if part["type"] == "function_call"
    )
    assert function_call_part["call_id"] == "call_1"
    assert function_call_part["name"] == "lookup"
    assert function_call_part["arguments"] == '{"q":"hello"}'

    assert payload[1]["role"] == "tool"
    tool_part = payload[1]["content"][0]
    assert tool_part["type"] == "function_call_output"
    assert tool_part["call_id"] == "call_1"
    assert tool_part["output"] == "tool result"


def test_prompt_messages_plain_user_content_is_still_input_text() -> None:
    user = FakeMessage(role="user", content="hello")
    payload = prompt_messages_to_responses_input([user])

    assert payload == [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": "hello"}],
        }
    ]


def test_prompt_messages_keep_empty_tool_output_with_call_id() -> None:
    tool = FakeMessage(role="tool", content="", tool_call_id="call_empty")

    payload = prompt_messages_to_responses_input([tool])

    assert payload == [
        {
            "role": "tool",
            "content": [
                {
                    "type": "function_call_output",
                    "call_id": "call_empty",
                    "output": "",
                }
            ],
        }
    ]


def test_prompt_messages_support_mixed_content_and_mapping_tool_arguments() -> (
    None
):
    assistant = FakeMessage(
        role="assistant",
        content=[
            FakeContentPart(data="line1"),
            {"text": "line2"},
            {"data": "line3"},
        ],
        tool_calls=[
            FakeToolCall(
                id="call_map",
                function=FakeFunction(name="lookup", arguments={"q": "x"}),
            )
        ],
    )

    payload = prompt_messages_to_responses_input([assistant])

    parts = payload[0]["content"]
    assert parts[0] == {"type": "output_text", "text": "line1\nline2\nline3"}
    assert parts[1]["type"] == "function_call"
    assert parts[1]["arguments"] == '{"q": "x"}'


def test_prompt_messages_skip_invalid_tool_call_without_id_or_name() -> None:
    assistant = FakeMessage(
        role="assistant",
        content="thought",
        tool_calls=[
            FakeToolCall(
                id="", function=FakeFunction(name="lookup", arguments="{}")
            ),
            FakeToolCall(
                id="call", function=FakeFunction(name="", arguments="{}")
            ),
        ],
    )

    payload = prompt_messages_to_responses_input([assistant])
    assert payload == [
        {
            "role": "assistant",
            "content": [{"type": "output_text", "text": "thought"}],
        }
    ]


def test_extract_output_text_prefers_direct_output_text() -> None:
    response = FakeMessage(role="assistant", content="")
    response.output_text = "direct"
    response.output = [
        {
            "content": [
                {
                    "type": "output_text",
                    "text": "fallback",
                }
            ]
        }
    ]

    assert extract_output_text(response) == "direct"


def test_extract_output_text_reads_mapping_and_object_parts() -> None:
    part_obj = FakeMessage(role="assistant", content="")
    part_obj.type = "output_text"
    part_obj.text = "obj"
    response = FakeMessage(role="assistant", content="")
    response.output_text = None
    response.output = [
        {"content": [{"type": "output_text", "text": "map"}]},
        {"content": [part_obj]},
        {"content": [{"type": "summary_text", "text": "ignored"}]},
    ]

    assert extract_output_text(response) == "map\nobj"


def test_extract_tool_calls_accepts_mapping_and_object_items() -> None:
    obj_call = FakeMessage(role="assistant", content="")
    obj_call.type = "function_call"
    obj_call.call_id = "call_obj"
    obj_call.name = "obj_lookup"
    obj_call.arguments = {"q": "obj"}

    response = FakeMessage(role="assistant", content="")
    response.output = [
        {
            "type": "function_call",
            "call_id": "call_map",
            "name": "map_lookup",
            "arguments": {"q": "map"},
        },
        obj_call,
        {
            "type": "function_call",
            "call_id": "call_no_name",
            "name": "",
            "arguments": "{}",
        },
    ]

    assert extract_tool_calls(response) == [
        {
            "id": "call_map",
            "name": "map_lookup",
            "arguments": '{"q": "map"}',
        },
        {
            "id": "call_obj",
            "name": "obj_lookup",
            "arguments": '{"q": "obj"}',
        },
    ]
