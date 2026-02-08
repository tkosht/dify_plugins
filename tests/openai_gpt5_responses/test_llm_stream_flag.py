from __future__ import annotations

import importlib
import sys
import types
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest


def _install_openai_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    openai_mod = types.ModuleType("openai")

    class APIError(Exception): ...

    class APIConnectionError(APIError): ...

    class APIStatusError(APIError): ...

    class APITimeoutError(APIError): ...

    class AuthenticationError(APIError): ...

    class PermissionDeniedError(APIError): ...

    class RateLimitError(APIError): ...

    class InternalServerError(APIError): ...

    class BadRequestError(APIError): ...

    class NotFoundError(APIError): ...

    class UnprocessableEntityError(APIError): ...

    class _ResponsesClient:
        def create(self, **_: Any) -> Any:
            return types.SimpleNamespace(
                model="gpt-5.2",
                usage=None,
                output_text="ok",
                output=[],
            )

    class OpenAI:
        def __init__(self, **_: Any) -> None:
            self.responses = _ResponsesClient()

    openai_mod.APIError = APIError
    openai_mod.APIConnectionError = APIConnectionError
    openai_mod.APIStatusError = APIStatusError
    openai_mod.APITimeoutError = APITimeoutError
    openai_mod.AuthenticationError = AuthenticationError
    openai_mod.PermissionDeniedError = PermissionDeniedError
    openai_mod.RateLimitError = RateLimitError
    openai_mod.InternalServerError = InternalServerError
    openai_mod.BadRequestError = BadRequestError
    openai_mod.NotFoundError = NotFoundError
    openai_mod.UnprocessableEntityError = UnprocessableEntityError
    openai_mod.OpenAI = OpenAI
    monkeypatch.setitem(sys.modules, "openai", openai_mod)


def _install_dify_plugin_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    dify_plugin_mod = types.ModuleType("dify_plugin")

    class LargeLanguageModel:
        def timing_context(self) -> Any:
            class _Ctx:
                def __enter__(self) -> None:
                    return None

                def __exit__(
                    self,
                    exc_type: type[BaseException] | None,
                    exc: BaseException | None,
                    tb: Any,
                ) -> bool:
                    return False

            return _Ctx()

        def _validate_and_filter_model_parameters(
            self, **kwargs: Any
        ) -> dict[str, Any]:
            return dict(kwargs["model_parameters"])

        def _transform_invoke_error(self, exc: Exception) -> Exception:
            return exc

        def _calc_response_usage(self, **_: Any) -> None:
            return None

        def _get_num_tokens_by_gpt2(self, text: str) -> int:
            return len(text)

    dify_plugin_mod.LargeLanguageModel = LargeLanguageModel

    entities_mod = types.ModuleType("dify_plugin.entities")
    model_mod = types.ModuleType("dify_plugin.entities.model")
    model_llm_mod = types.ModuleType("dify_plugin.entities.model.llm")
    model_message_mod = types.ModuleType("dify_plugin.entities.model.message")
    errors_mod = types.ModuleType("dify_plugin.errors")
    errors_model_mod = types.ModuleType("dify_plugin.errors.model")

    @dataclass
    class LLMResult:
        model: str
        prompt_messages: list[Any]
        message: Any
        usage: Any
        system_fingerprint: Any

    @dataclass
    class LLMResultChunkDelta:
        index: int
        message: Any
        finish_reason: str
        usage: Any

    @dataclass
    class LLMResultChunk:
        model: str
        prompt_messages: list[Any]
        system_fingerprint: Any
        delta: LLMResultChunkDelta

    @dataclass
    class AssistantPromptMessage:
        content: Any
        tool_calls: list[Any]

        @dataclass
        class ToolCall:
            @dataclass
            class ToolCallFunction:
                name: str
                arguments: str

            id: str
            type: str
            function: AssistantPromptMessage.ToolCall.ToolCallFunction

    class PromptMessage: ...

    class PromptMessageTool: ...

    class CredentialsValidateFailedError(Exception): ...

    class InvokeError(Exception): ...

    model_llm_mod.LLMResult = LLMResult
    model_llm_mod.LLMResultChunk = LLMResultChunk
    model_llm_mod.LLMResultChunkDelta = LLMResultChunkDelta
    model_message_mod.AssistantPromptMessage = AssistantPromptMessage
    model_message_mod.PromptMessage = PromptMessage
    model_message_mod.PromptMessageTool = PromptMessageTool
    errors_model_mod.CredentialsValidateFailedError = (
        CredentialsValidateFailedError
    )
    errors_model_mod.InvokeError = InvokeError

    monkeypatch.setitem(sys.modules, "dify_plugin", dify_plugin_mod)
    monkeypatch.setitem(sys.modules, "dify_plugin.entities", entities_mod)
    monkeypatch.setitem(sys.modules, "dify_plugin.entities.model", model_mod)
    monkeypatch.setitem(
        sys.modules, "dify_plugin.entities.model.llm", model_llm_mod
    )
    monkeypatch.setitem(
        sys.modules, "dify_plugin.entities.model.message", model_message_mod
    )
    monkeypatch.setitem(sys.modules, "dify_plugin.errors", errors_mod)
    monkeypatch.setitem(
        sys.modules, "dify_plugin.errors.model", errors_model_mod
    )


@pytest.fixture
def llm_module(monkeypatch: pytest.MonkeyPatch) -> Any:
    _install_openai_stub(monkeypatch)
    _install_dify_plugin_stub(monkeypatch)
    sys.modules.pop("app.openai_gpt5_responses.models.llm.llm", None)
    importlib.invalidate_caches()
    return importlib.import_module("app.openai_gpt5_responses.models.llm.llm")


def _build_llm_result(llm_module: Any) -> Any:
    assistant = llm_module.AssistantPromptMessage(content="ok", tool_calls=[])
    return llm_module.LLMResult(
        model="gpt-5.2",
        prompt_messages=[],
        message=assistant,
        usage=None,
        system_fingerprint=None,
    )


def test_invoke_disable_stream_string_returns_blocking_result(
    llm_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = llm_module.OpenAIGPT5LargeLanguageModel()
    llm_result = _build_llm_result(llm_module)

    monkeypatch.setattr(
        model,
        "_normalize_parameters",
        lambda **_: {"enable_stream": "false"},
    )
    monkeypatch.setattr(
        model, "_to_credential_kwargs", lambda _credentials: {}
    )
    monkeypatch.setattr(model, "_to_llm_result", lambda **_: llm_result)

    result = model._invoke(
        model="gpt-5.2",
        credentials={},
        prompt_messages=[],
        model_parameters={"enable_stream": "false"},
        tools=[],
        stream=True,
    )

    assert result is llm_result


def test_invoke_enable_stream_string_returns_generator(
    llm_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = llm_module.OpenAIGPT5LargeLanguageModel()
    llm_result = _build_llm_result(llm_module)
    expected_chunk = llm_module.LLMResultChunk(
        model="gpt-5.2",
        prompt_messages=[],
        system_fingerprint=None,
        delta=llm_module.LLMResultChunkDelta(
            index=0,
            message=llm_result.message,
            finish_reason="stop",
            usage=None,
        ),
    )

    monkeypatch.setattr(
        model,
        "_normalize_parameters",
        lambda **_: {"enable_stream": "true"},
    )
    monkeypatch.setattr(
        model, "_to_credential_kwargs", lambda _credentials: {}
    )
    monkeypatch.setattr(model, "_to_llm_result", lambda **_: llm_result)

    def _streaming_response(
        _llm_result: Any, _prompt_messages: list[Any]
    ) -> Any:
        yield expected_chunk

    monkeypatch.setattr(model, "_as_single_chunk_stream", _streaming_response)

    result = model._invoke(
        model="gpt-5.2",
        credentials={},
        prompt_messages=[],
        model_parameters={"enable_stream": "true"},
        tools=[],
        stream=True,
    )

    assert isinstance(result, Generator)
    assert list(result) == [expected_chunk]


def test_safe_int_and_credential_kwargs_bounds(llm_module: Any) -> None:
    model = llm_module.OpenAIGPT5LargeLanguageModel()

    assert model._safe_int("10", 1) == 10
    assert model._safe_int("not-int", 7) == 7

    kwargs = model._to_credential_kwargs(
        {
            "openai_api_key": "k",
            "openai_api_base": "https://api.openai.com",
            "request_timeout_seconds": "9999",
            "max_retries": "99",
            "openai_organization": " org ",
        }
    )
    assert kwargs["timeout"] == 900.0
    assert kwargs["max_retries"] == 5
    assert kwargs["base_url"] == "https://api.openai.com/v1"
    assert kwargs["organization"] == "org"


def test_get_num_tokens_joins_prompt_content(
    llm_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = llm_module.OpenAIGPT5LargeLanguageModel()
    captured: dict[str, str] = {}

    def _count(text: str) -> int:
        captured["text"] = text
        return 42

    monkeypatch.setattr(model, "_get_num_tokens_by_gpt2", _count)
    messages = [
        types.SimpleNamespace(content="a"),
        types.SimpleNamespace(content="b"),
        types.SimpleNamespace(content=None),
    ]

    assert model.get_num_tokens("gpt-5.2", {}, messages) == 42
    assert captured["text"] == "a\nb"


def test_normalize_parameters_fallback_after_validation_error(
    llm_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = llm_module.OpenAIGPT5LargeLanguageModel()

    def _raise_value_error(**_: Any) -> dict[str, Any]:
        raise ValueError("bad")

    monkeypatch.setattr(
        model, "_validate_and_filter_model_parameters", _raise_value_error
    )
    normalized = model._normalize_parameters(
        model="gpt-5.2",
        credentials={},
        model_parameters={
            "max_output_tokens": 10,
            "enable_stream": True,
            "unknown": "x",
        },
    )

    assert normalized == {"max_output_tokens": 10, "enable_stream": True}


def test_to_llm_result_converts_usage_and_tool_calls(
    llm_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = llm_module.OpenAIGPT5LargeLanguageModel()
    usage_marker = {"ok": True}
    monkeypatch.setattr(
        model, "_calc_response_usage", lambda **_: usage_marker
    )
    response = types.SimpleNamespace(
        model="gpt-5.2",
        output_text="assistant answer",
        output=[
            types.SimpleNamespace(
                type="function_call",
                call_id="call_1",
                name="lookup",
                arguments={"q": "hello"},
            )
        ],
        usage=types.SimpleNamespace(input_tokens=3, output_tokens=5),
    )

    llm_result = model._to_llm_result(
        model="gpt-5.2",
        credentials={},
        prompt_messages=[],
        response=response,
    )

    assert llm_result.message.content == "assistant answer"
    assert llm_result.message.tool_calls[0].function.name == "lookup"
    assert (
        llm_result.message.tool_calls[0].function.arguments == '{"q": "hello"}'
    )
    assert llm_result.usage is usage_marker


def test_validate_credentials_requires_api_key(llm_module: Any) -> None:
    model = llm_module.OpenAIGPT5LargeLanguageModel()

    with pytest.raises(llm_module.CredentialsValidateFailedError):
        model.validate_credentials("gpt-5.2", {})


def test_validate_credentials_calls_responses_create(
    llm_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    class _Responses:
        def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return types.SimpleNamespace()

    class _OpenAI:
        def __init__(self, **_: Any) -> None:
            self.responses = _Responses()

    monkeypatch.setattr(llm_module, "OpenAI", _OpenAI)
    model = llm_module.OpenAIGPT5LargeLanguageModel()
    model.validate_credentials("gpt-5.2", {"openai_api_key": "k"})

    assert captured["model"] == "gpt-5.2"
    assert captured["store"] is False


def test_invoke_sets_user_and_stop_truncation(
    llm_module: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    class _Responses:
        def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return types.SimpleNamespace(
                model="gpt-5.2", usage=None, output_text="ok", output=[]
            )

    class _OpenAI:
        def __init__(self, **_: Any) -> None:
            self.responses = _Responses()

    model = llm_module.OpenAIGPT5LargeLanguageModel()
    llm_result = _build_llm_result(llm_module)
    monkeypatch.setattr(llm_module, "OpenAI", _OpenAI)
    monkeypatch.setattr(
        model, "_normalize_parameters", lambda **_: {"enable_stream": False}
    )
    monkeypatch.setattr(
        model, "_to_credential_kwargs", lambda _credentials: {}
    )
    monkeypatch.setattr(model, "_to_llm_result", lambda **_: llm_result)

    result = model._invoke(
        model="gpt-5.2",
        credentials={},
        prompt_messages=[],
        model_parameters={"enable_stream": False},
        tools=[],
        stream=True,
        user="user-id",
        stop=["END"],
    )

    assert result is llm_result
    assert captured["user"] == "user-id"
    assert captured["truncation"] == "disabled"
