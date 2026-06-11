from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from agents.supervisor import build_graph

load_dotenv()

llm = init_chat_model("gemini-3.1-flash-lite", model_provider="google_genai", temperature=0)
graph = build_graph(llm)

print(graph.get_graph(xray=True).draw_mermaid())
