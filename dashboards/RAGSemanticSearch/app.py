from functools import lru_cache
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaEmbeddings, ChatOllama

from shiny import App, reactive, render, ui

VDB_CHOICES = {
    "EconomicsAI": "EconomicsAI",
    "JoeRogan": "Joe Rogan & Eric Wienstein",
}

VDB_CHOICES_INV = {v:k for (k, v) in VDB_CHOICES.items()}

_EMBEDDINGS = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)
_PROMPT = PromptTemplate.from_template(
    "{template}\n\nContext:\n{context}\n\nQuestion:\n{question}"
)


@lru_cache(maxsize=8)
def _load_faiss(db_id: str) -> FAISS:
    export_dir = Path("./www") / db_id
    return FAISS.load_local(
        str(export_dir),
        _EMBEDDINGS,
        allow_dangerous_deserialization=True,
    )


@lru_cache(maxsize=8)
def _load_llm(model: str):
    return ChatOllama(model=model, base_url="http://localhost:11434")


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h2("Parameters"),
        ui.input_select(
            "db",
            "Database",
            choices=VDB_CHOICES,
        ),
        ui.input_select(
            "model",
            "Ollama model",
            choices=[
                "gemma3:4b",
                "gemma3:12b",
                "gemma3:27b",
                "gpt-oss:20b",
            ],
        ),
        ui.input_numeric(
            "top_k",
            label="Number of nearest neighbors",
            value=10,          # default value
            min=1,
            max=100,
            step=1,
        ),
        ui.input_action_button("run", "Run"),
        open="always",
    ),
    ui.tags.style(
        """
        :root {
            color-scheme: light;
        }
        body {
            background: linear-gradient(135deg, #faf7f1 0%, #efe9df 100%);
            font-family: "IBM Plex Serif", "Georgia", serif;
        }
        .sidebar {
            background: #f6efe2;
            border-right: 1px solid #e1d8c8;
        }
        .main-stack {
            display: flex;
            flex-direction: column;
            height: calc(100vh - 2rem);
            gap: 1rem;
            padding: 0.5rem 0.25rem 1.5rem;
        }
        .panel-card {
            background: #ffffff;
            border: 1px solid #e1d8c8;
            border-radius: 14px;
            padding: 1rem 1.25rem;
            box-shadow: 0 12px 30px rgba(79, 52, 15, 0.08);
        }
        .input-panel {
            flex: 1 1 33%;
        }
        .output-panel {
            flex: 2 1 67%;
            overflow: auto;
            background: #fffaf2;
        }
        .btn-primary {
            background: #2e2a24;
            border-color: #2e2a24;
        }
        """
    ),
    ui.div(
        {"class": "main-stack"},
        # ── INPUT PANEL ───────────────────────────────────────────────────────
        ui.div(
            {"class": "panel-card input-panel"},
            ui.h3("Input"),
            ui.layout_columns(
                ui.input_text_area(
                    "query",
                    "Query",
                    placeholder="Ask a question or paste a document snippet...",
                    rows=6,
                ),
                ui.input_text_area(
                    "template",
                    "Prompt template",
                    placeholder="Summarize the following text chunks.",
                    rows=4,
                ),
                col_widths=(6, 6),
            ),
        ),
        # ── OUTPUT PANEL ────────────────────────────────────────────────────────
        ui.div(
            {"class": "panel-card output-panel"},
            ui.h3("LLM Output"),
            ui.output_ui("llm_md"),
        ),
    ),
    title="Ollama Semantic Search",
)


def server(input, output, session):
    result_md = reactive.Value("")

    @reactive.effect
    @reactive.event(input.run)
    def _build_response():
        prompt = input.query().strip()
        template = input.template().strip()
        if not prompt:
            result_md.set("*Awaiting input.*")
            return

        vdb = _load_faiss(input.db())
        rag_docs = vdb.similarity_search(prompt, k=input.top_k())
        rag_context = "\n\n----\n\n".join(
            doc.page_content.strip() for doc in rag_docs if doc.page_content
        )
        template_text = (
            template or "Summarize the following text chunks."
        )
        formatted_prompt = _PROMPT.format(
            template=template_text,
            context=rag_context or "No context provided.",
            question=prompt,
        )
        llm = _load_llm(input.model())
        #response = llm.invoke(formatted_prompt)
        response = StrOutputParser().invoke(llm.invoke(formatted_prompt))
        response_text = response.strip() if isinstance(response, str) else str(response)
        result_md.set(
            "\n".join(
                [
                    f"**Database:** {VDB_CHOICES[input.db()]}",
                    f"**Model:** {input.model()}",
                    f"**Template:** {template or '_default_'}",
                    "\n",
                    "---",
                    "\n",
                    "### Response",
                    response_text or "_No response returned._",
                    "\n",
                    '---',
                    "### RAG context",
                    rag_context or "_No context returned._",
                    "",
                ]
            )
        )

    @render.ui
    def llm_md():
        current = result_md.get()
        if not current:
            return ui.markdown("*Awaiting input.*")
        return ui.markdown(current)


app = App(app_ui, server)
