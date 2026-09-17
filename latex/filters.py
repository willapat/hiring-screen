import re

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_LIGATURE_PAIR_RE = re.compile(r"f(?=[fil])")

_TEX_SPECIAL_CHARS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex(value: str | None) -> str:
    """Escape a plain string for safe inclusion in LaTeX source. This is the
    security boundary between user/LLM-controlled resume content and the TeX
    compiler — every user-controlled string must pass through this before it
    reaches a template. Characters are mapped one at a time from the original
    string, so a backslash introduced by escaping (e.g. in \\textbackslash{})
    is never re-scanned and re-escaped."""
    if not value:
        return ""

    value = _CONTROL_CHARS_RE.sub("", value)
    value = value.replace("–", "--").replace("—", "---")
    value = value.replace("‘", "`").replace("’", "'")
    value = value.replace("“", "``").replace("”", "''")

    escaped = "".join(_TEX_SPECIAL_CHARS.get(ch, ch) for ch in value)

    # Break ff/fi/fl ligatures with an empty group. TeX forms ligatures purely
    # from adjacent character codes in the font's ligature table — inserting
    # `{}` breaks that adjacency in any engine. This matters because a ligature
    # glyph can extract as a single private-use/compatibility codepoint instead
    # of the original letters, which is exactly what several ATS checks flag.
    # microtype's \DisableLigatures only works under pdfTeX, not the XeTeX
    # engine tectonic uses, so this has to happen at the text level instead.
    return _LIGATURE_PAIR_RE.sub("f{}", escaped)


def texurl(value: str | None) -> str:
    """Escape a URL for use inside \\href{...}. Never run `tex()` on a URL —
    backslash-escaping breaks the link. hyperref parses \\href's first
    argument under special URL-safe catcodes, but a literal `%` (comment
    character) or `#` (macro parameter character) can still break parsing, so
    those two are percent-encoded instead."""
    if not value:
        return ""

    value = _CONTROL_CHARS_RE.sub("", value)
    return value.replace("%", "%25").replace("#", "%23")


def texinline(value: str) -> str:
    """Promotes a small safe markup subset in already-`tex()`-escaped text:
    **bold** becomes \\textbf{...}. Must run after `tex()`, not before — the
    inner content needs to already be escaped by the time it's wrapped."""
    return _BOLD_RE.sub(lambda m: r"\textbf{" + m.group(1) + "}", value)
