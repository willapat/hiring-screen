import time
import uuid
from dataclasses import dataclass, field
from threading import Lock

from ats.extract import ExtractedPdf


@dataclass
class ResumeRecord:
    resume_id: str
    display_filename: str
    path: str
    extracted: ExtractedPdf
    created_at: float = field(default_factory=time.time)


class ResumeStore:
    """In-process store for uploaded resumes, keyed by resume_id. Not persisted —
    a server restart clears it. This is fine for a single-worker demo deployment
    but means a stale resume_id after a restart should be treated as a 404, not
    an error worth retrying."""

    def __init__(self):
        self._records: dict[str, ResumeRecord] = {}
        self._lock = Lock()

    def put(self, display_filename: str, path: str, extracted: ExtractedPdf) -> ResumeRecord:
        record = ResumeRecord(
            resume_id=uuid.uuid4().hex,
            display_filename=display_filename,
            path=path,
            extracted=extracted,
        )
        with self._lock:
            self._records[record.resume_id] = record
        return record

    def get(self, resume_id: str) -> ResumeRecord | None:
        with self._lock:
            return self._records.get(resume_id)


@dataclass
class LatexBuildRecord:
    build_id: str
    tex_source: str
    pdf_path: str | None
    created_at: float = field(default_factory=time.time)


class LatexBuildStore:
    """In-process store for compiled LaTeX builds, keyed by build_id. Same
    restart caveat as ResumeStore."""

    def __init__(self):
        self._records: dict[str, LatexBuildRecord] = {}
        self._lock = Lock()

    def put(self, tex_source: str, pdf_path: str | None) -> LatexBuildRecord:
        record = LatexBuildRecord(build_id=uuid.uuid4().hex, tex_source=tex_source, pdf_path=pdf_path)
        with self._lock:
            self._records[record.build_id] = record
        return record

    def get(self, build_id: str) -> LatexBuildRecord | None:
        with self._lock:
            return self._records.get(build_id)
