import csv
import os
from typing import Iterable, Dict
from bs4 import BeautifulSoup
import re
import time
import requests
from urllib.parse import urljoin

urls_file = "data/sources.csv"

# Save the HTML file
DEBUG_HTML_FILE = "debug_page.html"
DEBUG_SAVE_HTML = False
INPUT_FILE = "dois_for_p07.txt"
BASE_FOLDER = "all_pdfs"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

BASE_EXPORT_URLS = {
    "desy": "https://bib-pubdb1.desy.de/PubExporter.py"
}

# Input and output files
OPEN_ACCESS_PAPERS_FILE = os.path.join("data", "open_access_papers.csv")
DOWNLOAD_DIR = "all_pdfs"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def load_years(file_path: str) -> list[int]:
    years = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.isdigit():
                years.append(int(line))
    return years

YEARS = list(range(1980, 2026)) 
OUTPUT_FILE = "dois_for_p07.txt"


def load_urls(file_path: str) -> list[str]:
    urls = []
    with open(file_path, "r") as f:
        for line in f:
            url = line.strip()
            if url.lower().startswith("http"):
                urls.append(url)
    return urls


def get_record_number(url):
    return url.rstrip("/").split("/")[-1]


def download_pdf(pdf_url: str, record_number: str, year_str: str | None = None):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    if year_str:
        filename = f"{record_number}_{year_str}.pdf"
    else:
        filename = f"{record_number}.pdf"

    file_path = os.path.join(DOWNLOAD_DIR, filename)

    with requests.get(pdf_url, headers=HEADERS, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        if "application/pdf" not in resp.headers.get("Content-Type", "").lower():
            print(f"⚠️ Skipped (not a PDF content-type): {pdf_url}")
            return
        with open(file_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    print(f"✅ Downloaded: {file_path}")


def process_record(url):
    try:
        record_number = get_record_number(url)
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Detect the access type of the PDFs
        access_tag = soup.find("div", {"id": "detailedrecordminipanelfile"})
        if not access_tag:
            print(f"❌ No file info found: {url}")
            return

        access_type = access_tag.find("small", class_="detailedRecordActions")
        if not access_type:
            print(f"❌ Could not determine access type: {url}")
            return

        if access_type.text.strip() != "OpenAccess:":
            print(f"🔒 Restricted: {url}")
            return

        pdf_link_tag = access_tag.find("a", href=True)
        if pdf_link_tag and pdf_link_tag["href"].endswith(".pdf"):
            pdf_url = pdf_link_tag["href"]
            year = None 
            download_pdf(pdf_url, record_number, year)
        else:
            print(f"⚠️ No valid PDF link found: {url}")

    except Exception as e:
        print(f"❌ Error processing {url}: {e}")


def fetch_publications(year, source="desy"):
    '''right now only for desy. can add more databases later (ESRF, Diamond, etc)'''
    base_url = BASE_EXPORT_URLS.get(source)
    if source == 'desy':
        params = {
            "p": f'typ:"PUB:(DE-HGF)16" AND experiment:"EXP:(DE-H253)P-P05-20150101" AND pub:"{year}"',
            "sf": "author",
            "so": "d",
            "of": "gsblst",
            "rg": "50",
        }
        response = requests.get(base_url, params=params, headers=HEADERS)
        response.raise_for_status()
        return response.text


def extract_clean_links(html):
    soup = BeautifulSoup(html, "html.parser")
    raw_links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        match = re.match(r"https://bib-pubdb1\.desy\.de/record/\d+$", href)
        if match:
            raw_links.add(href)
    return sorted(raw_links)


def download_pdf_from_record(title, url):
    """Download a PDF from URL."""
    safe_title = "".join(c if c.isalnum() or c in " -_()" else "_" for c in title)
    filepath = os.path.join(DOWNLOAD_DIR, f"{safe_title}.pdf")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)
        print(f"✅ {title}")
    except Exception as e:
        print(f"❌ Failed {title}: {e}")


def fetch_and_save(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    time.sleep(3) # 1 second delay

    if DEBUG_SAVE_HTML:
        with open(DEBUG_HTML_FILE, "w", encoding="utf-8") as file:
            file.write(response.text)
        print(f"Saved the page to '{DEBUG_HTML_FILE}'")

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "No title found"
        print(f"Page title is: {title}")
        print(f"Number of <p> tags in the page: {len(soup.find_all('p'))}")
        print(f"Number of <table> tags in the page: {len(soup.find_all('table'))}")

def main():
    urls = load_urls(urls_file)
    desy_urls = [u for u in urls if 'photon-science.desy.de' in u]
    if not desy_urls:
        print("No DESY URLs found in the source file.")
        return
    
    desy_url = desy_urls[0]
    print(f'using url: {desy_url}')
    fetch_and_save(desy_url)

    all_links = []
    for year in YEARS:
        print(f"Year: {year}")
        try:
            html = fetch_publications(year)
            links = extract_clean_links(html)
            all_links.extend(links)
            for link in links:
                print(f"{link}")
        except Exception as e:
            print(f"Failed to fetch for {year}: {e}")

    with open(OUTPUT_FILE, "w") as f:
        for link in all_links:
            f.write(link + "\n")

    print(f"\n Saved {len(all_links)} links to {OUTPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip().startswith("http")]

    if not urls:
        print(f"❌ No valid URLs found in {INPUT_FILE}")
    else:
        for url in urls:
            print(f"Checking: {url}")
            process_record(url)
            time.sleep(3)


if __name__ == "__main__":
    main()