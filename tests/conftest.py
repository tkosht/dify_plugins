from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest


def _is_pip_audit_gate_only_run(config: pytest.Config) -> bool:
    selected_paths = {
        Path(arg.split("::", maxsplit=1)[0]).as_posix() for arg in config.args
    }
    return selected_paths == {"tests/test_pip_audit_gate.py"}


@pytest.hookimpl(wrapper=True, trylast=True)
def pytest_runtestloop(session: pytest.Session) -> Any:
    result = yield
    if _is_pip_audit_gate_only_run(session.config):
        cov_plugin = session.config.pluginmanager.getplugin("_cov")
        if cov_plugin is not None:
            cov_plugin.options.cov_fail_under = None
            cov_plugin.options.cov_report = []
    return result
