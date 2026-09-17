import re
from difflib import SequenceMatcher

from ats.extract import ExtractedPdf, PageGeometry, WordBox
from tools.ats_models import AtsCheck

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
PUA_RE = re.compile(r"[-]")
LIGATURE_RE = re.compile(r"[ﬀ-ﬆ]")
SHORTHAND_YEAR_RE = re.compile(r"'\d{2}\b")
SEASON_YEAR_RE = re.compile(r"\b(?:Spring|Summer|Fall|Winter)\s+\d{4}\b", re.IGNORECASE)
DATE_RANGE_RE = re.compile(
    r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4})"
    r"\s*(?:[-–—]|to)\s*"
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}|Present|Current)\b",
    re.IGNORECASE,
)
BARE_YEAR_RANGE_RE = re.compile(r"\b(?:19|20)\d{2}\s*[-–—]\s*(?:19|20)\d{2}\b")

STANDARD_14_FONTS = {
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    "Symbol", "ZapfDingbats",
}
_SUBSET_TAG_RE = re.compile(r"^[A-Z]{6}\+")


def _base_font_name(name: str) -> str:
    return _SUBSET_TAG_RE.sub("", name.lstrip("/"))


CANONICAL_SECTIONS = {
    "experience": {"experience", "work experience", "professional experience", "employment", "employment history"},
    "education": {"education"},
    "skills": {"skills", "technical skills", "core competencies", "skills & interests", "skills and interests"},
}

RISKY_PRODUCERS = ("canva", "figma", "adobe illustrator", "keynote", "pages")
SAFE_PRODUCERS = ("pdftex", "xetex", "luatex", "libreoffice", "microsoft", "google docs", "wkhtmltopdf")


def _skip_if_encrypted(pdf: ExtractedPdf, id: str, label: str, stage: str) -> AtsCheck | None:
    if not pdf.is_encrypted:
        return None
    return AtsCheck(id=id, label=label, stage=stage, status="skip", weight=0,
                     detail="Skipped — the document is encrypted, so its content can't be inspected.")


def check_encryption(pdf: ExtractedPdf) -> AtsCheck:
    if pdf.is_encrypted:
        return AtsCheck(id="encryption", label="Not password-protected", stage="extraction", status="fail", weight=40,
                         detail="This PDF is encrypted or password-protected. Most ATS parsers reject encrypted "
                                "files outright, before a human ever sees the application.")
    return AtsCheck(id="encryption", label="Not password-protected", stage="extraction", status="pass", weight=40,
                     detail="The PDF is not encrypted.")


def check_text_extractable(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "text_extractable", "Text is extractable", "extraction")
    if skip:
        return skip

    total_chars = sum(p.char_count for p in pdf.pages)
    avg_image_area = sum(p.image_area_fraction for p in pdf.pages) / max(len(pdf.pages), 1)

    if total_chars < 20:
        reason = " and the page is mostly covered by an image" if avg_image_area > 0.3 else ""
        return AtsCheck(id="text_extractable", label="Text is extractable", stage="extraction", status="fail", weight=35,
                         detail=f"Almost no extractable text was found ({total_chars} characters){reason} — this "
                                "looks like a scanned or flattened-image resume. An ATS parser would see essentially nothing.")
    return AtsCheck(id="text_extractable", label="Text is extractable", stage="extraction", status="pass", weight=35,
                     detail=f"Extracted {total_chars} characters of text.")


def check_tounicode_maps(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "tounicode_maps", "Fonts declare ToUnicode maps", "extraction")
    if skip:
        return skip

    # Base-14 standard fonts (Helvetica, Times, Courier, ...) use a fixed standard
    # encoding and never carry /ToUnicode even in a perfectly healthy PDF — only
    # embedded/subset fonts need one to extract reliably.
    relevant = [f for f in pdf.fonts if _base_font_name(f.name) not in STANDARD_14_FONTS]
    if not relevant:
        return AtsCheck(id="tounicode_maps", label="Fonts declare ToUnicode maps", stage="extraction", status="pass",
                         weight=15, detail="Only standard fonts are used, which don't require a /ToUnicode map.")

    missing = [f.name for f in relevant if not f.has_tounicode]
    frac_missing = len(missing) / len(relevant)

    if frac_missing == 0:
        return AtsCheck(id="tounicode_maps", label="Fonts declare ToUnicode maps", stage="extraction", status="pass",
                         weight=15, detail=f"All {len(relevant)} embedded font(s) declare a /ToUnicode CMap, so "
                                           "extracted text should match what's rendered.")
    status = "fail" if frac_missing > 0.5 else "warn"
    return AtsCheck(id="tounicode_maps", label="Fonts declare ToUnicode maps", stage="extraction", status=status,
                     weight=15, evidence=missing[:5],
                     detail=f"{len(missing)} of {len(relevant)} embedded font(s) are missing a /ToUnicode map — text "
                            "set in them can extract as garbled characters even though it displays correctly on screen.")


def check_private_use_glyphs(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "pua_glyphs", "No private-use-area glyphs", "extraction")
    if skip:
        return skip

    matches = sorted(set(PUA_RE.findall(pdf.text)))
    if not matches:
        return AtsCheck(id="pua_glyphs", label="No private-use-area glyphs", stage="extraction", status="pass",
                         weight=8, detail="No private-use-area codepoints (a common source of garbled bullets or "
                                          "icon-font glyphs) were found in the extracted text.")
    return AtsCheck(id="pua_glyphs", label="No private-use-area glyphs", stage="extraction", status="warn", weight=8,
                     evidence=[f"U+{ord(c):04X}" for c in matches[:5]],
                     detail=f"Found {len(matches)} distinct private-use-area codepoint(s) in the extracted text — "
                            "these usually come from custom bullet glyphs or icon fonts and read as garbage to an ATS.")


def check_ligatures(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "ligatures", "No unresolved ligatures", "extraction")
    if skip:
        return skip

    matches = sorted(set(LIGATURE_RE.findall(pdf.text)))
    if not matches:
        return AtsCheck(id="ligatures", label="No unresolved ligatures", stage="extraction", status="pass", weight=5,
                         detail="No ligature characters (e.g. 'ﬁ', 'ﬄ') found in the extracted text.")
    return AtsCheck(id="ligatures", label="No unresolved ligatures", stage="extraction", status="warn", weight=5,
                     evidence=matches[:5],
                     detail=f"Found {len(matches)} ligature character(s) in the extracted text — some keyword "
                            "matchers treat 'efficient' and 'eﬃcient' as different strings.")


def compute_reading_order_fidelity(pdf: ExtractedPdf) -> float:
    """How well a naive top-to-bottom, left-to-right geometric pass over word
    positions agrees with the PDF's own linear text extraction. Low agreement
    usually means a multi-column or table layout that scrambles word order for
    an ATS. This is a proxy, not a ground truth — a well-behaved single-column
    PDF should score close to 1.0."""
    if pdf.is_encrypted or not pdf.pages:
        return 1.0

    linear_tokens = [t.lower() for t in pdf.text.split()]
    geometric_tokens = []
    for page in pdf.pages:
        ordered = sorted(page.words, key=lambda w: (round(w.top / 6), w.x0))
        geometric_tokens.extend(w.text.lower() for w in ordered)

    if not linear_tokens or not geometric_tokens:
        return 1.0

    return round(SequenceMatcher(None, linear_tokens, geometric_tokens).ratio(), 4)


def check_reading_order(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "reading_order", "Reading order fidelity", "reading_order")
    if skip:
        return skip

    fidelity = compute_reading_order_fidelity(pdf)
    if fidelity >= 0.9:
        status = "pass"
    elif fidelity >= 0.7:
        status = "warn"
    else:
        status = "fail"

    return AtsCheck(id="reading_order", label="Reading order fidelity", stage="reading_order", status=status, weight=15,
                     detail=f"Reading-order fidelity is {fidelity:.0%} — how closely the linear text extraction "
                            "matches a strict top-to-bottom, left-to-right pass over word positions. Low fidelity "
                            "usually means a multi-column or table layout that scrambles word order for an ATS.")


def _gutter_spans_many_rows(words: list[WordBox], gutter_x: float, row_tolerance: float = 3.0,
                             min_row_frac: float = 0.5, min_rows: int = 10) -> bool:
    """A real multi-column layout has content on both sides of the gutter on
    nearly every row. A single-column resume that right-aligns dates with
    \\hfill also produces a wide empty band in the page-wide word histogram —
    but only a handful of rows (the ones with a date) actually straddle it.
    Requiring the gutter to hold across most rows, not just in aggregate,
    tells the two apart. A sparse page (e.g. a short overflow onto a second
    page) doesn't have enough rows for that fraction to mean anything, so it's
    required outright rather than just diluting the threshold."""
    rows: dict[int, list[WordBox]] = {}
    for w in words:
        rows.setdefault(round(w.top / row_tolerance), []).append(w)

    if len(rows) < min_rows:
        return False

    straddling = sum(
        1
        for row_words in rows.values()
        if any((w.x0 + w.x1) / 2 < gutter_x for w in row_words)
        and any((w.x0 + w.x1) / 2 > gutter_x for w in row_words)
    )
    return (straddling / len(rows)) >= min_row_frac


def _has_column_gutter(page: PageGeometry, bin_count: int = 50, min_gutter_frac: float = 0.1) -> bool:
    if page.width <= 0 or len(page.words) < 20:
        return False

    bin_width = page.width / bin_count
    occupied = [False] * bin_count
    for w in page.words:
        mid = (w.x0 + w.x1) / 2
        idx = min(max(int(mid / bin_width), 0), bin_count - 1)
        occupied[idx] = True

    min_run = max(2, round(min_gutter_frac * bin_count))
    run_start = None
    for i, is_occupied in enumerate(occupied + [True]):
        if not is_occupied and run_start is None:
            run_start = i
        elif is_occupied and run_start is not None:
            run_len = i - run_start
            if run_len >= min_run and run_start > 0 and i < bin_count:
                gutter_x = (run_start + i) / 2 * bin_width
                if _gutter_spans_many_rows(page.words, gutter_x):
                    return True
            run_start = None
    return False


def check_columns(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "columns", "Single-column layout", "reading_order")
    if skip:
        return skip

    if any(_has_column_gutter(page) for page in pdf.pages):
        return AtsCheck(id="columns", label="Single-column layout", stage="reading_order", status="warn", weight=12,
                         detail="Detected a vertical gap running through the page with text on both sides — this "
                                "looks like a multi-column layout. Many ATS parsers read line-by-line straight "
                                "across columns and scramble the two side by side.")
    return AtsCheck(id="columns", label="Single-column layout", stage="reading_order", status="pass", weight=12,
                     detail="No multi-column layout detected.")


def check_tables(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "tables", "No table-based layout", "reading_order")
    if skip:
        return skip

    pages_with_tables = [i for i, p in enumerate(pdf.pages) if p.has_tables]
    if not pages_with_tables:
        return AtsCheck(id="tables", label="No table-based layout", stage="reading_order", status="pass", weight=8,
                         detail="No table structures detected.")
    return AtsCheck(id="tables", label="No table-based layout", stage="reading_order", status="warn", weight=8,
                     detail=f"Detected table-like structures on {len(pages_with_tables)} page(s) — content inside "
                            "tables (especially a skills grid) is often read out of order or skipped entirely by "
                            "ATS text extraction.")


def check_section_headers(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "section_headers", "Canonical section headers", "segmentation")
    if skip:
        return skip

    lines = {ln.strip().lower() for ln in pdf.text.splitlines() if ln.strip()}
    found = {name for name, synonyms in CANONICAL_SECTIONS.items() if lines & synonyms}
    missing_core = {"experience", "education"} - found

    if missing_core:
        return AtsCheck(id="section_headers", label="Canonical section headers", stage="segmentation", status="fail",
                         weight=10,
                         detail=f"Could not find a standalone section header for: {', '.join(sorted(missing_core))}. "
                                "ATS parsers segment resumes by matching headers against a synonym list — an "
                                "unconventional header name (e.g. 'My Journey' instead of 'Experience') means that "
                                "content may not get parsed into the right field at all.")

    detail = f"Found canonical section headers for: {', '.join(sorted(found))}."
    status = "pass"
    if "skills" not in found:
        status = "warn"
        detail += " No standalone 'Skills' section header was found — consider adding one so ATS keyword extraction can key off it."
    return AtsCheck(id="section_headers", label="Canonical section headers", stage="segmentation", status=status, weight=10, detail=detail)


def check_contact_info(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "contact_info", "Contact info is parseable", "field_extraction")
    if skip:
        return skip

    missing = []
    if not EMAIL_RE.search(pdf.text):
        missing.append("an email address")
    if not PHONE_RE.search(pdf.text):
        missing.append("a phone number")

    if not missing:
        return AtsCheck(id="contact_info", label="Contact info is parseable", stage="field_extraction", status="pass",
                         weight=10, detail="Found an email address and phone number in the extracted text.")
    return AtsCheck(id="contact_info", label="Contact info is parseable", stage="field_extraction", status="fail",
                     weight=10, detail=f"Could not find {' or '.join(missing)} in the extracted text — ATS "
                                       "contact-field extraction would come up empty.")


def check_links_visible(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "links_visible", "Links are visible as text", "field_extraction")
    if skip:
        return skip
    if not pdf.annotation_uris:
        return AtsCheck(id="links_visible", label="Links are visible as text", stage="field_extraction", status="skip",
                         weight=0, detail="No hyperlinks found to check.")

    text_lower = pdf.text.lower()
    invisible = []
    for uri in pdf.annotation_uris:
        target = re.sub(r"^(mailto:|tel:|https?://)", "", uri).rstrip("/")
        if target and target.lower() not in text_lower:
            invisible.append(uri)

    if not invisible:
        return AtsCheck(id="links_visible", label="Links are visible as text", stage="field_extraction", status="pass",
                         weight=5, detail=f"All {len(pdf.annotation_uris)} link(s) are also present as visible text, "
                                          "so plain-text ATS extraction can still pick them up.")
    return AtsCheck(id="links_visible", label="Links are visible as text", stage="field_extraction", status="warn",
                     weight=5, evidence=invisible[:5],
                     detail=f"{len(invisible)} of {len(pdf.annotation_uris)} link(s) are clickable but their target "
                            "never appears as visible text — plain-text extraction will miss them entirely.")


def check_date_ranges(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "date_ranges", "Parseable date ranges", "field_extraction")
    if skip:
        return skip

    issues = []
    if SHORTHAND_YEAR_RE.search(pdf.text):
        issues.append("shorthand two-digit years (e.g. '23)")
    if SEASON_YEAR_RE.search(pdf.text):
        issues.append("season-based dates (e.g. 'Fall 2024') instead of a month")
    if not DATE_RANGE_RE.search(pdf.text) and not BARE_YEAR_RANGE_RE.search(pdf.text):
        issues.append("no clearly formatted date range (Month YYYY – Month YYYY) was found at all")

    if not issues:
        return AtsCheck(id="date_ranges", label="Parseable date ranges", stage="field_extraction", status="pass",
                         weight=6, detail="Date ranges appear to use a consistent, parseable format.")
    return AtsCheck(id="date_ranges", label="Parseable date ranges", stage="field_extraction", status="warn", weight=6,
                     detail="Date formatting that can confuse automatic tenure calculation: " + "; ".join(issues) + ".")


def check_font_size(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "font_size", "Readable font size", "advisory")
    if skip:
        return skip

    sizes = [p.min_font_size for p in pdf.pages if p.min_font_size is not None]
    if not sizes:
        return AtsCheck(id="font_size", label="Readable font size", stage="advisory", status="skip", weight=0,
                         detail="No font size information available.")

    smallest = min(sizes)
    if smallest < 8:
        return AtsCheck(id="font_size", label="Readable font size", stage="advisory", status="warn", weight=4,
                         detail=f"Smallest font size on the page is about {smallest:.1f}pt — text below 8-9pt is "
                                "hard for a recruiter to skim, even though ATS parsers themselves don't care about size.")
    return AtsCheck(id="font_size", label="Readable font size", stage="advisory", status="pass", weight=4,
                     detail=f"Smallest font size is about {smallest:.1f}pt, within a comfortably readable range.")


def check_producer_fingerprint(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "producer_fingerprint", "Safe generating tool", "advisory")
    if skip:
        return skip

    combined = f"{pdf.producer or ''} {pdf.creator or ''}".lower().strip()
    tool_name = pdf.producer or pdf.creator
    if not combined:
        return AtsCheck(id="producer_fingerprint", label="Safe generating tool", stage="advisory", status="skip",
                         weight=0, detail="No PDF producer/creator metadata to check.")

    if any(r in combined for r in RISKY_PRODUCERS):
        return AtsCheck(id="producer_fingerprint", label="Safe generating tool", stage="advisory", status="warn",
                         weight=3, detail=f"This PDF was produced by {tool_name} — design tools like this frequently "
                                          "export text as vector outlines or flattened graphics that ATS parsers "
                                          "can't read at all. Worth double-checking the text-extraction result above.")
    return AtsCheck(id="producer_fingerprint", label="Safe generating tool", stage="advisory", status="pass", weight=3,
                     detail=f"Produced by {tool_name} — no known extraction issues with this tool.")


def check_word_count(pdf: ExtractedPdf) -> AtsCheck:
    skip = _skip_if_encrypted(pdf, "word_count", "Reasonable content length", "advisory")
    if skip:
        return skip

    word_count = len(pdf.text.split())
    if word_count < 150:
        return AtsCheck(id="word_count", label="Reasonable content length", stage="advisory", status="warn", weight=4,
                         detail=f"Only about {word_count} words of extractable content — this may be too sparse for "
                                "keyword-based ATS ranking to have much to match against.")
    if word_count > 1200:
        return AtsCheck(id="word_count", label="Reasonable content length", stage="advisory", status="warn", weight=4,
                         detail=f"About {word_count} words of extractable content — quite long. Consider trimming "
                                "for both ATS keyword density and recruiter attention span.")
    return AtsCheck(id="word_count", label="Reasonable content length", stage="advisory", status="pass", weight=4,
                     detail=f"About {word_count} words of extractable content, a reasonable length.")


def check_page_count(pdf: ExtractedPdf) -> AtsCheck:
    if pdf.page_count > 2:
        return AtsCheck(id="page_count", label="Reasonable page count", stage="advisory", status="warn", weight=3,
                         detail=f"{pdf.page_count} pages — most ATS systems and recruiters expect 1-2 pages for "
                                "early-career roles.")
    return AtsCheck(id="page_count", label="Reasonable page count", stage="advisory", status="pass", weight=3,
                     detail=f"{pdf.page_count} page(s), a typical length.")


CHECKS = [
    check_encryption,
    check_text_extractable,
    check_tounicode_maps,
    check_private_use_glyphs,
    check_ligatures,
    check_reading_order,
    check_columns,
    check_tables,
    check_section_headers,
    check_contact_info,
    check_links_visible,
    check_date_ranges,
    check_font_size,
    check_producer_fingerprint,
    check_word_count,
    check_page_count,
]
