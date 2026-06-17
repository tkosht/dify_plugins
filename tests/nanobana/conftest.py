from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from typing import Any

import pytest

BASE_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = BASE_DIR / "app" / "nanobana"


def install_dify_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    dify_plugin_mod = types.ModuleType("dify_plugin")
    entities_mod = types.ModuleType("dify_plugin.entities")
    entities_tool_mod = types.ModuleType("dify_plugin.entities.tool")
    errors_mod = types.ModuleType("dify_plugin.errors")
    errors_tool_mod = types.ModuleType("dify_plugin.errors.tool")

    class ToolProvider:
        pass

    class Tool:
        def create_text_message(self, text: str) -> dict[str, Any]:
            return {"type": "text", "text": text}

        def create_blob_message(
            self, blob: bytes, meta: dict[str, Any] | None = None
        ) -> dict[str, Any]:
            return {"type": "blob", "blob": blob, "meta": meta or {}}

    class ToolInvokeMessage:
        pass

    class ToolProviderCredentialValidationError(Exception):
        pass

    dify_plugin_mod.Tool = Tool
    dify_plugin_mod.ToolProvider = ToolProvider
    entities_tool_mod.ToolInvokeMessage = ToolInvokeMessage
    errors_tool_mod.ToolProviderCredentialValidationError = (
        ToolProviderCredentialValidationError
    )

    monkeypatch.setitem(sys.modules, "dify_plugin", dify_plugin_mod)
    monkeypatch.setitem(sys.modules, "dify_plugin.entities", entities_mod)
    monkeypatch.setitem(
        sys.modules, "dify_plugin.entities.tool", entities_tool_mod
    )
    monkeypatch.setitem(sys.modules, "dify_plugin.errors", errors_mod)
    monkeypatch.setitem(
        sys.modules, "dify_plugin.errors.tool", errors_tool_mod
    )


@pytest.fixture
def nanobana_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    install_dify_stubs(monkeypatch)
    monkeypatch.syspath_prepend(str(PLUGIN_DIR))
    for module_name in [
        "internal.auth",
        "provider.nanobana",
        "tools.nanobana",
    ]:
        sys.modules.pop(module_name, None)
    importlib.invalidate_caches()
