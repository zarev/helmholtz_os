from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

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


def test_resolve_api_key_prefers_env_over_file(monkeypatch, tmp_path):
    cfg = tmp_path / "gemini-cli.toml"
    cfg.write_text('token = "file-key"', encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "env-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = gh._resolve_api_key(cfg)

    assert result == "env-key"


def test_resolve_api_key_reads_cli_config(monkeypatch, tmp_path):
    cfg = tmp_path / "gemini-cli.toml"
    cfg.write_text('token = "file-key"', encoding="utf-8")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    result = gh._resolve_api_key(cfg)

    assert result == "file-key"


def test_call_gemini_invokes_generative_model(monkeypatch):
    captured = {}

    class DummyModel:
        def generate_content(self, prompt):
            captured["prompt"] = prompt
            return types.SimpleNamespace(text=" success ")

    class DummyGenAI:
        def __init__(self):
            self.configured_key = None
            self.model_name = None

        def configure(self, api_key):
            self.configured_key = api_key

        def GenerativeModel(self, name):
            self.model_name = name
            return DummyModel()

    dummy = DummyGenAI()
    monkeypatch.setenv("GEMINI_MODEL", "my-model")
    monkeypatch.setattr(gh, "_resolve_api_key", lambda *_args, **_kwargs: "api-key")

    result = gh.call_gemini("do things", genai_module=dummy)

    assert result == "success"
    assert dummy.configured_key == "api-key"
    assert dummy.model_name == "my-model"
    assert captured["prompt"] == "do things"


def test_call_gemini_requires_text(monkeypatch):
    class DummyModel:
        def generate_content(self, prompt):  # pragma: no cover - trivial
            return types.SimpleNamespace(text="")

    class DummyGenAI:
        def configure(self, *_args, **_kwargs):
            pass

        def GenerativeModel(self, *_args, **_kwargs):
            return DummyModel()

    monkeypatch.setattr(gh, "_resolve_api_key", lambda *_args, **_kwargs: "key")

    with pytest.raises(RuntimeError, match="did not contain any text"):
        gh.call_gemini("prompt", genai_module=DummyGenAI())


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
