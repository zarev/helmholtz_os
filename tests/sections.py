import pdfplumber
import re
import glob
import json
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-flash-latest")

def summarize(text, instruction="Summarize clearly and simply."):
    """Uses Gemini to summarize text."""
    response = model.generate_content(instruction + "\n\n" + text)
    return response.text

def extract_paper_structure(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    # Extract abstract
    abstract_match = re.search(
        r"Abstract(.+?)(?=\n[A-Z][A-Za-z ]+\n)",
        full_text,
        re.S
    )
    abstract = abstract_match.group(1).strip() if abstract_match else "(No abstract found)"

    # Extract sections
    titles = re.findall(r"\n\d*\.?\s*([A-Z][A-Za-z ]+)\n", full_text)
    sections = re.split(r"\n\d*\.?\s*[A-Z][A-Za-z ]+\n", full_text)

    section_dict = {title.strip(): content.strip() for title, content in zip(titles, sections)}

    # Paper title
    paper_title = titles[0] if titles else "Unknown Title"

    return {
        "title": paper_title,
        "abstract": abstract,
        "sections": section_dict,
        "full_text": full_text,
    }

def answer_query(query, paper):
    q = query.lower()

    # Title
    if "title" in q:
        return paper["title"]

    # Abstract summary
    if (
        "summary of abstract" in q 
        or "abstract summary" in q 
        or ("abstract" in q and ("summary" in q or "summarize" in q))
    ):
        return summarize(paper["abstract"])

    # Full abstract (no summarization)
    if "abstract" in q:
        return paper["abstract"]

    # Section summary (e.g. "summarize introduction", "summary of methods")
    for sec in paper["sections"]:
        sec_name = sec.lower()
        if sec_name in q and ("summary" in q or "summarize" in q or "summarise" in q):
            return summarize(paper["sections"][sec])

    # Full section (e.g. "show introduction", "give methods section")
    for sec in paper["sections"]:
        sec_name = sec.lower()
        if sec_name in q:
            return paper["sections"][sec]

    # Summaries of all sections
    if "summary of sections" in q or "summaries of sections" in q:
        output = {}
        for sec, txt in paper["sections"].items():
            output[sec] = summarize(txt)
        return output

    # Full paper
    if "full paper" in q or "entire paper" in q:
        return paper["full_text"]

    return "Query not understood."


def build_paper_database(pdf_pattern="papers/*.pdf", save_json="papers_db.json"):

    db = {}

    for pdf in glob.glob(pdf_pattern):
        print("Processing:", pdf)
        db[pdf] = extract_paper_structure(pdf)

    with open(save_json, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=4)

    print("\nDatabase saved to", save_json)
    return db

if __name__ == "__main__":
    path = "tests/633990.pdf" 
    paper = extract_paper_structure(path)

    print("\nTITLE:\n", answer_query("give me the title", paper))
    print("\nABSTRACT SUMMARY:\n", answer_query("summary of abstract", paper))
    print("\nINTRODUCTION SUMMARY:\n", answer_query("summarize introduction", paper))