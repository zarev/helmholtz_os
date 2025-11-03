"""Convert a PDF into Markdown using Gemini 1.5 Pro and extracted images.

This script splits the pages of a PDF into JPEG images and sends each page to
Google's Gemini API requesting a Markdown reconstruction of the content. The
Markdown for each page is saved to a single output file, with page images stored
in a dedicated directory.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import List

from google.api_core.exceptions import DeadlineExceeded, ResourceExhausted
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
from tqdm import tqdm


PDF_PATH = "input.pdf"
OUTPUT_MD = "output_with_images.md"
IMAGES_DIR = "pdf_images"
API_KEY = os.getenv("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY"
MODEL_NAME = "gemini-2.5-pro"
DPI = 200
RETRY_LIMIT = 6
IMAGE_QUALITY = 80


def _select_best_model(genai_module, prefer: str | None = None) -> str:
    """List available models and select the most capable one.

    Preference heuristic:
    - prefer model names containing 'pro' and '2.5'
    - avoid 'flash', 'lite', 'preview', 'embedding'
    - fall back to the provided MODEL_NAME if listing fails
    """
    try:
        models = genai_module.list_models()
    except Exception:
        return MODEL_NAME

    scores = {}
    for m in models:
        try:
            name = m.name
        except Exception:
            name = str(m)
        key = name.lower()
        score = 0
        if "pro" in key:
            score += 100
        if "2.5" in key:
            score += 80
        if "2.0" in key:
            score += 20
        if "flash" in key:
            score -= 30
        if "lite" in key:
            score -= 50
        if "preview" in key:
            score -= 10
        if "embedding" in key:
            score -= 80
        # slight preference for longer names (heuristic)
        score += min(len(key), 50) / 10
        scores[name] = score

    if not scores:
        return MODEL_NAME

    # pick the model with highest score
    best = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[0][0]
    return best


def split_pdf_to_images(
    pdf_path: str,
    dpi: int,
    converter=convert_from_path,
) -> List[Image.Image]:
    """Split a PDF into images using the provided DPI."""

    return converter(pdf_path, dpi=dpi)


def extract_markdown_from_pages(
    pages: List[Image.Image],
    images_dir: str = IMAGES_DIR,
    image_quality: int = IMAGE_QUALITY,
    retry_limit: int = RETRY_LIMIT,
    api_key: str = API_KEY,
    model_name: str = MODEL_NAME,
    sleep_fn=time.sleep,
    genai_module=genai,
    model=None,
    fail_on_error: bool = False,
) -> List[str]:
    """Process each page image through Gemini and return Markdown snippets."""

    if model is None:
        genai_module.configure(api_key=api_key)
        # attempt to select the best available model on this key
        try:
            # Only auto-select when the caller left model_name as the default.
            if model_name is None or model_name == MODEL_NAME:
                selected = _select_best_model(genai_module)
                # override the requested model_name if selection returns something
                if selected:
                    model_name = selected
        except Exception:
            # fall back silently
            pass
        model = genai_module.GenerativeModel(model_name)

    Path(images_dir).mkdir(exist_ok=True)

    results: List[str] = []
    for i, page in enumerate(tqdm(pages, desc="Processing pages")):
        img_name = f"page_{i + 1}.jpg"
        img_path = os.path.join(images_dir, img_name)

        page.save(img_path, "JPEG", quality=image_quality)

        for attempt in range(retry_limit):
            try:
                image_bytes = Path(img_path).read_bytes()
                prompt = (
                    "Extract this page into Markdown, keeping tables, code, and layout. "
                    "If this page includes images, refer to them as "
                    f"`![Page {i + 1}]({img_path})` at the appropriate place in the text."
                )
                image_part = {"mime_type": "image/jpeg", "data": image_bytes}
                response = model.generate_content([image_part, prompt])
                # robustly extract text from the response
                text_out = None
                try:
                    # quick accessor may fail if response parts differ
                    text_out = getattr(response, "text", None)
                except Exception:
                    text_out = None

                if not text_out:
                    # attempt to inspect candidates/parts
                    try:
                        pieces = []
                        candidates = getattr(response, "candidates", None) or []
                        for cand in candidates:
                            parts = getattr(cand, "content", None) or getattr(cand, "parts", None) or []
                            for part in parts:
                                # part may be object or dict-like
                                part_text = None
                                if hasattr(part, "text"):
                                    part_text = getattr(part, "text")
                                elif isinstance(part, dict):
                                    part_text = part.get("text") or part.get("content")
                                elif hasattr(part, "get"):
                                    try:
                                        part_text = part.get("text")
                                    except Exception:
                                        part_text = None
                                if part_text:
                                    pieces.append(str(part_text))
                        if pieces:
                            text_out = "\n".join(pieces)
                    except Exception:
                        text_out = None

                if text_out:
                    results.append(f"## Page {i + 1}\n\n{text_out}")
                else:
                    # no textual parts found — include raw response as note
                    results.append(f"## Page {i + 1}\n\n<!-- No textual part found in API response; raw: {str(response)[:400]} -->")
                break
            except (ResourceExhausted, DeadlineExceeded):
                # start with a 5s base backoff to match previous behaviour and
                # exponentially increase for subsequent attempts
                base_backoff = 5
                backoff = min(base_backoff * (2 ** attempt), 60)
                print(f"Retry {attempt + 1} for page {i + 1} due to rate/time limits; sleeping {backoff}s.")
                sleep_fn(backoff)
            except Exception as exc:  # pragma: no cover - defensive programming
                # Improved handling for API/model errors: attempt to list available models
                # and include that information in the output to assist debugging.
                note = f"{exc}"
                print(f"Error on page {i + 1}: {note}")
                try:
                    models = genai_module.list_models()
                    # models may be a list of objects or dicts depending on client
                    try:
                        model_ids = [m.name for m in models]
                    except Exception:
                        model_ids = [str(m) for m in models]
                    note += f"; available models: {', '.join(model_ids[:10])}"
                    print(f"Available models: {', '.join(model_ids[:10])}")
                except Exception:
                    # listing models failed; ignore and continue
                    pass

                if fail_on_error:
                    raise

                # include the note in the markdown output for visibility
                results.append(f"\n<!-- Page {i + 1} failed: {note} -->\n")
                break
    return results


def save_markdown(snippets: List[str], output_path: str = OUTPUT_MD) -> None:
    """Save the combined Markdown output to disk."""
    markdown_output = "\n\n---\n\n".join(snippets)
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(markdown_output)



def main() -> None:
    pages = split_pdf_to_images(PDF_PATH, DPI)
    markdown_snippets = extract_markdown_from_pages(pages)
    save_markdown(markdown_snippets)
    print(f"\n✅ Done! Markdown saved to: {OUTPUT_MD}")
    print(f"🖼️ Images stored in: {IMAGES_DIR}/")


if __name__ == "__main__":
    main()
