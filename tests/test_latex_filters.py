from latex.filters import tex, texinline, texurl


def test_tex_escapes_special_characters():
    assert tex("100% & $5 #1 _under_ {brace}") == r"100\% \& \$5 \#1 \_under\_ \{brace\}"


def test_tex_escapes_backslash_without_double_escaping():
    assert tex("C:\\path") == r"C:\textbackslash{}path"


def test_tex_handles_tilde_and_caret():
    assert tex("~/repo^2") == r"\textasciitilde{}/repo\textasciicircum{}2"


def test_tex_converts_dashes_and_smart_quotes():
    assert tex("2020\u20132021 \u201cquoted\u201d") == "2020--2021 ``quoted''"


def test_tex_strips_control_characters():
    assert tex("hello\x00world\x1f!") == "helloworld!"


def test_tex_handles_none_and_empty_as_empty_string():
    assert tex(None) == ""
    assert tex("") == ""


def test_tex_breaks_ligature_forming_letter_pairs():
    # TeX would otherwise typeset "fi"/"fl"/"ff" as a single ligature glyph,
    # which can extract as a different codepoint than the original letters.
    assert tex("efficient") == "ef{}f{}icient"
    assert tex("flow") == "f{}low"
    assert tex("office") == "of{}f{}ice"


def test_tex_prevents_command_injection():
    # A resume field containing raw LaTeX must not be able to close its
    # enclosing group and invoke another command.
    payload = "}\\input{/etc/passwd}{"
    escaped = tex(payload)
    assert payload not in escaped
    assert "\\input{" not in escaped


def test_texurl_percent_encodes_percent_and_hash():
    assert texurl("https://example.com/a%b#c") == "https://example.com/a%25b%23c"


def test_texurl_does_not_backslash_escape():
    # A backslash-escaped URL breaks the hyperlink -- texurl must never do this.
    assert "\\%" not in texurl("https://example.com/50%off")


def test_texurl_strips_control_characters():
    assert texurl("https://example.com/\x00path") == "https://example.com/path"


def test_texurl_handles_none_and_empty_as_empty_string():
    assert texurl(None) == ""
    assert texurl("") == ""


def test_texinline_promotes_bold_markers():
    assert texinline("Led a **critical** migration") == r"Led a \textbf{critical} migration"


def test_texinline_runs_safely_after_escaping():
    escaped = tex("**100% done**")
    assert texinline(escaped) == r"\textbf{100\% done}"
