from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama, OllamaEmbeddings
from mcp.server.fastmcp import Context, FastMCP

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VDB_DIR = REPO_ROOT / "dashboards" / "RAGSemanticSearch" / "www"

VDB_CHOICES = {
    "EconomicsAI": "EconomicsAI",
    "JoeRogan": "Joe Rogan & Eric Wienstein",
}

OLLAMA_BASE_URL = os.getenv("ECONOMICS_AI_OLLAMA_URL", "http://localhost:11434")
VDB_BASE_DIR = Path(
    os.getenv("ECONOMICS_AI_VDB_DIR", str(DEFAULT_VDB_DIR))
).expanduser()

_EMBEDDINGS = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url=OLLAMA_BASE_URL,
)
_PROMPT = PromptTemplate.from_template(
    "{template}\n\nContext:\n{context}\n\nQuestion:\n{question}"
)

MCP_DEPENDENCIES = [
    "langchain-community",
    "langchain-core",
    "langchain-ollama",
    "faiss-cpu",
]

mcp = FastMCP(
    "EconomicsAI RAG",
    instructions=(
        "RAG tools backed by local FAISS databases in the configured VDB directory, "
        "using Ollama embeddings and chat models."
    ),
    dependencies=MCP_DEPENDENCIES,
    json_response=True,
    host="127.0.0.1",
    port=5000
)


@lru_cache(maxsize=8)
def _load_faiss(db_id: str) -> FAISS:
    export_dir = VDB_BASE_DIR / db_id
    return FAISS.load_local(
        str(export_dir),
        _EMBEDDINGS,
        allow_dangerous_deserialization=True,
    )


@lru_cache(maxsize=8)
def _load_llm(model: str) -> ChatOllama:
    return ChatOllama(model=model, base_url=OLLAMA_BASE_URL)


def _run_rag_query(
    *,
    db_id: str,
    query: str,
    top_k: int,
    model: str,
    template: str | None,
) -> dict:
    vdb = _load_faiss(db_id)
    rag_docs = vdb.similarity_search(query, k=top_k)
    rag_context = "\n\n----\n\n".join(
        doc.page_content.strip() for doc in rag_docs if doc.page_content
    )
    template_text = template or "Summarize the following text chunks."
    formatted_prompt = _PROMPT.format(
        template=template_text,
        context=rag_context or "No context provided.",
        question=query,
    )
    llm = _load_llm(model)
    response = StrOutputParser().invoke(llm.invoke(formatted_prompt))
    response_text = response.strip() if isinstance(response, str) else str(response)
    return {
        "response": response_text or "",
        "context": rag_context or "",
        "db_id": db_id,
        "model": model,
        "template": template_text,
    }


@mcp.tool()
def rag_query(
    query: str,
    top_k: int = 10,
    model: str = "gemma3:4b",
    db_id: str = "EconomicsAI",
    template: str | None = None,
    ctx: Context | None = None,
) -> dict:
    """Query the EconomicsAI RAG database (or another local FAISS DB)."""
    if ctx is not None:
        ctx.info(
            f"RAG query against {db_id} with model {model} (top_k={top_k})"
        )
    if not query.strip():
        return {
            "response": "",
            "context": "",
            "db_id": db_id,
            "model": model,
            "template": template or "",
            "error": "Query is empty.",
        }
    return _run_rag_query(
        db_id=db_id,
        query=query.strip(),
        top_k=top_k,
        model=model,
        template=template,
    )


@mcp.tool()
def list_databases() -> dict:
    """List available FAISS databases in the VDB directory."""
    available = []
    if VDB_BASE_DIR.exists():
        for entry in sorted(VDB_BASE_DIR.iterdir()):
            if entry.is_dir():
                available.append(entry.name)
    return {
        "vdb_base_dir": str(VDB_BASE_DIR),
        "known_choices": list(VDB_CHOICES.keys()),
        "available": available,
    }

if __name__ == "__main__":
    mcp.run()  # stdio default
