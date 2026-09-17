import bisect
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

MIN_QUOTE_LEN = 8
MAX_QUOTE_LEN = 400
LINE_WINDOW = 2
FUZZY_MIN_RATIO = 0.8

_DASH_VARIANTS = {"‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "−": "-"}
_QUOTE_VARIANTS = {"‘": "'", "’": "'", "“": '"', "”": '"'}


@dataclass
class Span:
    start: int
    end: int


@dataclass
class Anchor:
    issue_id: str
    quote: str
    line: int | None = None


@dataclass
class Segment:
    text: str
    issue_ids: list[str]


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """NFKC-normalize, casefold, and collapse whitespace, returning the result
    alongside a list mapping each of its characters back to its offset in the
    original text. Matching happens against the normalized string; spans are
    reported in terms of the original one, via this map."""
    out_chars: list[str] = []
    index_map: list[int] = []
    prev_was_space = False

    for i, ch in enumerate(text):
        decomposed = unicodedata.normalize("NFKC", ch)
        decomposed = _DASH_VARIANTS.get(decomposed, decomposed)
        decomposed = _QUOTE_VARIANTS.get(decomposed, decomposed)

        if decomposed.isspace():
            if not prev_was_space:
                out_chars.append(" ")
                index_map.append(i)
            prev_was_space = True
            continue

        prev_was_space = False
        for dch in decomposed:
            for lch in dch.lower():
                out_chars.append(lch)
                index_map.append(i)

    return "".join(out_chars), index_map


def _line_start_offsets(text: str) -> list[int]:
    offsets = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def find_span(text: str, quote: str, line_hint: int | None = None) -> Span | None:
    """Resolve a verbatim (or near-verbatim) quote to a span in `text`. Tries an
    exact normalized match near `line_hint` first (which is what disambiguates a
    quote that occurs more than once), then anywhere in the document, then a
    fuzzy match within the line-hint window."""
    quote = quote.strip()
    if not (MIN_QUOTE_LEN <= len(quote) <= MAX_QUOTE_LEN):
        return None

    norm_text, index_map = normalize_with_map(text)
    norm_quote, _ = normalize_with_map(quote)
    if not norm_quote:
        return None

    line_offsets = _line_start_offsets(text)

    def to_span(norm_start: int, norm_len: int) -> Span:
        start = index_map[norm_start]
        end = index_map[norm_start + norm_len - 1] + 1
        return Span(start=start, end=end)

    def window_norm_bounds(line_hint: int) -> tuple[int, int]:
        start_line = max(0, line_hint - 1 - LINE_WINDOW)
        end_line = line_hint - 1 + LINE_WINDOW + 1
        char_start = line_offsets[start_line]
        char_end = line_offsets[end_line] if end_line < len(line_offsets) else len(text)
        return bisect.bisect_left(index_map, char_start), bisect.bisect_left(index_map, char_end)

    if line_hint is not None and 1 <= line_hint <= len(line_offsets):
        norm_start, norm_end = window_norm_bounds(line_hint)
        pos = norm_text.find(norm_quote, norm_start, norm_end)
        if pos != -1:
            return to_span(pos, len(norm_quote))

    pos = norm_text.find(norm_quote)
    if pos != -1:
        return to_span(pos, len(norm_quote))

    if line_hint is not None and 1 <= line_hint <= len(line_offsets):
        start_line = max(0, line_hint - 1 - LINE_WINDOW)
        end_line = line_hint - 1 + LINE_WINDOW + 1
        char_start = line_offsets[start_line]
        char_end = line_offsets[end_line] if end_line < len(line_offsets) else len(text)
        window = text[char_start:char_end]

        # A single typo (model paraphrased instead of copying) splits the match
        # into multiple blocks, so span from the first to the last matching
        # block rather than requiring one long contiguous run. The ratio is then
        # taken between that candidate substring and the quote, not the whole
        # window — the window normally contains unrelated neighboring lines that
        # would otherwise dilute a whole-window ratio.
        matcher = SequenceMatcher(None, window, quote)
        blocks = [b for b in matcher.get_matching_blocks() if b.size > 0]
        if blocks:
            span_start = blocks[0].a
            span_end = blocks[-1].a + blocks[-1].size
            candidate = window[span_start:span_end]
            local_ratio = SequenceMatcher(None, candidate, quote).ratio()
            if local_ratio >= FUZZY_MIN_RATIO and span_end - span_start >= MIN_QUOTE_LEN:
                return Span(start=char_start + span_start, end=char_start + span_end)

    return None


def resolve_anchors(text: str, anchors: list[Anchor]) -> list[tuple[str, Span | None]]:
    """Resolve each anchor's quote to a span in `text`. Returns (issue_id, span)
    pairs in the same order as `anchors`; span is None when unresolved — callers
    should keep those as unanchored issues rather than dropping them."""
    return [(a.issue_id, find_span(text, a.quote, a.line)) for a in anchors]


def build_segments(text: str, resolved: list[tuple[str, Span | None]]) -> list[Segment]:
    """Flatten resolved (possibly overlapping) spans into a non-overlapping
    sequence of segments covering the entire document, each tagged with the
    issue ids that cover it. The frontend renders this directly with no
    interval math of its own."""
    spans = [(span, issue_id) for issue_id, span in resolved if span is not None]
    if not spans:
        return [Segment(text=text, issue_ids=[])] if text else []

    boundaries = sorted({0, len(text)} | {s.start for s, _ in spans} | {s.end for s, _ in spans})
    segments = []
    for start, end in zip(boundaries, boundaries[1:]):
        if start >= end:
            continue
        issue_ids = [issue_id for span, issue_id in spans if span.start <= start and end <= span.end]
        segments.append(Segment(text=text[start:end], issue_ids=issue_ids))
    return segments
