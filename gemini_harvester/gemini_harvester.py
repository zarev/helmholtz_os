import argparse
import subprocess
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).resolve().parents[1] / "gemini_harvester" /"gemini_prompts.yaml"


def load_prompts():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_prompt(template: str, url: str) -> str:
    return template.replace("{{ url }}", url)


def call_gemini(prompt: str) -> str:
    """
    Call the `gemini` CLI with the prompt via stdin.
    """
    proc = subprocess.run(
        ["gemini"],
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"gemini CLI failed with code {proc.returncode}:\nSTDERR:\n{proc.stderr}"
        )

    return proc.stdout.strip()


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
