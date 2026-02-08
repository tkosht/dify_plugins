from __future__ import annotations

import importlib
import sys
import types
from typing import Any


def _install_dify_plugin_stub() -> None:
    dify_plugin_mod = types.ModuleType("dify_plugin")

    class DifyPluginEnv:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    class Plugin:
        def __init__(self, env: DifyPluginEnv) -> None:
            self.env = env

        def run(self) -> None:
            return None

    dify_plugin_mod.DifyPluginEnv = DifyPluginEnv
    dify_plugin_mod.Plugin = Plugin
    sys.modules["dify_plugin"] = dify_plugin_mod


def test_openai_main_plugin_entrypoint() -> None:
    _install_dify_plugin_stub()
    sys.modules.pop("app.openai_gpt5_responses.main", None)

    module = importlib.import_module("app.openai_gpt5_responses.main")
    assert module.plugin.env.kwargs["MAX_REQUEST_TIMEOUT"] == 240


def test_format_runtime_error() -> None:
    module = importlib.import_module("app.openai_gpt5_responses.internal.errors")
    assert module.format_runtime_error("boom", category="tool") == "[tool] boom"
