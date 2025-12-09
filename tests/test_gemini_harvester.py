from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "gemini_harvester" / "gemini_harvester.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("gemini_harvester", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("gemini_harvester", module)
    assert spec.loader is not None  # for type checkers
    spec.loader.exec_module(module)
    return module


gh = _load_module()


def test_call_gemini_returns_stdout(monkeypatch):
    recorded = {}

    class DummyProc:
        returncode = 0
        stdout = " success \n"
        stderr = ""

    def fake_run(args, input, text, capture_output, check):
        recorded["args"] = args
        recorded["input"] = input
        assert text is True and capture_output is True and check is False
        return DummyProc()

    monkeypatch.setattr(gh.subprocess, "run", fake_run)

    output = gh.call_gemini("do things")

    assert recorded["args"] == ["gemini"]
    assert recorded["input"] == "do things"
    assert output == "success"


def test_call_gemini_raises_on_failure(monkeypatch):
    class DummyProc:
        returncode = 42
        stdout = ""
        stderr = "boom"

    def fake_run(*_args, **_kwargs):
        return DummyProc()

    monkeypatch.setattr(gh.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc:
        gh.call_gemini("bad call")

    assert "gemini CLI failed" in str(exc.value)
    assert "boom" in str(exc.value)


def test_harvest_with_gemini_builds_prompt(monkeypatch):
    monkeypatch.setattr(gh, "load_prompts", lambda: {"harvest_publications": "Run {{ url }}"})
    captured = {}

    def fake_call(prompt: str) -> str:
        captured["prompt"] = prompt
        return "{\"result\": []}"

    monkeypatch.setattr(gh, "call_gemini", fake_call)

    result = gh.harvest_with_gemini("https://harvest.me")

    assert result == "{\"result\": []}"
    assert captured["prompt"] == "Run https://harvest.me"
