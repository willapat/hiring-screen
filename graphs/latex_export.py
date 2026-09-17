from typing import Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from tools.ats_models import AtsReport
from tools.resume_models import StructuredResume
import agents.resume_structurer as resume_structurer_agent
import latex.compile as latex_compiler
import latex.render as latex_renderer
from ats.extract import extract as extract_pdf
from ats.report import scan as scan_ats


class LatexExportState(TypedDict):
    resume_text: str
    structured_resume: Optional[StructuredResume]
    tex_source: Optional[str]
    pdf_path: Optional[str]
    pdf_available: Optional[bool]
    compile_log_tail: Optional[str]
    ats_after: Optional[AtsReport]


def build_latex_export_graph(llm):
    def structure_resume(state: LatexExportState):
        return {"structured_resume": resume_structurer_agent.run(llm, state["resume_text"])}

    def render_latex(state: LatexExportState):
        return {"tex_source": latex_renderer.render(state["structured_resume"])}

    def compile_pdf(state: LatexExportState):
        result = latex_compiler.compile_pdf(state["tex_source"])
        return {
            "pdf_path": result.pdf_path,
            "pdf_available": result.pdf_path is not None,
            "compile_log_tail": result.log_tail,
        }

    def verify_ats(state: LatexExportState):
        if not state.get("pdf_path"):
            return {"ats_after": None}
        return {"ats_after": scan_ats(extract_pdf(state["pdf_path"]))}

    builder = StateGraph(LatexExportState)
    builder.add_node("structure_resume", structure_resume)
    builder.add_node("render_latex", render_latex)
    builder.add_node("compile_pdf", compile_pdf)
    builder.add_node("verify_ats", verify_ats)

    builder.add_edge(START, "structure_resume")
    builder.add_edge("structure_resume", "render_latex")
    builder.add_edge("render_latex", "compile_pdf")
    builder.add_edge("compile_pdf", "verify_ats")
    builder.add_edge("verify_ats", END)

    return builder.compile()
