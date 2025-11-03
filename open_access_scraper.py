import csv
import os
import time
from typing import Dict, Iterable, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from requests import HTTPError, Response
from urllib.parse import urljoin, urlparse, urlunparse

# Input and output files
OPEN_ACCESS_PAPERS_FILE = os.path.join("data", "open_access_papers.csv")
DOWNLOAD_DIR = "papers"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
)

REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1

_WARMED_ORIGINS = set()


# Recognised open-access repositories we scrape directly.
_OA_WHITELIST = (
    "arxiv.org",
    "biorxiv.org",
    "medrxiv.org",
    "hal.science",
    "zenodo.org",
    "osf.io",
    "ncbi.nlm.nih.gov",
)


def _normalise_host(host: str) -> str:
    return (host or "").lower().lstrip(".")


def _classify_oa_source(url: str) -> Optional[str]:
    parsed = urlparse(url)
    host = _normalise_host(parsed.netloc)
    path = parsed.path.lower()

    if not host:
        return None

    if host.endswith("arxiv.org"):
        return "arxiv"
    if host.endswith("biorxiv.org") or host.endswith("medrxiv.org"):
        return "rxiv"
    if host.endswith("hal.science"):
        return "hal"
    if host.endswith("zenodo.org"):
        return "zenodo"
    if host.endswith("osf.io"):
        return "osf"
    if host.endswith("ncbi.nlm.nih.gov") and "/pmc/" in path:
        return "pmc"

    if "/bitstream/handle/" in path:
        return "dspace"
    if "/eprint/" in path and path.endswith("document.pdf"):
        return "eprints"

    return None


def _is_whitelisted_oa_url(url: str) -> bool:
    if not url:
        return False
    if _classify_oa_source(url):
        return True
    parsed = urlparse(url)
    host = _normalise_host(parsed.netloc)
    return any(host.endswith(candidate) for candidate in _OA_WHITELIST)


class NonPdfContentError(Exception):
    """Raised when a response does not look like a PDF."""


def _is_pdf_response(response: Response) -> bool:
    content_type = response.headers.get("Content-Type", "").lower()
    return "application/pdf" in content_type


def _stream_pdf(url: str, filepath: str, referer: Optional[str] = None) -> None:
    headers = {}
    if referer:
        headers["Referer"] = referer

    with SESSION.get(url, stream=True, timeout=REQUEST_TIMEOUT, headers=headers) as response:
        response.raise_for_status()
        if not _is_pdf_response(response):
            raise NonPdfContentError(
                f"Unexpected content type '{response.headers.get('Content-Type')}'"
            )

        with open(filepath, "wb") as f:
            bytes_written = 0
            for chunk in response.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)

        if bytes_written == 0:
            raise NonPdfContentError("Empty PDF response")


def _derive_landing_page_url(pdf_url: str) -> Optional[str]:
    parsed = urlparse(pdf_url)
    source = _classify_oa_source(pdf_url)
    path = parsed.path

    if not source:
        return None

    if source == "arxiv":
        if "/pdf/" in path:
            identifier = path.split("/pdf/")[-1].split(".pdf")[0]
            new_path = f"/abs/{identifier}"
        elif "/abs/" in path:
            new_path = path
        else:
            return None
        return urlunparse(parsed._replace(path=new_path, query="", fragment=""))

    if source == "rxiv":
        if path.endswith(".pdf"):
            new_path = path[: -len(".pdf")]
        else:
            new_path = path
        return urlunparse(parsed._replace(path=new_path, query="", fragment=""))

    if source == "hal":
        if path.endswith("/document"):
            new_path = path[: -len("/document")]
        else:
            new_path = path
        return urlunparse(parsed._replace(path=new_path, query="", fragment=""))

    if source == "zenodo":
        segments = [segment for segment in path.split("/") if segment]
        if "record" in segments:
            record_index = segments.index("record")
            if record_index + 1 < len(segments):
                record_id = segments[record_index + 1]
                new_path = f"/record/{record_id}"
                return urlunparse(parsed._replace(path=new_path, query="", fragment=""))
        return urlunparse(parsed._replace(query="", fragment=""))

    if source == "osf":
        segments = [segment for segment in path.split("/") if segment]
        if segments:
            node = segments[0]
            new_path = f"/{node}/"
            return urlunparse(parsed._replace(path=new_path, query="", fragment=""))
        return None

    if source == "pmc":
        trimmed = path.replace("/pdf/", "/")
        if trimmed.endswith(".pdf"):
            trimmed = trimmed[: -len(".pdf")]
        segments = [segment for segment in trimmed.split("/") if segment]
        if len(segments) > 1:
            trimmed = "/" + "/".join(segments[:-1])
        return urlunparse(parsed._replace(path=trimmed, query="", fragment=""))

    if source in {"dspace", "eprints"}:
        lower_path = path.lower()
        marker = "/bitstream/"
        if marker in lower_path:
            idx = lower_path.index(marker) + len(marker)
            remainder = path[idx:]
            segments = [segment for segment in remainder.split("/") if segment]
            if len(segments) > 1:
                landing_segments = segments[:-1]
                new_path = f"/{'/'.join(landing_segments)}"
                return urlunparse(parsed._replace(path=new_path, query="", fragment=""))
        if path.endswith("document.pdf"):
            new_path = path[: -len("document.pdf")]
            return urlunparse(parsed._replace(path=new_path, query="", fragment=""))

    return urlunparse(parsed._replace(query="", fragment=""))


def _origin_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None

    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin.rstrip("/")


def _referer_for_url(url: str) -> Optional[str]:
    origin = _origin_from_url(url)
    if not origin:
        return None

    return f"{origin}/"


def _warm_up_origin(url: str) -> None:
    origin = _origin_from_url(url)
    if not origin or origin in _WARMED_ORIGINS:
        return

    try:
        SESSION.get(origin, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        print(f"   ↪️  Origin warm-up failed ({origin}): {exc}")
        return

    _WARMED_ORIGINS.add(origin)


def _extract_pdf_link(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    # Common meta tag used by many publishers
    meta_pdf = soup.find("meta", attrs={"name": "citation_pdf_url"})
    if meta_pdf and meta_pdf.get("content"):
        return urljoin(base_url, meta_pdf["content"])

    for tag in soup.find_all(["a", "link"], href=True):
        href = tag["href"]
        if _looks_like_pdf_url(href):
            return urljoin(base_url, href)

    # Some pages embed PDF URLs in meta tags with property attributes
    for meta in soup.find_all("meta", attrs={"property": True, "content": True}):
        if _looks_like_pdf_url(meta["content"]):
            return urljoin(base_url, meta["content"])

    return None


def _looks_like_pdf_url(url: str) -> bool:
    """Heuristically determine whether a URL likely points to a PDF file."""

    without_fragment = url.split("#", 1)[0]
    without_query = without_fragment.split("?", 1)[0].lower()
    if without_query.endswith(".pdf"):
        return True

    pdf_indicators = (
        "/pdf",
        "/pdfft",
        "pdfdownload",
        "?md5=",
        "/document",
        "/download",
        "/bitstream/handle/",
        "document.pdf",
    )
    normalized = without_fragment.lower()
    return any(indicator in normalized for indicator in pdf_indicators)


def _safe_search_get(url: str) -> Optional[str]:
    """Fetch a search/result page and return its HTML text or None on error."""
    try:
        resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        return None


def search_whitelisted_domains(title: str) -> Optional[Tuple[str, str]]:
    """Best-effort: search whitelisted OA domains for a paper by title.

    Returns a tuple (pdf_url, referer) if found, otherwise None.
    This is a lightweight, best-effort search — it tries a few known patterns
    for major OA hosts and falls back quickly on errors.
    """
    if not title:
        return None

    import urllib.parse

    q = urllib.parse.quote_plus(title)

    search_templates = {
        "arxiv.org": [f"https://arxiv.org/search/?query={q}&searchtype=all"],
        "zenodo.org": [f"https://zenodo.org/search?q={q}"],
        "hal.science": [f"https://hal.science/search/index/?q={q}", f"https://hal.science/search/index/?q={q}"],
        "osf.io": [f"https://osf.io/search/?q={q}"],
        "ncbi.nlm.nih.gov": [f"https://pubmed.ncbi.nlm.nih.gov/?term={q}"],
    }

    for host, templates in search_templates.items():
        for template in templates:
            html = _safe_search_get(template)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")

            # look for likely result links
            for a in soup.find_all("a", href=True):
                href = a["href"]
                # normalize possible relative URLs
                candidate = urljoin(f"https://{host}", href)

                # If the candidate is a whitelisted OA URL or looks like pdf, try to resolve it
                if _is_whitelisted_oa_url(candidate) or _looks_like_pdf_url(candidate):
                    # If it's a landing page, resolve via landing page resolution
                    resolved = None
                    try:
                        resolved = resolve_pdf_via_landing_page(candidate)
                    except Exception:
                        resolved = None

                    if resolved:
                        return resolved

                    # If not resolved but looks like a direct pdf, return it
                    if _looks_like_pdf_url(candidate):
                        referer = _derive_landing_page_url(candidate) or _referer_for_url(candidate)
                        return candidate, referer

    return None


def resolve_pdf_via_landing_page(pdf_url: str) -> Optional[Tuple[str, str]]:
    if not _is_whitelisted_oa_url(pdf_url):
        return None

    landing_page = _derive_landing_page_url(pdf_url)
    if not landing_page:
        return None

    _warm_up_origin(pdf_url)

    referer_header = _referer_for_url(pdf_url)
    headers = {"Referer": referer_header} if referer_header else None

    try:
        response = SESSION.get(landing_page, timeout=REQUEST_TIMEOUT, headers=headers)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"   ↪️  Landing page fetch failed ({landing_page}): {exc}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    resolved_pdf = _extract_pdf_link(soup, landing_page)
    if not resolved_pdf:
        print(f"   ↪️  No PDF link discovered on landing page {landing_page}")
        return None

    return resolved_pdf, landing_page


REPORT_FILE = os.path.join("data", "report.csv")


def _write_report_row(title: str, status: str, source: Optional[str], final_url: Optional[str], notes: Optional[str]) -> None:
    """Append a row to the CSV report at `data/report.csv`.

    Columns: Title,Status,Source,Final_URL,Notes
    """
    fieldnames = ["Title", "Status", "Source", "Final_URL", "Notes"]
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    write_header = not os.path.exists(REPORT_FILE)

    with open(REPORT_FILE, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(
            {
                "Title": title,
                "Status": status,
                "Source": source or "",
                "Final_URL": final_url or "",
                "Notes": notes or "",
            }
        )


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


def download_pdf(title: str, url: str) -> None:
    """Download a PDF from a whitelisted open-access repository."""
    safe_title = "".join(c if c.isalnum() or c in " -_()" else "_" for c in title)
    filepath = os.path.join(DOWNLOAD_DIR, f"{safe_title}.pdf")

    time.sleep(RATE_LIMIT_DELAY)

    if not url:
        print(f"⚠️ Skipping {title}: missing URL")
        _write_report_row(title, "SKIPPED", None, None, "missing URL")
        return

    original_url = url
    referer_for_direct = None

    if not _is_whitelisted_oa_url(url):
        # Try to find the paper on whitelisted OA domains by title
        print(f"⚠️ Domain not in OA whitelist for '{title}'; searching whitelist domains...")
        found = search_whitelisted_domains(title)
        if not found:
            print(f"⚠️ Skipping {title}: domain not in OA whitelist")
            _write_report_row(title, "SKIPPED", _origin_from_url(original_url), original_url, "domain not in OA whitelist")
            return
        # found is a tuple (pdf_url, referer)
        url, referer_for_direct = found

    need_fallback = False
    last_error = None

    looks_like_pdf = _looks_like_pdf_url(url)
    # only derive referer if not provided by a prior search
    if 'referer_for_direct' not in locals() or referer_for_direct is None:
        referer_for_direct = _derive_landing_page_url(url) if looks_like_pdf else None

    if looks_like_pdf:
        try:
            _stream_pdf(url, filepath, referer=referer_for_direct)
            print(f"✅ {title}")
            _write_report_row(title, "DOWNLOADED", _origin_from_url(url), url, "")
            return
        except NonPdfContentError as exc:
            print(f"   ↪️  Non-PDF response from {url}: {exc}")
            need_fallback = True
            last_error = exc
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response else "unknown"
            print(f"   ↪️  HTTP {status_code} when downloading {url}")
            need_fallback = True
            last_error = exc
        except requests.RequestException as exc:
            print(f"   ↪️  Network error for {url}: {exc}")
            need_fallback = True
            last_error = exc
    else:
        need_fallback = True

    if need_fallback:
        resolved = resolve_pdf_via_landing_page(url)
        if resolved:
            resolved_url, referer = resolved
            try:
                _stream_pdf(resolved_url, filepath, referer=referer)
                print(f"✅ {title} (resolved via landing page)")
                _write_report_row(title, "DOWNLOADED", _origin_from_url(resolved_url), resolved_url, "resolved via landing page")
                return
            except Exception as exc:  # noqa: BLE001 - broad to report fallback failure clearly
                last_error = exc
                print(f"   ↪️  Landing page download failed: {exc}")
        elif last_error is None:
            last_error = "Unable to resolve PDF from landing page"
    notes = str(last_error) if last_error else "No PDF link discovered"
    print(f"❌ Failed {title}: {notes}")
    _write_report_row(title, "FAILED", _origin_from_url(url), url, notes)

def main():
    papers = list(iter_open_access_papers())

    if not papers:
        print("⚠️ No papers found in the open access CSV.")
        return

    for paper in papers:
        download_pdf(paper["Title"], paper["PDF_URL"])

if __name__ == "__main__":
    main()
