import io

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

_ESCAPE = str.maketrans({"\\": "\\\\", "(": "\\(", ")": "\\)"})


def build_pdf(lines: list[str], password: str | None = None) -> bytes:
    """A minimal one-page, single-column PDF containing the given lines of text,
    set in the standard Helvetica font. Built with pypdf's own writer (rather than
    a real fixture file) so tests don't need to commit binary PDFs to the repo."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    font_dict = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = writer._add_object(font_dict)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
    })

    ops = ["BT", "/F1 12 Tf", "72 720 Td"]
    for i, line in enumerate(lines):
        escaped = line.translate(_ESCAPE)
        prefix = "" if i == 0 else "0 -20 Td "
        ops.append(f"{prefix}({escaped}) Tj")
    ops.append("ET")

    stream = DecodedStreamObject()
    stream.set_data("\n".join(ops).encode("latin-1"))
    page[NameObject("/Contents")] = writer._add_object(stream)

    if password is not None:
        writer.encrypt(password)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
