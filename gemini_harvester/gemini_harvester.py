import argparse
import os
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python <3.11 fallback
    import tomli as tomllib  # type: ignore

import google.generativeai as genai
import yaml


CONFIG_PATH = Path(__file__).resolve().parents[1] / "gemini_harvester" /"gemini_prompts.yaml"
GEMINI_CONFIG_PATH = Path.home() / ".config" / "gemini-cli.toml"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"


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


def call_gemini(
    prompt: str,
    *,
    model: Optional[str] = None,
    genai_module=genai,
) -> str:
    api_key = _resolve_api_key()
    selected_model = model or os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    # Configure the SDK once per call to keep the function stateless.
    genai_module.configure(api_key=api_key)
    chat_model = genai_module.GenerativeModel(selected_model)
    response = chat_model.generate_content(prompt)

    text = getattr(response, "text", "")
    if not text:
        raise RuntimeError("Gemini response did not contain any text output")

    return text.strip()


def harvest_with_gemini(url: str) -> dict:
    prompts = load_prompts()
    template = prompts["harvest_publications"]
    prompt = build_prompt(template, url)
    print("Building better worlds...")
    data = call_gemini(prompt)

    return data


def main():
    parser = argparse.ArgumentParser(
        description="Harvest publications from a URL using Gemini + Chrome DevTools MCP."
    )
    parser.add_argument("url", help="Publications page URL to harvest")
    parser.add_argument(
        "-o", "--output", help="Output file (default: stdout)", default=None
    )
    args = parser.parse_args()

    data = harvest_with_gemini(args.url)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(data, encoding="utf-8")
    
    print(data)
    print("\n")
    print("*****Done!*****")
    print("*****You still don't understand what you're dealing with, do you? The perfect organism.*****")


if __name__ == "__main__":
    main()
