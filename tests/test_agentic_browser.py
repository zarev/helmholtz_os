from pathlib import Path
import sys

import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import agentic_browser
import web_scraper


class DummyLLM:
    def __init__(self, response: str) -> None:
        self.response = response
        self.seen_prompts = []

    def complete(self, prompt: str, *, system_prompt=None, temperature=0.2, max_tokens=400):  # type: ignore[override]
        self.seen_prompts.append((system_prompt, prompt))
        return self.response


class DummyFetcher:
    def __init__(self, html: str) -> None:
        self.html = html
        self.seen = []

    def __call__(self, url: str) -> str:
        self.seen.append(url)
        return self.html


def test_html_to_text_removes_tags_and_normalises_whitespace():
    html = "<div>Open <b>access</b> paper <a href='https://example.com'>Link</a></div>"
    assert agentic_browser.html_to_text(html) == "Open access paper Link"


def test_parse_llm_response_handles_plain_text():
    decision = agentic_browser.parse_llm_response("No publications here")

    assert decision.decision == "UNKNOWN"
    assert "No publications" in decision.reason
    assert decision.publications == []


def test_agentic_browser_inspect_source_returns_structured_finding():
    llm = DummyLLM('{"decision": "YES", "reason": "Found list", "publications": ["Paper A", "Paper B"]}')
    fetcher = DummyFetcher("<html><body>Paper list with PDF links</body></html>")
    sources = [web_scraper.Source(url="https://example.com")] 
    browser = agentic_browser.AgenticBrowser(sources, llm_client=llm, fetcher=fetcher)

    finding = browser.inspect_source(sources[0])

    assert finding.decision == "YES"
    assert finding.publications == ["Paper A", "Paper B"]
    assert fetcher.seen == ["https://example.com"]
    assert llm.seen_prompts  # prompt captured


def test_agentic_browser_run_captures_request_errors():
    class ErrorFetcher:
        def __call__(self, url: str) -> str:  # pragma: no cover - simple stub
            raise requests.RequestException("boom")

    llm = DummyLLM('{}')
    sources = [web_scraper.Source(url="https://broken.example")]
    browser = agentic_browser.AgenticBrowser(sources, llm_client=llm, fetcher=ErrorFetcher())

    findings = browser.run()

    assert findings[0].decision == "ERROR"
    assert "boom" in findings[0].reason
