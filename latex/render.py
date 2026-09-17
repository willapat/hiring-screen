from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from latex.filters import tex, texinline, texurl
from tools.resume_models import ContactInfo, StructuredResume

TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    block_start_string="((*",
    block_end_string="*))",
    variable_start_string="((",
    variable_end_string="))",
    comment_start_string="((#",
    comment_end_string="#))",
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    undefined=StrictUndefined,
)
_env.filters["tex"] = tex
_env.filters["texurl"] = texurl
_env.filters["texinline"] = texinline


def _contact_line(contact: ContactInfo) -> str:
    parts = []
    if contact.phone:
        parts.append(tex(contact.phone))
    if contact.location:
        parts.append(tex(contact.location))
    if contact.email:
        parts.append(rf"\href{{mailto:{texurl(contact.email)}}}{{{tex(contact.email)}}}")
    for link in contact.links:
        parts.append(rf"\href{{{texurl(link)}}}{{{tex(link)}}}")
    return " | ".join(parts)


def render(resume: StructuredResume, template_name: str = "resume_classic") -> str:
    template = _env.get_template(f"{template_name}.tex.j2")
    return template.render(
        contact=resume.contact,
        contact_line=_contact_line(resume.contact),
        summary=resume.summary,
        sections=resume.sections,
    )
