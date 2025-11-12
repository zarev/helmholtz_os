"""Agentic browser that triages beamline sources with the help of an LLM."""
from __future__ import annotations

import argparse
import json
import os
import textwrap
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable, Iterable, List, Optional, Protocol, Sequence

import requests

import web_scraper

USER_AGENT = "HelmholtzAgent/0.1 (+https://github.com/helmholtz-os)"
DEFAULT_SYSTEM_PROMPT = """You are a meticulous research assistant.
Given a snippet of a publications page decide if it lists open access or open source publications.
Respond with compact JSON."""
PROMPT_TEMPLATE = textwrap.dedent(
    """
    You are checking whether {url} lists open-access or open-source publications.
    Review the provided text and respond with JSON containing:
      - decision: YES if the page clearly lists relevant publications, otherwise NO.
      - reason: short justification referencing the snippet.
      - publications: array of publication titles or links that look open access/source (max 3 entries).
    Text snippet:
    ---
    {snippet}
    ---
    JSON:
    """
)


class LLMClient(Protocol):
    """Minimal protocol for LLM clients used by the agentic browser."""

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> str:
        ...


class OpenAIChatLLM:
    """Thin wrapper over OpenAI's chat completions endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
    ) -> None:
        if not api_key:
            raise ValueError("An API key is required to use the OpenAIChatLLM client.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 400,
    ) -> str:
        messages: List[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        try:
            choices = data.get("choices") or []
        except AttributeError as exc:  # pragma: no cover - defensive guard
            raise ValueError(f"Unexpected response payload: {data}") from exc
        if not choices:
            raise ValueError("OpenAI response did not include choices")
        message = choices[0].get("message") or {}
        content = message.get("content") or ""
        if not isinstance(content, str):
            raise ValueError("OpenAI response did not contain textual content")
        return content.strip()


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []

    def handle_data(self, data: str) -> None:  # pragma: no cover - exercised indirectly
        text = data.strip()
        if text:
            self._chunks.append(text)

    def get_text(self) -> str:
        return " \n".join(self._chunks)


def html_to_text(html: str) -> str:
    """Convert HTML into a whitespace-normalised text snippet."""

    stripper = _HTMLStripper()
    stripper.feed(html)
    return " ".join(stripper.get_text().split())


@dataclass(frozen=True)
class BrowserDecision:
    decision: str
    reason: str
    publications: List[str]


@dataclass(frozen=True)
class BrowserFinding:
    source: web_scraper.Source
    decision: str
    reason: str
    publications: List[str]
    raw_response: str


def parse_llm_response(raw: str) -> BrowserDecision:
    """Parse the JSON-like response returned by the LLM."""

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        decision = "UNKNOWN"
        reason = raw.strip() or "LLM response was empty"
        return BrowserDecision(decision=decision, reason=reason, publications=[])

    decision = str(payload.get("decision", "UNKNOWN")).strip().upper() or "UNKNOWN"
    if decision not in {"YES", "NO"}:
        decision = "UNKNOWN"
    reason = str(payload.get("reason", "")) or "No reason provided"
    publications_raw = payload.get("publications") or []
    publications: List[str] = []
    if isinstance(publications_raw, str):
        publications = [publications_raw]
    elif isinstance(publications_raw, Iterable):
        for entry in publications_raw:
            if not entry:
                continue
            publications.append(str(entry))
    return BrowserDecision(decision=decision, reason=reason, publications=publications[:3])


class AgenticBrowser:
    """Simple agent that fetches sources and asks an LLM to triage them."""

    def __init__(
        self,
        sources: Sequence[web_scraper.Source],
        llm_client: LLMClient,
        *,
        fetcher: Optional[Callable[[str], str]] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        snippet_chars: int = 2000,
    ) -> None:
        self.sources = list(sources)
        self.llm_client = llm_client
        self.fetcher = fetcher or self._default_fetcher
        self.system_prompt = system_prompt
        self.snippet_chars = snippet_chars

    def _default_fetcher(self, url: str) -> str:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        return response.text

    def inspect_source(self, source: web_scraper.Source) -> BrowserFinding:
        html = self.fetcher(source.url)
        snippet = html_to_text(html)[: self.snippet_chars]
        prompt = PROMPT_TEMPLATE.format(url=source.url, snippet=snippet)
        raw = self.llm_client.complete(
            prompt,
            system_prompt=self.system_prompt,
            temperature=0.1,
            max_tokens=400,
        )
        decision = parse_llm_response(raw)
        return BrowserFinding(
            source=source,
            decision=decision.decision,
            reason=decision.reason,
            publications=decision.publications,
            raw_response=raw,
        )

    def run(self, *, limit: Optional[int] = None) -> List[BrowserFinding]:
        findings: List[BrowserFinding] = []
        for source in self.sources[: limit or None]:
            try:
                findings.append(self.inspect_source(source))
            except requests.RequestException as exc:
                findings.append(
                    BrowserFinding(
                        source=source,
                        decision="ERROR",
                        reason=str(exc),
                        publications=[],
                        raw_response="",
                    )
                )
        return findings


def _load_sources(path: str | os.PathLike[str]) -> List[web_scraper.Source]:
    return web_scraper.load_sources(path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Agentic browser for Helmholtz sources")
    parser.add_argument("--sources", default="data/sources.csv", help="Path to sources.csv")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Limit the number of sources to inspect (default: 5)",
    )
    parser.add_argument("--model", default=os.getenv("LLM_MODEL", "gpt-4o-mini"))
    args = parser.parse_args(argv)

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        parser.error("Set LLM_API_KEY or OPENAI_API_KEY to run the agentic browser.")

    sources = _load_sources(args.sources)
    llm_client = OpenAIChatLLM(api_key=api_key, model=args.model)
    browser = AgenticBrowser(sources, llm_client)
    findings = browser.run(limit=args.limit)

    for finding in findings:
        print(f"[{finding.decision}] {finding.source.url}")
        print(f"  Reason: {finding.reason}")
        if finding.publications:
            for entry in finding.publications:
                print(f"    - {entry}")
        print()

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
