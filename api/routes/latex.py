import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.deps import get_latex_graph, get_latex_store, get_store
from ats.report import scan as scan_ats
from tools.ats_models import AtsReport

router = APIRouter()


class LatexBuildRequest(BaseModel):
    resume_id: str


class LatexBuildResponse(BaseModel):
    build_id: str
    tex: str
    pdf_available: bool
    compile_log_tail: str | None = None
    ats_before: AtsReport
    ats_after: AtsReport | None = None


@router.post("/latex/build", response_model=LatexBuildResponse)
async def build_latex(body: LatexBuildRequest):
    record = get_store().get(body.resume_id)
    if not record:
        raise HTTPException(status_code=404, detail="Unknown resume_id — it may have expired after a server restart.")

    ats_before = scan_ats(record.extracted)

    graph = get_latex_graph()
    result = await graph.ainvoke({"resume_text": record.extracted.text})

    build_record = get_latex_store().put(result["tex_source"], result.get("pdf_path"))

    return LatexBuildResponse(
        build_id=build_record.build_id,
        tex=result["tex_source"],
        pdf_available=bool(result.get("pdf_available")),
        compile_log_tail=result.get("compile_log_tail"),
        ats_before=ats_before,
        ats_after=result.get("ats_after"),
    )


@router.get("/latex/{build_id}/resume.tex")
def get_tex(build_id: str):
    record = get_latex_store().get(build_id)
    if not record:
        raise HTTPException(status_code=404, detail="Unknown build_id — it may have expired after a server restart.")
    return Response(content=record.tex_source, media_type="text/x-tex")


@router.get("/latex/{build_id}/resume.pdf")
def get_pdf(build_id: str):
    record = get_latex_store().get(build_id)
    if not record or not record.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not available for this build.")

    # pdf_path always comes from tempfile.mkdtemp(), never from user input, but
    # assert containment before serving a file off disk regardless. Resolve
    # both sides — on macOS /var is itself a symlink to /private/var, so an
    # unresolved gettempdir() would never match a resolved path.
    resolved = Path(record.pdf_path).resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    if not resolved.is_relative_to(temp_root):
        raise HTTPException(status_code=400, detail="Invalid build.")

    # content_disposition_type="inline" is the fix here — FileResponse defaults
    # to "attachment" whenever a filename is given, which forces a download on
    # every request to this URL, including the <iframe> preview load. The
    # actual "Download .pdf" button still works: its <a download> attribute
    # forces a save regardless of this header.
    return FileResponse(resolved, media_type="application/pdf", filename="resume.pdf", content_disposition_type="inline")
