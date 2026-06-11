import os
from pypdf import PdfReader


def read_resume(path: str) -> str:
    path = os.path.expanduser(path.strip("'\""))

    if not os.path.exists(path):
        raise FileNotFoundError(f"No file found at: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()

    if ext == ".pdf":
        reader = PdfReader(path)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    raise ValueError(f"Unsupported file type '{ext}'. Use .pdf or .txt.")