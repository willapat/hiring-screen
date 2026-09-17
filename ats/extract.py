import os
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field

import pdfplumber
from pypdf import PdfReader

MAX_PAGES = 10
EXTRACTION_TIMEOUT_SECONDS = 15


class PdfExtractionError(ValueError):
    pass


@dataclass
class WordBox:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float


@dataclass
class FontInfo:
    name: str
    subtype: str | None
    has_tounicode: bool


@dataclass
class PageGeometry:
    width: float
    height: float
    words: list[WordBox] = field(default_factory=list)
    image_area_fraction: float = 0.0
    char_count: int = 0
    min_font_size: float | None = None
    has_tables: bool = False


@dataclass
class ExtractedPdf:
    filename: str
    page_count: int
    text: str
    layout_text: str
    pages: list[PageGeometry]
    fonts: list[FontInfo]
    annotation_uris: list[str]
    producer: str | None
    creator: str | None
    is_encrypted: bool
    is_tagged: bool
    language: str | None


_CRLF_RE = re.compile(r"\r\n?")
_TRAILING_WS_RE = re.compile(r"[ \t]+\n")
_BLANK_RUN_RE = re.compile(r"\n{3,}")


def canonicalize(text: str) -> str:
    """The single normalization pass every downstream consumer shares — ATS checks,
    the review LLM, span anchoring, and the frontend. Deliberately light: it only
    standardizes whitespace. It must NOT fold ligatures, smart quotes, or
    private-use-area glyphs, since several ATS checks exist specifically to detect
    those (a Word bullet extracting as a PUA codepoint, a ligature breaking a
    keyword match) — normalizing them away here would erase the evidence."""
    text = _CRLF_RE.sub("\n", text)
    text = _TRAILING_WS_RE.sub("\n", text)
    text = _BLANK_RUN_RE.sub("\n\n", text)
    return text.strip()


def extract(path: str) -> ExtractedPdf:
    if not os.path.exists(path):
        raise PdfExtractionError(f"No file found at: {path}")

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_extract_sync, path)
        try:
            return future.result(timeout=EXTRACTION_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            raise PdfExtractionError(
                "PDF took too long to parse — it may be malformed or a decompression bomb."
            )
        except PdfExtractionError:
            raise
        except Exception as e:
            raise PdfExtractionError(f"Could not parse PDF: {e}") from e


def _extract_sync(path: str) -> ExtractedPdf:
    filename = os.path.basename(path)
    reader = PdfReader(path)

    # Accessing .pages on an undecrypted reader raises, so encryption must be
    # resolved first. decrypt() reports failure via its return value (a falsy
    # PasswordType.NOT_DECRYPTED), not by raising.
    is_encrypted = reader.is_encrypted
    if is_encrypted:
        try:
            is_encrypted = not bool(reader.decrypt(""))
        except Exception:
            is_encrypted = True

    if is_encrypted:
        try:
            page_count = len(reader.pages)
        except Exception:
            page_count = 0
        return ExtractedPdf(
            filename=filename,
            page_count=page_count,
            text="",
            layout_text="",
            pages=[],
            fonts=[],
            annotation_uris=[],
            producer=None,
            creator=None,
            is_encrypted=True,
            is_tagged=False,
            language=None,
        )

    try:
        page_count = len(reader.pages)
    except Exception as e:
        raise PdfExtractionError(f"Could not read page structure: {e}") from e

    if page_count > MAX_PAGES:
        raise PdfExtractionError(f"PDF has {page_count} pages — refusing to parse more than {MAX_PAGES}.")

    text_parts = []
    layout_parts = []
    fonts: list[FontInfo] = []
    annotation_uris: list[str] = []

    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
        try:
            layout_parts.append(page.extract_text(extraction_mode="layout") or "")
        except Exception:
            layout_parts.append("")
        fonts.extend(_extract_fonts(page))
        annotation_uris.extend(_extract_annotation_uris(page))

    root = reader.trailer.get("/Root") or {}
    mark_info = root.get("/MarkInfo")
    is_tagged = bool(mark_info and mark_info.get("/Marked"))
    language = root.get("/Lang")

    meta = reader.metadata
    producer = str(meta.producer) if meta and meta.producer else None
    creator = str(meta.creator) if meta and meta.creator else None

    return ExtractedPdf(
        filename=filename,
        page_count=page_count,
        text=canonicalize("\n".join(text_parts)),
        layout_text=canonicalize("\n".join(layout_parts)),
        pages=_extract_geometry(path),
        fonts=fonts,
        annotation_uris=annotation_uris,
        producer=producer,
        creator=creator,
        is_encrypted=False,
        is_tagged=is_tagged,
        language=str(language) if language else None,
    )


def _extract_fonts(page) -> list[FontInfo]:
    fonts = []
    resources = page.get("/Resources")
    font_dict = resources.get("/Font") if resources else None
    if not font_dict:
        return fonts

    for font_ref in font_dict.values():
        try:
            font_obj = font_ref.get_object()
        except Exception:
            continue
        name = str(font_obj.get("/BaseFont", "unknown"))
        subtype = str(font_obj.get("/Subtype")) if font_obj.get("/Subtype") else None
        has_tounicode = "/ToUnicode" in font_obj
        fonts.append(FontInfo(name=name, subtype=subtype, has_tounicode=has_tounicode))

    return fonts


def _extract_annotation_uris(page) -> list[str]:
    uris = []
    annots = page.get("/Annots")
    if not annots:
        return uris

    for annot_ref in annots:
        try:
            action = annot_ref.get_object().get("/A")
            if action and action.get("/URI"):
                uris.append(str(action["/URI"]))
        except Exception:
            continue

    return uris


def _extract_geometry(path: str) -> list[PageGeometry]:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = [
                WordBox(text=w["text"], x0=w["x0"], x1=w["x1"], top=w["top"], bottom=w["bottom"])
                for w in page.extract_words(keep_blank_chars=False)
            ]
            chars = page.chars
            font_sizes = [c["size"] for c in chars if "size" in c]
            page_area = (page.width or 0) * (page.height or 0)
            image_area = sum((img["width"] or 0) * (img["height"] or 0) for img in page.images)

            try:
                has_tables = bool(page.find_tables())
            except Exception:
                has_tables = False

            pages.append(PageGeometry(
                width=page.width or 0,
                height=page.height or 0,
                words=words,
                image_area_fraction=min(image_area / page_area, 1.0) if page_area else 0.0,
                char_count=len(chars),
                min_font_size=min(font_sizes) if font_sizes else None,
                has_tables=has_tables,
            ))

    return pages
