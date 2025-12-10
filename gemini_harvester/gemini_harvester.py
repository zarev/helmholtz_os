import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore

import google.generativeai as genai
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "gemini_harvester" / "gemini_prompts.yaml"
GEMINI_CONFIG_PATH = Path.home() / ".config" / "gemini-cli.toml"
DEFAULT_GEMINI_MODEL = "models/gemini-pro-latest"
DEFAULT_SOURCES_CSV = PROJECT_ROOT / "data" / "sources.csv"
HARVEST_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "open_access": {"type": "array", "items": {"type": "string"}},
        "not_open_access": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["open_access", "not_open_access"],
    "additionalProperties": False,
}


def load_prompts():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_prompt(template: str, url: str) -> str:
    return template.replace("{{ url }}", url)


def _load_cli_token(config_path: Path = GEMINI_CONFIG_PATH) -> Optional[str]:
    if not config_path.exists():
        return None

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None

    token = data.get("token")
    return token if isinstance(token, str) and token.strip() else None


def _resolve_api_key(config_path: Path = GEMINI_CONFIG_PATH) -> str:
    for env_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        value = os.environ.get(env_var)
        if value:
            return value

    token = _load_cli_token(config_path)
    if token:
        return token

    raise RuntimeError(
        "Gemini API key not found. Set GEMINI_API_KEY/GOOGLE_API_KEY or add a token to "
        f"{config_path}."
    )


def _validate_harvest_payload(payload: Any) -> Dict[str, List[str]]:
    if not isinstance(payload, dict):
        raise RuntimeError("Gemini response must be a JSON object")

    def _normalize_list(key: str) -> List[str]:
        value = payload.get(key)
        if not isinstance(value, list):
            raise RuntimeError(f"Gemini response field '{key}' must be a list")
        cleaned: List[str] = []
        for item in value:
            if not isinstance(item, str):
                raise RuntimeError(
                    f"Gemini response field '{key}' must contain only strings"
                )
            cleaned.append(item.strip())
        return cleaned

    return {
        "open_access": _normalize_list("open_access"),
        "not_open_access": _normalize_list("not_open_access"),
    }


def call_gemini(
    prompt: str,
    *,
    model: Optional[str] = None,
    genai_module=genai,
) -> Dict[str, List[str]]:
    api_key = _resolve_api_key()
    selected_model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    # Configure the SDK once per call to keep the function stateless.
    genai_module.configure(api_key=api_key)
    chat_model = genai_module.GenerativeModel(selected_model)
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": HARVEST_RESPONSE_SCHEMA,
    }
    response = chat_model.generate_content(prompt, generation_config=generation_config)

    text = getattr(response, "text", "")
    if not text:
        raise RuntimeError("Gemini response did not contain any text output")

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise RuntimeError("Gemini response was not valid JSON") from exc

    return _validate_harvest_payload(payload)


def harvest_with_gemini(url: str) -> Dict[str, List[str]]:
    prompts = load_prompts()
    template = prompts["harvest_publications"]
    prompt = build_prompt(template, url)
    print("Building better worlds...")
    return call_gemini(prompt)


def load_source_urls(csv_path: Path) -> List[str]:
    urls: List[str] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            candidate = row[0].strip()
            if not candidate:
                continue
            if not urls and candidate.lower() == "website":
                continue
            urls.append(candidate)
    return urls


def harvest_multiple(urls: Sequence[str]) -> List[Tuple[str, Dict[str, List[str]]]]:
    results: List[Tuple[str, Dict[str, List[str]]]] = []
    for url in urls:
        payload = harvest_with_gemini(url)
        results.append((url, payload))
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Harvest publications from a URL using Gemini + Chrome DevTools MCP."
    )
    parser.add_argument("url", nargs="?", help="Publications page URL to harvest")
    parser.add_argument(
        "-o", "--output", help="Output file (default: stdout)", default=None
    )
    parser.add_argument(
        "-s",
        "--sources-file",
        help="CSV file containing source URLs (used when URL is omitted)",
        default=str(DEFAULT_SOURCES_CSV),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of sources to process from the CSV when no URL is provided",
    )
    args = parser.parse_args()

    if args.url:
        urls_to_process: List[str] = [args.url]
    else:
        if args.batch_size <= 0:
            parser.error("--batch-size must be a positive integer")
        csv_path = Path(args.sources_file)
        urls = load_source_urls(csv_path)
        if not urls:
            parser.error(f"No URLs found in {csv_path}")
        urls_to_process = urls[: args.batch_size]

    if args.output and len(urls_to_process) > 1:
        parser.error("--output may only be used when harvesting a single URL")

    results = harvest_multiple(urls_to_process)

    for url, data in results:
        rendered = json.dumps(data, ensure_ascii=False, indent=2)
        if args.output:
            out_path = Path(args.output)
            out_path.write_text(rendered, encoding="utf-8")
        else:
            print(rendered)
        print("\n")
        print("*****Done!*****")
        print(
            "*****You still don't understand what you're dealing with, do you? The perfect organism.*****"
        )


if __name__ == "__main__":
    main()
