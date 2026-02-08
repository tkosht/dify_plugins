from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass, field
from typing import Any

import pytest
from pydantic import BaseModel, Field


def _install_strategy_dify_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    entities_agent_mod = types.ModuleType("dify_plugin.entities.agent")
    entities_model_mod = types.ModuleType("dify_plugin.entities.model")
    entities_model_llm_mod = types.ModuleType("dify_plugin.entities.model.llm")
    entities_model_message_mod = types.ModuleType("dify_plugin.entities.model.message")
    entities_tool_mod = types.ModuleType("dify_plugin.entities.tool")
    interfaces_agent_mod = types.ModuleType("dify_plugin.interfaces.agent")

    class AgentInvokeMessage(dict):
        pass

    class ModelFeature:
        STREAM_TOOL_CALL = "stream_tool_call"
        VISION = "vision"

    @dataclass
    class LLMModelConfig:
        data: dict[str, Any]

        def __init__(self, **kwargs: Any) -> None:
            self.data = kwargs

    @dataclass
    class LLMUsage:
        total_price: float = 0.0
        currency: str = ""
        total_tokens: int = 0
        prompt_tokens: int = 0
        prompt_unit_price: float = 0.0
        prompt_price_unit: float = 0.0
        prompt_price: float = 0.0
        completion_tokens: int = 0
        completion_unit_price: float = 0.0
        completion_price_unit: float = 0.0
        completion_price: float = 0.0
        latency: float = 0.0

    @dataclass
    class LLMResult:
        model: str
        prompt_messages: list[Any]
        message: Any
        usage: LLMUsage | None
        system_fingerprint: Any = None

    @dataclass
    class LLMResultChunkDelta:
        message: Any
        usage: LLMUsage | None = None
        index: int = 0
        finish_reason: str = "stop"

    @dataclass
    class LLMResultChunk:
        model: str
        prompt_messages: list[Any]
        delta: LLMResultChunkDelta
        system_fingerprint: Any = None

    @dataclass
    class PromptMessage:
        content: Any = ""

    class PromptMessageContentType:
        TEXT = "text"
        IMAGE = "image"

    @dataclass
    class SystemPromptMessage(PromptMessage):
        pass

    @dataclass
    class UserPromptMessage(PromptMessage):
        pass

    @dataclass
    class ToolPromptMessage(PromptMessage):
        tool_call_id: str = ""
        name: str = ""

    @dataclass
    class AssistantPromptMessage(PromptMessage):
        tool_calls: list[Any] = field(default_factory=list)

        @dataclass
        class ToolCall:
            @dataclass
            class ToolCallFunction:
                name: str
                arguments: str

            id: str
            type: str
            function: AssistantPromptMessage.ToolCallFunction

    class ToolProviderType(str):
        pass

    class ToolInvokeMessage:
        class LogMessage:
            class LogStatus:
                START = "start"

        class MessageType:
            TEXT = "text"
            LINK = "link"
            IMAGE_LINK = "image_link"
            IMAGE = "image"
            JSON = "json"
            BLOB = "blob"

        @dataclass
        class TextMessage:
            text: str

        @dataclass
        class JsonMessage:
            json_object: dict[str, Any]

        class RetrieverResourceMessage:
            @dataclass
            class RetrieverResource:
                content: str
                position: Any = None
                dataset_id: Any = None
                dataset_name: Any = None
                document_id: Any = None
                document_name: Any = None
                data_source_type: Any = None
                segment_id: Any = None
                retriever_from: Any = None
                score: Any = None
                hit_count: Any = None
                word_count: Any = None
                segment_position: Any = None
                index_node_hash: Any = None
                page: Any = None
                doc_metadata: Any = None

    class _ErrorMeta:
        def __init__(self, message: str) -> None:
            self._message = message

        def to_dict(self) -> dict[str, str]:
            return {"error": self._message}

    class ToolInvokeMeta:
        @staticmethod
        def error_instance(message: str) -> _ErrorMeta:
            return _ErrorMeta(message)

    class ToolIdentity(BaseModel):
        name: str
        provider: str = "provider"

    class ToolEntity(BaseModel):
        identity: ToolIdentity
        runtime_parameters: dict[str, Any] = Field(default_factory=dict)
        provider_type: str = "builtin"

    class AgentModelEntity(BaseModel):
        features: list[str] = Field(default_factory=list)

    class AgentModelConfig(BaseModel):
        provider: str = "provider"
        model: str = "gpt-5.2"
        completion_params: dict[str, Any] = Field(default_factory=dict)
        history_prompt_messages: list[Any] = Field(default_factory=list)
        entity: AgentModelEntity | None = Field(default_factory=AgentModelEntity)

    class AgentStrategy:
        def _init_prompt_tools(self, tools: list[Any] | None) -> list[Any]:  # noqa: ARG002
            return []

        def recalc_llm_max_tokens(
            self, entity: Any, prompt_messages: list[Any], completion_params: dict[str, Any]
        ) -> None:  # noqa: ARG002
            return None

        def create_log_message(self, **kwargs: Any) -> dict[str, Any]:
            return {"kind": "log", **kwargs}

        def finish_log_message(
            self,
            *,
            log: dict[str, Any],
            data: dict[str, Any],
            metadata: dict[str, Any],
        ) -> dict[str, Any]:
            return {
                "kind": "log_finish",
                "log": log,
                "data": data,
                "metadata": metadata,
            }

        def create_text_message(self, text: str) -> dict[str, Any]:
            return {"kind": "text", "text": text}

        def create_blob_message(self, blob: bytes, meta: dict[str, Any]) -> dict[str, Any]:
            return {"kind": "blob", "blob": blob, "meta": meta}

        def create_json_message(self, payload: dict[str, Any]) -> dict[str, Any]:
            return {"kind": "json", "payload": payload}

        def create_retriever_resource_message(
            self, *, retriever_resources: list[Any], context: str
        ) -> dict[str, Any]:
            return {
                "kind": "retriever",
                "retriever_resources": retriever_resources,
                "context": context,
            }

        def increase_usage(self, llm_usage: dict[str, Any], usage: Any) -> None:
            llm_usage["usage"] = usage

        def update_prompt_message_tool(self, tool_instance: Any, prompt_tool: Any) -> None:  # noqa: ARG002
            return None

    entities_agent_mod.AgentInvokeMessage = AgentInvokeMessage
    entities_model_mod.ModelFeature = ModelFeature
    entities_model_llm_mod.LLMModelConfig = LLMModelConfig
    entities_model_llm_mod.LLMResult = LLMResult
    entities_model_llm_mod.LLMResultChunk = LLMResultChunk
    entities_model_llm_mod.LLMResultChunkDelta = LLMResultChunkDelta
    entities_model_llm_mod.LLMUsage = LLMUsage
    entities_model_message_mod.AssistantPromptMessage = AssistantPromptMessage
    entities_model_message_mod.PromptMessage = PromptMessage
    entities_model_message_mod.PromptMessageContentType = PromptMessageContentType
    entities_model_message_mod.SystemPromptMessage = SystemPromptMessage
    entities_model_message_mod.ToolPromptMessage = ToolPromptMessage
    entities_model_message_mod.UserPromptMessage = UserPromptMessage
    entities_tool_mod.ToolInvokeMessage = ToolInvokeMessage
    entities_tool_mod.ToolProviderType = ToolProviderType
    interfaces_agent_mod.AgentModelConfig = AgentModelConfig
    interfaces_agent_mod.AgentModelEntity = AgentModelEntity
    interfaces_agent_mod.AgentStrategy = AgentStrategy
    interfaces_agent_mod.ToolEntity = ToolEntity
    interfaces_agent_mod.ToolInvokeMeta = ToolInvokeMeta

    monkeypatch.setitem(sys.modules, "dify_plugin.entities.agent", entities_agent_mod)
    monkeypatch.setitem(sys.modules, "dify_plugin.entities.model", entities_model_mod)
    monkeypatch.setitem(
        sys.modules, "dify_plugin.entities.model.llm", entities_model_llm_mod
    )
    monkeypatch.setitem(
        sys.modules, "dify_plugin.entities.model.message", entities_model_message_mod
    )
    monkeypatch.setitem(sys.modules, "dify_plugin.entities.tool", entities_tool_mod)
    monkeypatch.setitem(sys.modules, "dify_plugin.interfaces.agent", interfaces_agent_mod)


class _SequenceLLM:
    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls = 0

    def invoke(self, **_: Any) -> Any:
        self.calls += 1
        if len(self._responses) > 1:
            return self._responses.pop(0)
        return self._responses[0]


def _build_model_config(strategy_module: Any, *, stream: bool) -> Any:
    features = [strategy_module.ModelFeature.STREAM_TOOL_CALL] if stream else []
    interfaces_mod = sys.modules["dify_plugin.interfaces.agent"]
    entity = interfaces_mod.AgentModelEntity(features=features)
    return strategy_module.AgentModelConfig(
        provider="openai",
        model="gpt-5.2",
        completion_params={},
        history_prompt_messages=[],
        entity=entity,
    )


def _build_tool_entity(name: str = "lookup", **kwargs: Any) -> Any:
    interfaces_mod = sys.modules["dify_plugin.interfaces.agent"]
    payload = {
        "identity": {"name": name, "provider": "provider"},
        "runtime_parameters": {},
        "provider_type": "builtin",
    }
    payload.update(kwargs)
    return interfaces_mod.ToolEntity(**payload)


@pytest.fixture
def strategy_module(monkeypatch: pytest.MonkeyPatch) -> Any:
    _install_strategy_dify_stub(monkeypatch)
    sys.modules.pop(
        "app.gpt5_agent_strategies.strategies.gpt5_function_calling", None
    )
    importlib.invalidate_caches()
    return importlib.import_module(
        "app.gpt5_agent_strategies.strategies.gpt5_function_calling"
    )


def test_invoke_blocking_result_message_none_is_safe(strategy_module: Any) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    llm_result = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=None,
        usage=None,
    )
    llm = _SequenceLLM([llm_result])
    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=lambda **_: []),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [],
                "maximum_iterations": 1,
            }
        )
    )

    assert llm.calls == 1
    assert any(m.get("kind") == "json" for m in messages)


def test_invoke_blocking_tool_not_found_path(strategy_module: Any) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    tool_call = strategy_module.AssistantPromptMessage.ToolCall(
        id="call_1",
        type="function",
        function=strategy_module.AssistantPromptMessage.ToolCall.ToolCallFunction(
            name="lookup",
            arguments='{"q":"hello"}',
        ),
    )
    llm_result = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="thinking",
            tool_calls=[tool_call],
        ),
        usage=None,
    )
    llm = _SequenceLLM([llm_result])
    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=lambda **_: []),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [],
                "maximum_iterations": 1,
            }
        )
    )

    text_messages = [
        m["text"]
        for m in messages
        if isinstance(m, dict) and m.get("kind") == "text"
    ]
    assert "there is not a tool named lookup" in "\n".join(text_messages)


def test_invoke_streaming_plain_text_path(strategy_module: Any) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    chunk = strategy_module.LLMResultChunk(
        model="gpt-5.2",
        prompt_messages=[],
        delta=types.SimpleNamespace(
            message=strategy_module.AssistantPromptMessage(
                content="stream hello",
                tool_calls=[],
            ),
            usage=None,
        ),
    )

    def _stream() -> Any:
        yield chunk

    llm = _SequenceLLM([_stream()])
    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=lambda **_: []),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=True),
                "tools": [],
                "maximum_iterations": 1,
            }
        )
    )

    text_messages = [
        m["text"]
        for m in messages
        if isinstance(m, dict) and m.get("kind") == "text"
    ]
    assert "stream hello" in text_messages


def test_invoke_parse_error_tool_call_path(strategy_module: Any) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    bad_tool_call = strategy_module.AssistantPromptMessage.ToolCall(
        id="call_bad",
        type="function",
        function=strategy_module.AssistantPromptMessage.ToolCall.ToolCallFunction(
            name="lookup",
            arguments="{broken",
        ),
    )
    llm_result = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="need tool",
            tool_calls=[bad_tool_call],
        ),
        usage=None,
    )
    llm = _SequenceLLM([llm_result])
    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=lambda **_: []),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [],
                "maximum_iterations": 1,
            }
        )
    )

    joined_text = "\n".join(
        [m["text"] for m in messages if m.get("kind") == "text"]
    )
    assert "tool arguments parse error" in joined_text


def test_invoke_max_iteration_limit_skips_tool_execution(strategy_module: Any) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    tool_call = strategy_module.AssistantPromptMessage.ToolCall(
        id="call_1",
        type="function",
        function=strategy_module.AssistantPromptMessage.ToolCall.ToolCallFunction(
            name="lookup",
            arguments='{"q":"hello"}',
        ),
    )
    first = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="round1",
            tool_calls=[tool_call],
        ),
        usage=None,
    )
    second = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="round2",
            tool_calls=[tool_call],
        ),
        usage=None,
    )
    llm = _SequenceLLM([first, second])
    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=lambda **_: []),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [],
                "maximum_iterations": 2,
            }
        )
    )

    finished_logs = [m for m in messages if m.get("kind") == "log_finish"]
    rendered = str(finished_logs)
    assert "Maximum iteration limit (2) reached" in rendered
    assert llm.calls == 2


def test_prompt_helper_methods_handle_images_and_system_message(
    strategy_module: Any,
) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()

    base_messages = strategy._init_system_message(
        "system prompt",
        [strategy_module.UserPromptMessage(content="hi")],
    )
    assert isinstance(base_messages[0], strategy_module.SystemPromptMessage)

    image_item = types.SimpleNamespace(
        type=strategy_module.PromptMessageContentType.IMAGE,
        data="https://example.com/a.png",
    )
    text_item = types.SimpleNamespace(
        type=strategy_module.PromptMessageContentType.TEXT,
        data="caption",
    )
    user = strategy_module.UserPromptMessage(content=[text_item, image_item])
    normalized = strategy._clear_user_prompt_image_messages([user])
    assert normalized[0].content == "caption\n[image]"


def test_invoke_tool_image_message_path(strategy_module: Any) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    tool_call = strategy_module.AssistantPromptMessage.ToolCall(
        id="call_img",
        type="function",
        function=strategy_module.AssistantPromptMessage.ToolCall.ToolCallFunction(
            name="lookup",
            arguments='{"q":"hello"}',
        ),
    )
    llm_result = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="need image",
            tool_calls=[tool_call],
        ),
        usage=None,
    )
    llm = _SequenceLLM([llm_result])
    image_response = types.SimpleNamespace(
        type=strategy_module.ToolInvokeMessage.MessageType.IMAGE,
        message=strategy_module.ToolInvokeMessage.TextMessage(
            text="https://example.com/image.png"
        ),
    )
    called: dict[str, Any] = {}

    def _tool_invoke(**kwargs: Any) -> list[Any]:
        called.update(kwargs)
        return [image_response]

    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=_tool_invoke),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [
                    _build_tool_entity(
                        runtime_parameters={"lang": "ja"},
                    )
                ],
                "maximum_iterations": 1,
            }
        )
    )

    assert called["provider"] == "provider"
    assert called["tool_name"] == "lookup"
    assert called["parameters"]["lang"] == "ja"
    assert called["parameters"]["q"] == "hello"

    assert any(
        getattr(message, "type", None)
        == strategy_module.ToolInvokeMessage.MessageType.IMAGE
        for message in messages
    )
    text_messages = [
        m["text"]
        for m in messages
        if isinstance(m, dict) and m.get("kind") == "text"
    ]
    assert "image generated and sent to user." in "\n".join(text_messages)


def test_invoke_tool_blob_message_path(strategy_module: Any) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    tool_call = strategy_module.AssistantPromptMessage.ToolCall(
        id="call_blob",
        type="function",
        function=strategy_module.AssistantPromptMessage.ToolCall.ToolCallFunction(
            name="lookup",
            arguments='{"q":"hello"}',
        ),
    )
    llm_result = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="need file",
            tool_calls=[tool_call],
        ),
        usage=None,
    )
    llm = _SequenceLLM([llm_result])
    blob_response = types.SimpleNamespace(
        type=strategy_module.ToolInvokeMessage.MessageType.BLOB,
        message=types.SimpleNamespace(data=b"blob-data"),
    )
    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=lambda **_: [blob_response]),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [_build_tool_entity()],
                "maximum_iterations": 1,
            }
        )
    )

    assert any(
        getattr(message, "type", None)
        == strategy_module.ToolInvokeMessage.MessageType.BLOB
        for message in messages
    )
    text_messages = [
        m["text"]
        for m in messages
        if isinstance(m, dict) and m.get("kind") == "text"
    ]
    assert "Generated file ..." in "\n".join(text_messages)


def test_resolve_safe_local_file_path_rejects_path_traversal(
    strategy_module: Any,
) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    assert strategy._resolve_safe_local_file_path("/files/../etc/passwd") is None


def test_read_local_file_for_blob_rejects_oversized_file(
    strategy_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    monkeypatch.setattr(strategy, "_resolve_safe_local_file_path", lambda _: "/tmp/fake")
    monkeypatch.setattr(strategy_module.os.path, "exists", lambda _: True)
    monkeypatch.setattr(
        strategy_module.os.path,
        "getsize",
        lambda _: strategy._max_blob_file_bytes() + 1,
    )

    with pytest.raises(ValueError, match="too large"):
        strategy._read_local_file_for_blob("/files/huge.bin")


def test_invoke_image_blob_conversion_error_masks_internal_details(
    strategy_module: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    tool_call = strategy_module.AssistantPromptMessage.ToolCall(
        id="call_img_err",
        type="function",
        function=strategy_module.AssistantPromptMessage.ToolCall.ToolCallFunction(
            name="lookup",
            arguments='{"q":"hello"}',
        ),
    )
    llm_result = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="need image",
            tool_calls=[tool_call],
        ),
        usage=None,
    )
    llm = _SequenceLLM([llm_result])
    image_response = types.SimpleNamespace(
        type=strategy_module.ToolInvokeMessage.MessageType.IMAGE,
        message=strategy_module.ToolInvokeMessage.TextMessage(text="/files/a.png"),
    )

    def _raise(_: str) -> tuple[bytes, str] | None:
        raise RuntimeError("internal path /etc/secret")

    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=lambda **_: [image_response]),
    )
    monkeypatch.setattr(strategy, "_read_local_file_for_blob", _raise)

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [_build_tool_entity()],
                "maximum_iterations": 1,
            }
        )
    )

    text_messages = [
        m["text"]
        for m in messages
        if isinstance(m, dict) and m.get("kind") == "text"
    ]
    rendered = "\n".join(text_messages)
    assert "Failed to process generated image file." in rendered
    assert "internal path /etc/secret" not in rendered


def test_invoke_tool_exception_masks_internal_details(
    strategy_module: Any,
) -> None:
    strategy = strategy_module.GPT5FunctionCallingStrategy()
    tool_call = strategy_module.AssistantPromptMessage.ToolCall(
        id="call_tool_error",
        type="function",
        function=strategy_module.AssistantPromptMessage.ToolCall.ToolCallFunction(
            name="lookup",
            arguments='{"q":"hello"}',
        ),
    )
    llm_result = strategy_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=strategy_module.AssistantPromptMessage(
            content="need tool",
            tool_calls=[tool_call],
        ),
        usage=None,
    )
    llm = _SequenceLLM([llm_result])

    def _tool_invoke(**_: Any) -> list[Any]:
        raise RuntimeError("internal error path=/srv/secret")

    strategy.session = types.SimpleNamespace(
        model=types.SimpleNamespace(llm=llm),
        tool=types.SimpleNamespace(invoke=_tool_invoke),
    )

    messages = list(
        strategy._invoke(
            {
                "query": "hello",
                "instruction": "",
                "model": _build_model_config(strategy_module, stream=False),
                "tools": [_build_tool_entity()],
                "maximum_iterations": 1,
            }
        )
    )

    text_messages = [
        m["text"]
        for m in messages
        if isinstance(m, dict) and m.get("kind") == "text"
    ]
    rendered = "\n".join(text_messages)
    assert "tool invoke error: failed to execute tool" in rendered
    assert "internal error path=/srv/secret" not in rendered
