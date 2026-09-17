import os
import re
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from api.config import get_settings
from api.deps import get_store
from ats.extract import PdfExtractionError, extract

router = APIRouter()

_UNSAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9 ._-]")


def _sanitize_filename(name: str | None) -> str:
    name = os.path.basename(name or "resume.pdf")
    name = _UNSAFE_FILENAME_RE.sub("_", name)
    return name[:100] or "resume.pdf"


@router.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    settings = get_settings()

    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    data = bytearray()
    while chunk := await file.read(1024 * 1024):
        data.extend(chunk)
        if len(data) > settings.max_upload_bytes:
            limit_mb = settings.max_upload_bytes // (1024 * 1024)
            raise HTTPException(status_code=413, detail=f"File exceeds the {limit_mb}MB limit.")

    if not bytes(data[:5]) == b"%PDF-":
        raise HTTPException(status_code=400, detail="That doesn't look like a valid PDF file.")

    build_dir = Path(settings.build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(dir=build_dir)
    pdf_path = os.path.join(tmp_dir, "source.pdf")
    with open(pdf_path, "wb") as f:
        f.write(data)

    try:
        extracted = extract(pdf_path)
    except PdfExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    record = get_store().put(_sanitize_filename(file.filename), pdf_path, extracted)

    return {
        "resume_id": record.resume_id,
        "filename": record.display_filename,
        "page_count": extracted.page_count,
        "char_count": len(extracted.text),
        "canonical_text": extracted.text,
        "warnings": ["This document appears to be encrypted."] if extracted.is_encrypted else [],
    }
