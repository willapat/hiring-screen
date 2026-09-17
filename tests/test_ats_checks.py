from ats import checks
from ats.extract import ExtractedPdf, FontInfo, PageGeometry, WordBox, extract
from ats.report import compute_keyword_coverage, scan
from tests.pdf_builder import build_pdf


def make_pdf(text="", pages=None, **kw) -> ExtractedPdf:
    defaults = dict(
        filename="r.pdf", page_count=1, text=text, layout_text=text,
        pages=pages if pages is not None else [PageGeometry(width=612, height=792)],
        fonts=[], annotation_uris=[], producer=None, creator=None,
        is_encrypted=False, is_tagged=False, language=None,
    )
    defaults.update(kw)
    return ExtractedPdf(**defaults)


CLEAN_RESUME_LINES = [
    "Will Patton",
    "wpatton31@gatech.edu | (404) 578-8071",
    "Experience",
    "Software Engineer Intern Jan 2023 - Dec 2024",
    "Education",
    "Georgia Institute of Technology",
    "Skills",
    "Python, React, SQL",
]


# --- integration: extract() / scan() against a real generated PDF ---

def test_extract_reads_simple_resume(tmp_path):
    path = tmp_path / "resume.pdf"
    path.write_bytes(build_pdf(CLEAN_RESUME_LINES))

    pdf = extract(str(path))
    assert pdf.page_count == 1
    assert "wpatton31@gatech.edu" in pdf.text
    assert not pdf.is_encrypted


def test_scan_scores_clean_resume_highly(tmp_path):
    path = tmp_path / "resume.pdf"
    path.write_bytes(build_pdf(CLEAN_RESUME_LINES))

    report = scan(extract(str(path)))
    statuses = {c.id: c.status for c in report.checks}
    assert report.score >= 80
    assert statuses["encryption"] == "pass"
    assert statuses["contact_info"] == "pass"
    assert statuses["section_headers"] == "pass"
    assert statuses["tounicode_maps"] == "pass"  # standard font, no ToUnicode needed


def test_encrypted_pdf_is_detected(tmp_path):
    path = tmp_path / "locked.pdf"
    path.write_bytes(build_pdf(["Secret resume"], password="hunter2"))

    pdf = extract(str(path))
    assert pdf.is_encrypted is True
    assert checks.check_encryption(pdf).status == "fail"
    assert checks.check_text_extractable(pdf).status == "skip"


# --- unit tests: pure checks against synthetic ExtractedPdf ---

def test_missing_core_sections_fails():
    pdf = make_pdf(text="Will Patton\nSome random text\nNo headers here")
    assert checks.check_section_headers(pdf).status == "fail"


def test_missing_contact_info_fails():
    pdf = make_pdf(text="Experience\nEducation\nNothing to reach me with")
    assert checks.check_contact_info(pdf).status == "fail"


def test_private_use_glyphs_warn():
    pdf = make_pdf(text="Led team  shipped efficient code")
    assert checks.check_private_use_glyphs(pdf).status == "warn"


def test_ligatures_warn():
    pdf = make_pdf(text="shipped eﬀicient code")
    assert checks.check_ligatures(pdf).status == "warn"


def test_shorthand_year_dates_warn():
    pdf = make_pdf(text="Worked there '23 - '24")
    assert checks.check_date_ranges(pdf).status == "warn"


def test_clean_date_range_passes():
    pdf = make_pdf(text="Software Engineer Jan 2023 - Dec 2024")
    assert checks.check_date_ranges(pdf).status == "pass"


def test_risky_producer_warns():
    pdf = make_pdf(producer="Canva")
    assert checks.check_producer_fingerprint(pdf).status == "warn"


def test_safe_producer_passes():
    pdf = make_pdf(producer="pdfTeX-1.40.25")
    assert checks.check_producer_fingerprint(pdf).status == "pass"


def test_too_many_pages_warns():
    pdf = make_pdf(page_count=3)
    assert checks.check_page_count(pdf).status == "warn"


def test_sparse_word_count_warns():
    pdf = make_pdf(text="short resume")
    assert checks.check_word_count(pdf).status == "warn"


def test_two_column_layout_detected():
    words = []
    for i in range(40):
        words.append(WordBox(text=f"L{i}", x0=50, x1=150, top=i * 15, bottom=i * 15 + 10))
        words.append(WordBox(text=f"R{i}", x0=430, x1=550, top=i * 15, bottom=i * 15 + 10))
    page = PageGeometry(width=612, height=792, words=words)
    pdf = make_pdf(text=" ".join(w.text for w in words), pages=[page])
    assert checks.check_columns(pdf).status == "warn"


def test_single_column_layout_passes():
    words = [WordBox(text=f"W{i}", x0=72, x1=150, top=i * 15, bottom=i * 15 + 10) for i in range(40)]
    page = PageGeometry(width=612, height=792, words=words)
    pdf = make_pdf(text=" ".join(w.text for w in words), pages=[page])
    assert checks.check_columns(pdf).status == "pass"


def test_right_aligned_dates_do_not_trigger_false_column_positive():
    # A very common, legitimate resume pattern: \hfill-aligned dates create a
    # wide empty band on a handful of rows (title/date lines), but most rows
    # (wrapped bullets) only have content on the left. This must not be
    # mistaken for a real two-column layout.
    words = []
    for i in range(40):
        words.append(WordBox(text=f"Bullet{i}", x0=50, x1=250, top=i * 15, bottom=i * 15 + 10))
    # Only 3 of 40 rows (title lines) also have a right-aligned date.
    for i in (0, 15, 30):
        words.append(WordBox(text="Jan2024", x0=500, x1=560, top=i * 15, bottom=i * 15 + 10))
    page = PageGeometry(width=612, height=792, words=words)
    pdf = make_pdf(text=" ".join(w.text for w in words), pages=[page])
    assert checks.check_columns(pdf).status == "pass"


def test_table_layout_warns():
    page = PageGeometry(width=612, height=792, has_tables=True)
    pdf = make_pdf(text="some text", pages=[page])
    assert checks.check_tables(pdf).status == "warn"


def test_all_embedded_fonts_missing_tounicode_fails():
    pdf = make_pdf(fonts=[FontInfo(name="/ABCDEF+CustomFont", subtype="/TrueType", has_tounicode=False)])
    assert checks.check_tounicode_maps(pdf).status == "fail"


def test_some_embedded_fonts_missing_tounicode_warns():
    pdf = make_pdf(fonts=[
        FontInfo(name="/ABCDEF+CustomFont", subtype="/TrueType", has_tounicode=False),
        FontInfo(name="/GHIJKL+OtherFont", subtype="/TrueType", has_tounicode=True),
    ])
    assert checks.check_tounicode_maps(pdf).status == "warn"


def test_standard_font_without_tounicode_passes():
    pdf = make_pdf(fonts=[FontInfo(name="/Helvetica", subtype="/Type1", has_tounicode=False)])
    assert checks.check_tounicode_maps(pdf).status == "pass"


# --- keyword coverage ---

def test_keyword_coverage_literal_alias_and_missing():
    coverage = compute_keyword_coverage(
        "Experienced with Python and Kubernetes deployments.",
        ["Python", "K8s", "Rust"],
    )
    assert coverage.covered == ["Python"]
    assert coverage.alias_only == ["K8s"]
    assert coverage.missing == ["Rust"]
