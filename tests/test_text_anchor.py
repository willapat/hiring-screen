from tools.text_anchor import Anchor, build_segments, find_span, normalize_with_map, resolve_anchors


def test_normalize_collapses_whitespace_and_preserves_length_invariant():
    text = "Led  team\r\nof   five\tengineers"
    norm, index_map = normalize_with_map(text)
    assert len(norm) == len(index_map)
    assert "  " not in norm
    assert "\r" not in norm and "\t" not in norm


def test_normalize_expands_ligatures_and_maps_back():
    text = "shipped eﬀicient code"
    norm, index_map = normalize_with_map(text)
    assert "ﬀ" not in norm
    assert "efficient" in norm
    assert len(norm) == len(index_map)


def test_normalize_unifies_dash_and_quote_variants():
    text = "2020– 2021, “shipped it”"
    norm, _ = normalize_with_map(text)
    assert "–" not in norm
    assert "“" not in norm and "”" not in norm


def test_find_span_exact_match():
    text = "Led migration of the billing service to a new provider."
    span = find_span(text, "migration of the billing service")
    assert span is not None
    assert text[span.start:span.end] == "migration of the billing service"


def test_find_span_survives_pdf_whitespace_and_dash_differences():
    text = "Managed a team\nof   five – six engineers"
    span = find_span(text, "team of five - six engineers")
    assert span is not None
    assert "five" in text[span.start:span.end] and "six" in text[span.start:span.end]


def test_find_span_ligature_mismatch_still_resolves():
    text = "Delivered a highly eﬀicient pipeline redesign"
    span = find_span(text, "highly efficient pipeline redesign")
    assert span is not None


def test_find_span_uses_line_hint_to_disambiguate_duplicates():
    text = "Built with Python\nJava backend\nC++ tooling\nBuilt with Python\nRust CLI"
    # "Built with Python" appears on line 1 and line 4 — line_hint must pick the right one.
    span = find_span(text, "Built with Python", line_hint=4)
    assert span is not None
    assert text[:span.start].count("\n") == 3  # resolved on the 4th line


def test_find_span_rejects_too_short_quote():
    assert find_span("some text here", "text") is None


def test_find_span_unresolvable_returns_none():
    text = "Led migration of the billing service."
    assert find_span(text, "invented a time machine for the finance team") is None


def test_find_span_fuzzy_fallback_for_near_verbatim_quote_with_typo():
    text = "Line one\nLine two\nCoordinated cross-fnuctional teams to ship the release\nLine four"
    # Model "corrected" a typo (fnuctional -> functional) instead of copying verbatim.
    span = find_span(text, "Coordinated cross-functional teams to ship the release", line_hint=3)
    assert span is not None


def test_build_segments_covers_whole_document_with_no_gaps():
    text = "AAAA BBBB CCCC"
    resolved = resolve_anchors(text, [Anchor(issue_id="1", quote="BBBB CCCC")])
    segments = build_segments(text, resolved)
    assert "".join(s.text for s in segments) == text


def test_build_segments_tags_overlapping_issues_on_shared_segment():
    text = "The quick brown fox jumps over the lazy dog"
    resolved = [
        ("a", find_span(text, "quick brown fox")),
        ("b", find_span(text, "brown fox jumps")),
    ]
    segments = build_segments(text, resolved)
    assert "".join(s.text for s in segments) == text
    overlap_segments = [s for s in segments if set(s.issue_ids) == {"a", "b"}]
    assert overlap_segments, "expected a segment tagged with both overlapping issues"


def test_build_segments_keeps_unresolved_issues_out_of_segments():
    text = "Short resume text"
    resolved = resolve_anchors(text, [Anchor(issue_id="1", quote="nonexistent phrase entirely")])
    segments = build_segments(text, resolved)
    assert all("1" not in s.issue_ids for s in segments)
    assert "".join(s.text for s in segments) == text
