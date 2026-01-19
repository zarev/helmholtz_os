from pathlib import Path
import sys

import pytest
from requests import HTTPError

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import open_access_scraper  # noqa: E402


@pytest.fixture(autouse=True)
def _patch_rate_limit(monkeypatch):
    monkeypatch.setattr(open_access_scraper.time, "sleep", lambda _: None)


@pytest.fixture(autouse=True)
def _reset_origin_cache():
    open_access_scraper._WARMED_ORIGINS.clear()
    yield
    open_access_scraper._WARMED_ORIGINS.clear()


def test_download_pdf_skips_non_whitelisted_domain(monkeypatch, tmp_path, capsys):
    called = {"count": 0}

    def fake_stream(url, filepath, referer=None):  # pragma: no cover - should not be called
        called["count"] += 1

    monkeypatch.setattr(open_access_scraper, "_stream_pdf", fake_stream)
    monkeypatch.setattr(open_access_scraper, "DOWNLOAD_DIR", str(tmp_path))

    url = (
        "https://www.sciencedirect.com/science/article/pii/"
        "S0030399224008855/pdfft?pid=1-s2.0-S0030399224008855-main.pdf"
    )

    # simulate search returning nothing
    search_called = {"count": 0}

    def fake_search(title):
        search_called["count"] += 1
        return None

    monkeypatch.setattr(open_access_scraper, "search_whitelisted_domains", fake_search)

    open_access_scraper.download_pdf("Blocked Host", url)

    captured = capsys.readouterr().out
    assert "Domain not in OA whitelist" in captured or "domain not in OA whitelist" in captured
    assert search_called["count"] == 1
    assert called["count"] == 0


def test_download_pdf_streams_direct_arxiv_pdf(monkeypatch, tmp_path):
    calls = []

    def fake_stream(url, filepath, referer=None):
        calls.append((url, referer))
        Path(filepath).write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(open_access_scraper, "_stream_pdf", fake_stream)
    monkeypatch.setattr(open_access_scraper, "DOWNLOAD_DIR", str(tmp_path))

    url = "https://arxiv.org/pdf/2101.00001.pdf"
    open_access_scraper.download_pdf("ArXiv Paper", url)

    target = Path(tmp_path, "ArXiv Paper.pdf")
    assert target.exists()
    assert calls == [(url, "https://arxiv.org/abs/2101.00001")]


def test_download_pdf_uses_landing_resolution_for_arxiv_abs(monkeypatch, tmp_path):
    stream_calls = []
    resolve_calls = []

    def fake_stream(url, filepath, referer=None):
        stream_calls.append((url, referer))
        Path(filepath).write_bytes(b"%PDF-1.4 test")

    def fake_resolve(url):
        resolve_calls.append(url)
        return "https://arxiv.org/pdf/2101.00001.pdf", "https://arxiv.org/abs/2101.00001"

    monkeypatch.setattr(open_access_scraper, "_stream_pdf", fake_stream)
    monkeypatch.setattr(open_access_scraper, "resolve_pdf_via_landing_page", fake_resolve)
    monkeypatch.setattr(open_access_scraper, "DOWNLOAD_DIR", str(tmp_path))

    open_access_scraper.download_pdf("ArXiv Abs", "https://arxiv.org/abs/2101.00001")

    target = Path(tmp_path, "ArXiv Abs.pdf")
    assert target.exists()
    assert resolve_calls == ["https://arxiv.org/abs/2101.00001"]
    assert stream_calls == [
        ("https://arxiv.org/pdf/2101.00001.pdf", "https://arxiv.org/abs/2101.00001")
    ]


def test_resolve_pdf_via_landing_page_arxiv(monkeypatch):
    landing_html = """
    <html>
        <head>
            <meta name="citation_pdf_url" content="/pdf/2101.00001.pdf" />
        </head>
    </html>
    """

    class DummyResponse:
        def __init__(self, text=""):
            self.text = text

        def raise_for_status(self):
            return None

    calls = []

    def fake_get(url, timeout, headers=None):
        calls.append((url, headers))
        if url == "https://arxiv.org":
            return DummyResponse()
        assert url == "https://arxiv.org/abs/2101.00001"
        assert headers == {"Referer": "https://arxiv.org/"}
        return DummyResponse(landing_html)

    monkeypatch.setattr(open_access_scraper.SESSION, "get", fake_get)

    resolved = open_access_scraper.resolve_pdf_via_landing_page("https://arxiv.org/pdf/2101.00001.pdf")

    assert resolved is not None
    pdf_url, referer = resolved
    assert pdf_url == "https://arxiv.org/pdf/2101.00001.pdf"
    assert referer == "https://arxiv.org/abs/2101.00001"
    assert calls[0] == ("https://arxiv.org", None)


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "https://arxiv.org/pdf/2101.00001.pdf",
            "https://arxiv.org/abs/2101.00001",
        ),
        (
            "https://hal.science/hal-012345/document",
            "https://hal.science/hal-012345",
        ),
        (
            "https://zenodo.org/record/123456/files/paper.pdf",
            "https://zenodo.org/record/123456",
        ),
        (
            "https://osf.io/abcd1/download",
            "https://osf.io/abcd1/",
        ),
        (
            "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/pdf/paper.pdf",
            "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567",
        ),
        (
            "https://repo.example.edu/bitstream/handle/1234/5678/Document.pdf",
            "https://repo.example.edu/handle/1234/5678",
        ),
        (
            "https://example.edu/eprint/12345/document.pdf",
            "https://example.edu/eprint/12345/",
        ),
    ],
)
def test_derive_landing_page_url(url, expected):
    assert open_access_scraper._derive_landing_page_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://arxiv.org/pdf/2101.00001.pdf",
        "https://hal.science/hal-012345/document",
        "https://zenodo.org/record/123456/files/paper.pdf",
        "https://osf.io/abcd1/download",
        "https://repo.example.edu/bitstream/handle/1234/5678/Document.pdf",
    ],
)
def test_is_whitelisted_positive(url):
    assert open_access_scraper._is_whitelisted_oa_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.sciencedirect.com/science/article/pii/S0030399224008855/pdfft",
        "https://example.com/paper.pdf",
    ],
)
def test_is_whitelisted_negative(url):
    assert not open_access_scraper._is_whitelisted_oa_url(url)


def test_resolve_pdf_returns_none_for_non_whitelisted():
    assert (
        open_access_scraper.resolve_pdf_via_landing_page(
            "https://www.sciencedirect.com/science/article/pii/S0030399224008855/pdfft"
        )
        is None
    )


def test_stream_pdf_propagates_http_error(monkeypatch, tmp_path):
    class DummyResponse:
        def __init__(self):
            self.status_code = 403
            self.url = "https://arxiv.org/pdf/2101.00001.pdf"
            self.headers = {"Content-Type": "text/html"}

        def raise_for_status(self):
            error = HTTPError("403 Client Error: Forbidden for url")
            error.response = self
            raise error

        def iter_content(self, _chunk_size):
            yield from ()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_get(url, stream=True, timeout=None, headers=None):
        assert headers == {"Referer": "https://arxiv.org/abs/2101.00001"}
        return DummyResponse()

    monkeypatch.setattr(open_access_scraper.SESSION, "get", fake_get)

    target = tmp_path / "blocked.pdf"
    with pytest.raises(HTTPError):
        open_access_scraper._stream_pdf(
            "https://arxiv.org/pdf/2101.00001.pdf",
            str(target),
            referer="https://arxiv.org/abs/2101.00001",
        )

    assert not target.exists()


@pytest.mark.parametrize(
    "url",
    [
        "https://arxiv.org/pdf/2101.00001.pdf",
        "https://hal.science/hal-012345/document",
        "https://zenodo.org/record/123456/files/paper.pdf",
    ],
)
def test_looks_like_pdf_url_positive(url):
    assert open_access_scraper._looks_like_pdf_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://arxiv.org/abs/2101.00001",
        "https://example.com/viewer",
    ],
)
def test_looks_like_pdf_url_negative(url):
    assert not open_access_scraper._looks_like_pdf_url(url)
