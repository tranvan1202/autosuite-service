# tests/unit/service/executor/test_scheduler_spawn.py

from __future__ import annotations

import sys

import pytest

from service.executor import scheduler


class _Proc:
    def __init__(self, pid: int) -> None:
        self.pid = pid


pytestmark = pytest.mark.unit


def test_spawn_worker_constructs_expected_command(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_popen(cmd: list[str], close_fds: bool) -> _Proc:
        # WHY: Intercept subprocess invocation to assert CLI contract without spawning processes.
        captured["cmd"] = cmd
        captured["close_fds"] = close_fds
        return _Proc(pid=4321)

    monkeypatch.setattr(scheduler.subprocess, "Popen", _fake_popen)

    pid = scheduler._spawn_worker("job-42")

    assert pid == 4321
    assert captured["close_fds"] is True
    assert captured["cmd"] == [
        sys.executable,
        "-m",
        "service.executor.worker",
        "--job-id",
        "job-42",
    ]
