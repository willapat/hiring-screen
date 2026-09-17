import shutil

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import ats, job_match, latex, resume, review

load_dotenv()

settings = get_settings()
app = FastAPI(title="Hiring Screen API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume.router, prefix="/api")
app.include_router(ats.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(job_match.router, prefix="/api")
app.include_router(latex.router, prefix="/api")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model": settings.model_name,
        "tectonic_available": shutil.which("tectonic") is not None,
        "llm_enabled": not settings.mock_llm,
    }
