from __future__ import annotations

import importlib.util
import os
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
        def generate_content(self, prompt, **_kwargs):
            captured["prompt"] = prompt
            return types.SimpleNamespace(text='{"open_access": ["success"], "not_open_access": []}')

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

    assert result == {"open_access": ["success"], "not_open_access": []}
    assert dummy.configured_key == "api-key"
    assert dummy.model_name == "my-model"
    assert captured["prompt"] == "do things"


def test_call_gemini_requires_text(monkeypatch):
    class DummyModel:
        def generate_content(self, prompt, **_kwargs):  # pragma: no cover - trivial
            return types.SimpleNamespace(text="")

    class DummyGenAI:
        def configure(self, *_args, **_kwargs):
            pass

        def GenerativeModel(self, *_args, **_kwargs):
            return DummyModel()

    monkeypatch.setattr(gh, "_resolve_api_key", lambda *_args, **_kwargs: "key")

    with pytest.raises(RuntimeError, match="did not contain any text"):
        gh.call_gemini("prompt", genai_module=DummyGenAI())


def test_call_gemini_validates_json(monkeypatch):
    class DummyModel:
        def generate_content(self, prompt, **_kwargs):  # pragma: no cover - trivial
            return types.SimpleNamespace(text="not json")

    class DummyGenAI:
        def configure(self, *_args, **_kwargs):
            pass

        def GenerativeModel(self, *_args, **_kwargs):
            return DummyModel()

    monkeypatch.setattr(gh, "_resolve_api_key", lambda *_args, **_kwargs: "key")

    with pytest.raises(RuntimeError, match="not valid JSON"):
        gh.call_gemini("prompt", genai_module=DummyGenAI())


def test_call_gemini_best_effort_extracts_embedded_json(monkeypatch):
    class DummyModel:
        def generate_content(self, prompt, **_kwargs):  # pragma: no cover - trivial
            return types.SimpleNamespace(text="Here you go: {\"open_access\": [\"A\"], \"not_open_access\": []} Thanks!")

    class DummyGenAI:
        def configure(self, *_args, **_kwargs):
            pass

        def GenerativeModel(self, *_args, **_kwargs):
            return DummyModel()

    monkeypatch.setattr(gh, "_resolve_api_key", lambda *_args, **_kwargs: "key")

    result = gh.call_gemini("prompt", genai_module=DummyGenAI(), best_effort=True)

    assert result == {"open_access": ["A"], "not_open_access": []}


def test_harvest_with_gemini_builds_prompt(monkeypatch):
    monkeypatch.setattr(gh, "load_prompts", lambda: {"harvest_publications": "Run {{ url }}"})
    captured = {}

    def fake_call(prompt: str, **_kwargs):
        captured["prompt"] = prompt
        return {"open_access": [], "not_open_access": []}

    monkeypatch.setattr(gh, "call_gemini", fake_call)

    result = gh.harvest_with_gemini("https://harvest.me")

    assert result == {"open_access": [], "not_open_access": []}
    assert captured["prompt"] == "Run https://harvest.me"


def test_load_source_urls_skips_header_and_blank_lines(tmp_path):
    sources = tmp_path / "sources.csv"
    sources.write_text("Website\n\nhttps://first.example.com\n  \nhttps://second.example.com  \n", encoding="utf-8")

    urls = gh.load_source_urls(sources)

    assert urls == ["https://first.example.com", "https://second.example.com"]


def test_harvest_multiple_calls_each_url(monkeypatch):
    urls = ["https://one", "https://two"]
    responses = {
        "https://one": {"open_access": ["1"], "not_open_access": []},
        "https://two": {"open_access": [], "not_open_access": ["2"]},
    }
    calls = []

    def fake_harvest(url: str, **_kwargs) -> str:
        calls.append(url)
        return responses[url]

    monkeypatch.setattr(gh, "harvest_with_gemini", fake_harvest)

    result = gh.harvest_multiple(urls)

    assert calls == urls
    assert result == [(url, responses[url]) for url in urls]


def test_validate_harvest_payload_rejects_bad_shapes():
    with pytest.raises(RuntimeError, match="JSON object"):
        gh._validate_harvest_payload([])

    with pytest.raises(RuntimeError, match="open_access.*list"):
        gh._validate_harvest_payload({"open_access": "oops", "not_open_access": []})

    with pytest.raises(RuntimeError, match="strings"):
        gh._validate_harvest_payload({"open_access": [1], "not_open_access": []})
def test_harvest_specific_url_returns_real_papers():
    url = "https://www.maxiv.lu.se/science/publications/"

    result = gh.harvest_with_gemini(url, best_effort=True)

    assert "open_access" in result
    assert isinstance(result["open_access"], list)
    assert len(result["open_access"]) >= 1
    assert all(isinstance(item, str) and item.strip() for item in result["open_access"])
    print("Open access publications found:")
    for item in result["open_access"]:
        print(f"- {item}")
