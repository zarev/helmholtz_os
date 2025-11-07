import csv
import os
from typing import Iterable, Dict
from bs4 import BeautifulSoup


import requests

URL = 'https://photon-science.desy.de/facilities/petra_iii/beamlines/p05_imaging_beamline/publications_from_p05/2025/index_eng.html'

# save the HTML file
OUTPUT_FILE = 'last_page1_final.html'

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

BASE_EXPORT_URL = "https://bib-pubdb1.desy.de/PubExporter.py"
YEARS = list(range(2007, 2026))  
OUTPUT_FILE = "dois_for_p07.txt"

PARAMS_TEMPLATE = {
    "p": 'typ:"PUB:(DE-HGF)16" AND experiment:"EXP:(DE-H253)P-P05-20150101" AND pub:"{year}"',
    "sf": "author",
    "so": "d",
    "of": "gsblst",
    "rg": "50"
}
# Input and output files
OPEN_ACCESS_PAPERS_FILE = os.path.join("data", "open_access_papers.csv")
DOWNLOAD_DIR = "papers"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_publications(year):
    params = PARAMS_TEMPLATE.copy()
    params["p"] = params["p"].format(year=year)
    response = requests.get(BASE_EXPORT_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    return response.text

def extract_clean_links(html):
    soup = BeautifulSoup(html, 'html.parser')
    raw_links = set()

    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.match(r'https://bib-pubdb1\.desy\.de/record/\d+$', href)
        if match:
            raw_links.add(href)  
    return sorted(raw_links)

def iter_open_access_papers() -> Iterable[Dict[str, str]]:
    """Yield paper metadata rows from the open access CSV file."""
    try:
        with open(OPEN_ACCESS_PAPERS_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = (row.get("Title") or "").strip()
                url = (row.get("PDF_URL") or "").strip()
                if not url:
                    continue
                yield {"Title": title or "Unknown Title", "PDF_URL": url}
    except FileNotFoundError:
        raise SystemExit(
            f"❌ Could not find '{OPEN_ACCESS_PAPERS_FILE}'. Ensure the open access CSV exists."
        )


def download_pdf(title, url):
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
    
def fetch_and_save(url, filename):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()  # when there is error, the code stops 

    with open(filename, 'w', encoding='utf-8') as file:
        file.write(response.text)

    print(f"Saved the page to '{filename}'")


    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string.strip() if soup.title else "No title found"
    print(f"Page title is: {title}")
    print(f"Number of <p> tags in the page: {len(soup.find_all('p'))}")
    print(f"Number of <table> tags in the page: {len(soup.find_all('table'))}")


def main():
    # papers = list(iter_open_access_papers())

    #if not papers:
    #    print("⚠️ No papers found in the open access CSV.")
    #    return

    #for paper in papers:
    #    download_pdf(paper["Title"], paper["PDF_URL"])
    
    fetch_and_save(URL, OUTPUT_FILE)

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

if __name__ == "__main__":
    main()
