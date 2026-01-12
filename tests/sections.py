import sys
if 'pytest' in sys.modules:
    import pytest
    pytest.skip('not a testing file', allow_module_level = True)
import os
import re
import json
import time
import random
import argparse
import pdfplumber
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded

default_pdf = 'tests/633990.pdf'
final_json = 'paper_summaries.json'
partial_json = 'partial_paper_summaries.json'
model_name = 'models/gemini-flash-latest'

max_chars_per_section = 14000

skip_words = ["references", "bibliography", "acknowledg", "funding", 
              "conflict of interest", "author contribution", "appendix",
              "supplementary", "supporting information"]

def get_api_key():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("api key is missing. set gemini or google api key")
    return key

def skip_section(title):
    # skips sections like references, acknowledgements etc
    t = title.lower()
    return any(w in t for w in skip_words)

def extract_title(pdf):
    first = pdf.pages[0].extract_text() or ""
    lines = [l.strip() for l in first.splitlines() if l.strip()]

    stop = ("abstract", "keywords", "simple summary")
    title_lines = []

    for l in lines:
        if l.lower().startswith(stop):
            break
        title_lines.append(l)
        if len(title_lines) == 3: 
            break
    title = " ".join(title_lines)
    title = re.sub(r"\s+", " ", title).strip()
    return title if title else "title not known"


def shorten_text(text, max_chars=max_chars_per_section):
    # If section is huge, keep start and end. cut the middle to reduces timeouts
    if text is None:
        text = ''
    text = str(text).strip()

    if len(text) <= max_chars:
        return text

    head = text[: int(max_chars * 0.7)]
    tail = text[-int(max_chars * 0.3):]
    return head + "\n\n[deleted the middle part]\n\n" + tail


def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)



def make_model():
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def gemini_generate_text(model, prompt, max_retries=8):
    for attempt in range(max_retries):
        try:
            resp = model.generate_content(prompt)
            return resp.text or ""

        except (ResourceExhausted, DeadlineExceeded):
            wait = 25 + random.random()
            print(f"Rate-limited. Waiting {wait:.1f}s (try {attempt+1}/{max_retries})")
            time.sleep(wait)

        except Exception as e:
            return f"(failed: {e})"

    return "(failed: too many rate limits)"


def summarize_text(model, text, instruction):
    # making prompt 
    if text is None:
        return ""
    text = str(text).strip()
    if not text:
        return ""

    text = shorten_text(text) 
    prompt = instruction + "\n" + text
    return gemini_generate_text(model, prompt)

 # text extraction starting   from here  

def extract_numbered_sections(full_text):
    # finding headings like intro, conclusion, etc
    heading_re = re.compile(r"(?m)^\s*\d+(?:\.\d+)*\.?\s+([A-Za-z][A-Za-z0-9 &\-/]{1,80})\s*$")

    matches = list(heading_re.finditer(full_text))
    sections = {}

    for i in range(len(matches)):
        title = matches[i].group(1).strip()

        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)

        content = full_text[start:end].strip()

        # skips tiny sections
        if len(content) >= 200:
            if title in sections:
                title = title + " (" + str(i + 1) + ")"
            sections[title] = content

    return sections


def extract_abstract(full_text):
    # getting text after abtract until keywords or intro
    m = re.search(
        r"(?is)\bAbstract\b\s*(.+?)(?=\n\s*Keywords?:|\n\s*1\.\s*Introduction\b)",
        full_text,
    )
    return m.group(1).strip() if m else "(No abstract found)"


def extract_paper_structure(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        title = extract_title(pdf)
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    abstract = extract_abstract(full_text)
    sections = extract_numbered_sections(full_text)

    return {
        "title": title,   
        "abstract": abstract,
        "sections": sections,
        "full_text": full_text,
    }

# building pipeline

def summarize_paper(pdf_path, final_json, partial_json, resume):

    print("\n\nPDF:", pdf_path)

    model = make_model()
    paper = extract_paper_structure(pdf_path)

    section_titles = list(paper["sections"].keys())
    print("Found", len(section_titles), "sections. First few:")
    print(section_titles[:15])

    # If resume=True and partial file exists, continue from there
    if resume:
        result = load_json(partial_json)
    else:
        result = {}

    # making sure these keys always exist 
    if "pdf_path" not in result:
        result["pdf_path"] = pdf_path

    if "title" not in result:
        result["title"] = paper["title"]

    if "abstract_summary" not in result:
        result["abstract_summary"] = ""

    if "section_summaries" not in result:
        result["section_summaries"] = {}

    # getting the abstract first
    if (not result["abstract_summary"]) or str(result["abstract_summary"]).startswith("(failed"):
        print("\nSummarizing: Abstract")
        result["abstract_summary"] = summarize_text(
            model,
            paper["abstract"],
            "Summarize the abstract in 6 bullet points."
        )
        save_json(partial_json, result)

    # after abstract, all the following sections 
    for title, text in paper["sections"].items():
        if skip_section(title):
            continue
        if not text or len(text.strip()) < 200:
            continue

        if resume:
            old = result["section_summaries"].get(title, "")
            if old and not str(old).startswith("(failed"):
                continue

        print("\nSummarizing section:", title)
        result["section_summaries"][title] = summarize_text(
            model,
            text,
            "Summarize the section '" + title + "' in 6 bullet points."
        )

        # Ssaving after every section 
        save_json(partial_json, result)

    # Final save
    save_json(final_json, result)
    print("\ncompleted and saved:", final_json)
    print("Also saved progress file:", partial_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default=default_pdf)
    parser.add_argument("--out", default=final_json)
    parser.add_argument("--partial", default=partial_json)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    summarize_paper(args.pdf, args.out, args.partial, args.resume)


if __name__ == "__main__":
    main()
