from __future__ import annotations

import importlib.util
import os
import socket
import ssl
import sys
import types
from pathlib import Path
from typing import List

import pytest
from pdf2image.exceptions import PDFInfoNotInstalledError
from PIL import Image, ImageDraw


def _load_pdf_to_markdown_module(*, stub_genai: bool = True):
    module_path = Path(__file__).resolve().parents[1] / "pdf_to_markdown.py"

    module_name = "pdf_to_markdown"

    for name in [module_name, f"tests.{module_name}"]:
        sys.modules.pop(name, None)

    if stub_genai:
        google_module = types.ModuleType("google")
        api_core_module = types.ModuleType("google.api_core")
        exceptions_module = types.ModuleType("google.api_core.exceptions")

        class _TransientError(Exception):
            pass

        exceptions_module.ResourceExhausted = _TransientError
        exceptions_module.DeadlineExceeded = _TransientError

        api_core_module.exceptions = exceptions_module
        google_module.api_core = api_core_module

        generative_module = types.ModuleType("google.generativeai")

        class DummyGenerativeModel:
            def __init__(self, *_args, **_kwargs):  # pragma: no cover - stub
                raise AssertionError("This stub should not be instantiated in tests")

        def configure(**_kwargs):  # pragma: no cover - stub
            raise AssertionError("configure should not be called in tests")

        generative_module.GenerativeModel = DummyGenerativeModel
        generative_module.configure = configure

        sys.modules.setdefault("google", google_module)
        sys.modules.setdefault("google.api_core", api_core_module)
        sys.modules.setdefault("google.api_core.exceptions", exceptions_module)
        sys.modules.setdefault("google.generativeai", generative_module)

        tqdm_module = types.ModuleType("tqdm")

        def _tqdm(iterable, **_kwargs):  # pragma: no cover - stub
            return iterable

        tqdm_module.tqdm = _tqdm

        sys.modules.setdefault("tqdm", tqdm_module)
    else:
        for name in [
            "google.generativeai",
            "google.api_core.exceptions",
            "google.api_core",
            "google",
            "tqdm",
        ]:
            if name in sys.modules and isinstance(sys.modules[name], types.ModuleType):
                sys.modules.pop(name, None)

    spec = importlib.util.spec_from_file_location("pdf_to_markdown", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None  # for mypy
    spec.loader.exec_module(module)
    return module


ptm = _load_pdf_to_markdown_module()


class DummyResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class DummyModel:
    def __init__(self, responses: List[str]) -> None:
        self._responses = iter(responses)
        self.calls = []

    def generate_content(self, args):
        self.calls.append(args)
        return DummyResponse(next(self._responses))


class DummyImage:
    def __init__(self) -> None:
        self.saved_paths = []

    def save(self, path: str, _format: str, quality: int) -> None:  # pragma: no cover - trivial
        self.saved_paths.append((path, quality))
        Path(path).write_bytes(b"fake image data")


@pytest.fixture()
def sample_image() -> DummyImage:
    return DummyImage()


@pytest.fixture(scope="session")
def sample_pdf_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    pdf_dir = tmp_path_factory.mktemp("pdf_samples")
    pdf_path = pdf_dir / "sample.pdf"

    if not pdf_path.exists():
        pages: list[Image.Image] = []
        for idx in range(2):
            image = Image.new("RGB", (612, 792), "white")
            draw = ImageDraw.Draw(image)
            draw.rectangle((60, 60, 552, 732), outline="black", width=3)
            draw.text((90, 120), f"Sample Page {idx + 1}", fill="black")
            draw.text((90, 180), "Automated test document", fill="black")
            draw.text((90, 240), "Generated on demand", fill="black")
            pages.append(image)

        first_page, *rest = pages
        first_page.save(pdf_path, format="PDF", save_all=True, append_images=rest)

        for image in pages:
            image.close()

    return pdf_path


def test_extract_markdown_from_pages_saves_images_and_returns_markdown(tmp_path: Path, sample_image: DummyImage):
    images_dir = tmp_path / "images"
    dummy_model = DummyModel(["markdown output"])

    snippets = ptm.extract_markdown_from_pages(
        [sample_image],
        images_dir=str(images_dir),
        model=dummy_model,
        genai_module=None,  # bypass configuration
        fail_on_error=True,
    )

    assert snippets == ["## Page 1\n\nmarkdown output"]
    expected_image = images_dir / "page_1.jpg"
    assert expected_image.exists()
    assert dummy_model.calls[0][1] == (
        "Extract this page into Markdown, keeping tables, code, and layout. "
        "If this page includes images, refer to them as "
        f"`![Page 1]({expected_image})` at the appropriate place in the text."
    )


def test_extract_markdown_retries_on_transient_errors(tmp_path: Path, sample_image: DummyImage):
    images_dir = tmp_path / "images"

    class FlakyModel:
        def __init__(self) -> None:
            self.calls = 0

        def generate_content(self, _):
            self.calls += 1
            if self.calls == 1:
                raise ptm.ResourceExhausted("transient")
            return DummyResponse("second attempt")

    sleep_calls = []

    def fake_sleep(seconds: int) -> None:  # pragma: no cover - trivial
        sleep_calls.append(seconds)

    model = FlakyModel()

    snippets = ptm.extract_markdown_from_pages(
        [sample_image],
        images_dir=str(images_dir),
        model=model,
        genai_module=None,
        retry_limit=3,
        sleep_fn=fake_sleep,
    )

    assert snippets == ["## Page 1\n\nsecond attempt"]
    assert sleep_calls == [5]
    assert model.calls == 2


def test_save_markdown_writes_joined_output(tmp_path: Path):
    output_path = tmp_path / "output.md"

    ptm.save_markdown(["first", "second"], output_path=str(output_path))

    assert output_path.read_text(encoding="utf-8") == "first\n\n---\n\nsecond"


def test_split_pdf_to_images_uses_provided_converter():
    calls = {}

    def fake_convert(path, dpi):
        calls["path"] = path
        calls["dpi"] = dpi
        return ["image"]

    result = ptm.split_pdf_to_images("some.pdf", 144, converter=fake_convert)

    assert result == ["image"]
    assert calls == {"path": "some.pdf", "dpi": 144}


def test_end_to_end_processing_with_real_pdf(tmp_path: Path, sample_pdf_path: Path):
    pdf_path = sample_pdf_path
    try:
        pages = ptm.split_pdf_to_images(str(pdf_path), dpi=72)
    except PDFInfoNotInstalledError as exc:
        pytest.skip(f"pdf2image dependencies unavailable: {exc}")

    assert len(pages) == 2

    responses = [f"content for page {idx + 1}" for idx in range(len(pages))]
    images_dir = tmp_path / "images"

    snippets = ptm.extract_markdown_from_pages(
        pages,
        images_dir=str(images_dir),
        model=DummyModel(responses),
        genai_module=None,
        fail_on_error=True,
    )

    assert len(snippets) == len(pages)
    for idx in range(len(pages)):
        expected_path = images_dir / f"page_{idx + 1}.jpg"
        assert expected_path.exists()
        assert snippets[idx] == f"## Page {idx + 1}\n\ncontent for page {idx + 1}"


def test_end_to_end_processing_with_stubbed_gemini_module(
    tmp_path: Path, sample_pdf_path: Path
):
    pdf_path = sample_pdf_path
    try:
        pages = ptm.split_pdf_to_images(str(pdf_path), dpi=72)
    except PDFInfoNotInstalledError as exc:
        pytest.skip(f"pdf2image dependencies unavailable: {exc}")

    assert len(pages) == 2

    responses = [f"markdown from gemini page {idx + 1}" for idx in range(len(pages))]
    response_iter = iter(responses)

    class RecordingGenerativeModel:
        def __init__(self, model_name: str) -> None:
            self.model_name = model_name
            self.calls: list[tuple[Path, str]] = []

        def generate_content(self, parts):
            image_part, prompt = parts
            assert image_part["mime_type"] == "image/jpeg"
            image_path = images_dir / f"page_{len(self.calls) + 1}.jpg"
            assert image_path.exists()
            assert image_path.read_bytes() == image_part["data"]
            self.calls.append((image_path, prompt))
            return DummyResponse(next(response_iter))

    class StubGenAIModule:
        def __init__(self) -> None:
            self.configured_keys: list[str] = []
            self.models: list[RecordingGenerativeModel] = []

        def configure(self, *, api_key: str) -> None:
            self.configured_keys.append(api_key)

        def GenerativeModel(self, model_name: str) -> RecordingGenerativeModel:
            model = RecordingGenerativeModel(model_name)
            self.models.append(model)
            return model

    stub_module = StubGenAIModule()
    images_dir = tmp_path / "images"

    snippets = ptm.extract_markdown_from_pages(
        pages,
        images_dir=str(images_dir),
        genai_module=stub_module,
        model=None,
        api_key="test-key",
        model_name="fake-model",
        fail_on_error=True,
    )

    assert stub_module.configured_keys == ["test-key"]
    assert len(stub_module.models) == 1
    model = stub_module.models[0]
    assert model.model_name == "fake-model"
    assert len(model.calls) == len(pages)

    for idx, (image_path, prompt) in enumerate(model.calls):
        expected_path = images_dir / f"page_{idx + 1}.jpg"
        assert image_path == expected_path
        assert prompt == (
            "Extract this page into Markdown, keeping tables, code, and layout. "
            "If this page includes images, refer to them as "
            f"`![Page {idx + 1}]({expected_path})` at the appropriate place in the text."
        )

    assert snippets == [f"## Page {idx + 1}\n\n{responses[idx]}" for idx in range(len(pages))]


def test_end_to_end_processing_with_real_gemini(tmp_path: Path, sample_pdf_path: Path):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not provided in environment")

    real_ptm = _load_pdf_to_markdown_module(stub_genai=False)

    os.environ.setdefault(
        "GRPC_DEFAULT_SSL_ROOTS_FILE_PATH", "/etc/ssl/certs/ca-certificates.crt"
    )

    genai = pytest.importorskip(
        "google.generativeai", reason="google-generativeai package not installed"
    )

    pdf_path = sample_pdf_path
    try:
        pages = real_ptm.split_pdf_to_images(str(pdf_path), dpi=72)
    except PDFInfoNotInstalledError as exc:
        pytest.skip(f"pdf2image dependencies unavailable: {exc}")

    first_page = pages[:1]
    assert first_page, "Expected at least one page from sample PDF"

    images_dir = tmp_path / "real_gemini_images"

    context = ssl.create_default_context()
    try:
        with context.wrap_socket(
            socket.socket(socket.AF_INET), server_hostname="generativelanguage.googleapis.com"
        ) as sock:
            sock.settimeout(5)
            sock.connect(("generativelanguage.googleapis.com", 443))
    except ssl.SSLError as exc:
        pytest.skip(f"Gemini API TLS failure: {exc}")
    except OSError as exc:
        pytest.skip(f"Gemini API network unavailable: {exc}")

    try:
        snippets = real_ptm.extract_markdown_from_pages(
            first_page,
            images_dir=str(images_dir),
            api_key=api_key,
            genai_module=genai,
            model=None,
            fail_on_error=True,
        )
    except Exception as exc:
        message = str(exc)
        if "CERTIFICATE_VERIFY_FAILED" in message:
            pytest.skip(f"Gemini API certificate verification failed: {message}")
        raise

    assert len(snippets) == 1
    assert snippets[0].startswith("## Page 1\n\n")
    assert len(snippets[0].strip().splitlines()) > 1
    expected_image = images_dir / "page_1.jpg"
    assert expected_image.exists()
