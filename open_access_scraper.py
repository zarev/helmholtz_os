import csv
import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from pgvector_ingest import store_paper

# Input and output files
SOURCES_FILE = "sources.csv"       # List of institution URLs
OUTPUT_FILE = "open_access_papers.csv"
DOWNLOAD_DIR = "papers"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_open_access_links(base_url):
    """Scrape Open Access papers from an institution page."""
    papers = []
    try:
        r = requests.get(base_url, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Find links to PDFs or Open Access indicators
        for link in soup.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            if any(keyword in href.lower() for keyword in [".pdf", "open", "doi.org", "publication"]):
                full_url = urljoin(base_url, href)
                papers.append({
                    "Title": text or "Unknown Title",
                    "PDF_URL": full_url
                })
    except Exception as e:
        print(f"⚠️ Could not scrape {base_url}: {e}")
    return papers

def download_pdf(title, url):
    """Download a PDF from URL.

    Returns the filesystem path for the saved PDF when the download succeeds,
    otherwise returns ``None``.
    """
    safe_title = "".join(c if c.isalnum() or c in " -_()" else "_" for c in title)
    filepath = os.path.join(DOWNLOAD_DIR, f"{safe_title}.pdf")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print(f"✅ {title}")
        return filepath
    except Exception as e:
        print(f"❌ Failed {title}: {e}")
        return None

def main():
    all_papers = []

    # Load institution websites
    with open(SOURCES_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            site = row.get("Website") or row.get("URL")
            if site:
                print(f"🌐 Scanning {site}")
                papers = get_open_access_links(site)
                all_papers.extend(papers)

    # Write all found papers to CSV
    with open(OUTPUT_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "PDF_URL"])
        writer.writeheader()
        writer.writerows(all_papers)

    # Download all papers
    for paper in all_papers:
        filepath = download_pdf(paper["Title"], paper["PDF_URL"])
        if filepath:
            store_paper(filepath, paper["Title"], paper["PDF_URL"])

if __name__ == "__main__":
    main()
