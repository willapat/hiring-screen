from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from agents.supervisor import build_graph
from graphs.job_match import build_job_match_graph
from graphs.latex_export import build_latex_export_graph
from graphs.resume_audit import build_resume_audit_graph

load_dotenv()

llm = init_chat_model("gemini-3.1-flash-lite", model_provider="google_genai", temperature=0)

graph = build_graph(llm)
job_match_graph = build_job_match_graph(llm)
resume_audit_graph = build_resume_audit_graph(llm)
latex_export_graph = build_latex_export_graph(llm)
