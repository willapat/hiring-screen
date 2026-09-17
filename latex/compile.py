import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

COMPILE_TIMEOUT_SECONDS = 60
LOG_TAIL_LINES = 30


@dataclass
class CompileResult:
    pdf_path: str | None
    log_tail: str | None
    engine_available: bool


def is_tectonic_available() -> bool:
    return shutil.which("tectonic") is not None


def compile_pdf(tex_source: str) -> CompileResult:
    """Compile LaTeX source to PDF with tectonic in an isolated temp dir. Never
    shells out to anything derived from user input beyond the .tex file
    contents themselves — tex_source is written to disk and only the file path
    is passed as an argv element."""
    if not is_tectonic_available():
        return CompileResult(pdf_path=None, log_tail=None, engine_available=False)

    workdir = Path(tempfile.mkdtemp(prefix="hiring-screen-latex-"))
    tex_path = workdir / "resume.tex"
    tex_path.write_text(tex_source, encoding="utf-8")

    try:
        proc = subprocess.run(
            ["tectonic", "-X", "compile", str(tex_path), "--outdir", str(workdir), "--untrusted"],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=COMPILE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return CompileResult(pdf_path=None, log_tail="Compilation timed out.", engine_available=True)

    log_lines = (proc.stdout + proc.stderr).splitlines()
    log_tail = "\n".join(log_lines[-LOG_TAIL_LINES:])

    pdf_path = workdir / "resume.pdf"
    if proc.returncode != 0 or not pdf_path.exists():
        return CompileResult(pdf_path=None, log_tail=log_tail, engine_available=True)

    return CompileResult(pdf_path=str(pdf_path), log_tail=log_tail, engine_available=True)
