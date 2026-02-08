from __future__ import annotations

import importlib
import sys
import types
from typing import Any

from tests.gpt5_agent_strategies.test_strategy_invoke_paths import (
    _install_strategy_dify_stub,
)


def _install_main_provider_stub() -> None:
    dify_plugin_mod = types.ModuleType("dify_plugin")
    interfaces_agent_mod = types.ModuleType("dify_plugin.interfaces.agent")

    class DifyPluginEnv:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    class Plugin:
        def __init__(self, env: DifyPluginEnv) -> None:
            self.env = env

        def run(self) -> None:
            return None

    class AgentProvider:
        pass

    dify_plugin_mod.DifyPluginEnv = DifyPluginEnv
    dify_plugin_mod.Plugin = Plugin
    interfaces_agent_mod.AgentProvider = AgentProvider

    sys.modules["dify_plugin"] = dify_plugin_mod
    sys.modules["dify_plugin.interfaces.agent"] = interfaces_agent_mod


def test_agent_main_and_provider_entrypoint() -> None:
    _install_main_provider_stub()
    sys.modules.pop("app.gpt5_agent_strategies.main", None)
    sys.modules.pop("app.gpt5_agent_strategies.provider.gpt5_agent", None)

    main_module = importlib.import_module("app.gpt5_agent_strategies.main")
    provider_module = importlib.import_module(
        "app.gpt5_agent_strategies.provider.gpt5_agent"
    )

    assert main_module.plugin.env.kwargs["MAX_REQUEST_TIMEOUT"] == 240
    assert provider_module.GPT5AgentProvider.__mro__[1].__name__ == "AgentProvider"


def test_gpt5_react_reuses_function_calling_strategy(monkeypatch: Any) -> None:
    _install_strategy_dify_stub(monkeypatch)
    sys.modules.pop("app.gpt5_agent_strategies.strategies.gpt5_react", None)

    module = importlib.import_module("app.gpt5_agent_strategies.strategies.gpt5_react")

    assert module.GPT5ReActParams.__mro__[1].__name__ == "GPT5FunctionCallingParams"
    assert module.GPT5ReActStrategy.__mro__[1].__name__ == "GPT5FunctionCallingStrategy"
