"""Generate a local PDF explaining the capstone implementation."""

from __future__ import annotations

from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "ecombot_capstone_functionality.pdf"

CONTENT = [
    ("ADK Capstone eComBot", [
        "This document explains the fully integrated eComBot capstone implementation.",
        "Deterministic mode runs without paid model keys; live ADK, LiteLLM, and LangSmith modes are environment-controlled.",
    ]),
    ("Implemented Modules", [
        "Day 01-02: support agent foundation, prompt variants, and domain boundaries.",
        "Day 03: order tools and in-memory session state for customer name, last order, and last product.",
        "Day 04: active Redis session persistence, PostgreSQL business tools, and durable turn history.",
        "Day 05-06: LangChain Runnable RAG over product, FAQ, and PDF records stored in ChromaDB.",
        "Day 07: real LiteLLM completion routing with primary and fallback providers.",
        "Day 08: real FastMCP client/server order and inventory tool execution.",
        "Day 09: Sales Agent ReAct reasoning and reflection after rejected recommendations.",
        "Final hardening: Google ADK multi-agent tree, LangSmith tracing, 12 Promptfoo cases, CI/CD, guardrails, voice adapters, and Chainlit UI.",
    ]),
    ("Agents", [
        "Support Agent handles order status, cancellation, invoices, inventory, product lookup, and grounded policy answers.",
        "Sales Agent handles recommendations, comparisons, ReAct reasoning, and reflection.",
        "Orchestrator routes between support and sales, applies guardrails, filters output, and records traces.",
    ]),
    ("Tools and Backend Calls", [
        "Order tools: get_order_status, cancel_order, and get_invoice validate order IDs and return structured data.",
        "Product tools: lookup_product, check_stock, list_variants, and catalog filtering use the local product corpus.",
        "FastMCP client invokes a real in-process or HTTP FastMCP server with structured results.",
    ]),
    ("RAG and PDF Ingestion", [
        "Products and FAQ are stored as rich JSON source documents.",
        "PDF knowledge documents are extracted, chunked with overlap, tagged with source file, title, section, page, and doc_type metadata, and written to document_index.json.",
        "LangChain RunnableLambda and StructuredTool components query ChromaDB using deterministic local embeddings and confidence filtering.",
    ]),
    ("Model Routing", [
        "The gateway route classifier chooses fast-faq for simple support traffic and deep-support for comparisons, recommendations, complaints, and multi-step decisions.",
        "LiteLLM performs real completion calls and provider fallback in live mode; the proxy config supports OpenAI primary and OpenRouter fallback.",
    ]),
    ("Security and Observability", [
        "Input guardrail blocks prompt injection, role override, system prompt extraction, and data exfiltration attempts.",
        "Output guardrail redacts email addresses, phone numbers, and unsupported competitor references without redacting delivery dates.",
        "LangSmith traceable runs capture agent execution when configured; JSONL tracing remains always available locally.",
        "Promptfoo evaluates 12 support, sales, RAG, MCP, reflection, and security cases through the same FastAPI runtime.",
    ]),
    ("How to Execute Locally", [
        "Install base dependencies: python -m pip install -r requirements.txt",
        "Build local RAG index: python -m src.rag.embed_catalog",
        "Run scenario: python run_agent.py --scenario",
        "Run evals: python run_agent.py --eval",
        "Run tests: python -m pytest -q",
        "Run Chainlit UI: chainlit run src/ui/app.py -w",
        "Run API: python -m uvicorn src.api.app:app --port 8001",
        "Run Promptfoo: npm run eval",
        "Run Rancher stack: docker compose up --build -d",
    ]),
]


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_minimal_pdf(lines: list[str], path: Path) -> None:
    """Small dependency-free PDF writer used when reportlab is unavailable."""
    path.parent.mkdir(parents=True, exist_ok=True)

    lines_per_page = 48
    pages = [lines[index : index + lines_per_page] for index in range(0, len(lines), lines_per_page)]
    if not pages:
        pages = [["ADK Capstone eComBot Documentation"]]

    objects: list[str] = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
    ]

    page_object_numbers: list[int] = []
    content_object_numbers: list[int] = []
    next_object_number = 3

    for page_lines in pages:
        page_object_numbers.append(next_object_number)
        content_object_numbers.append(next_object_number + 1)
        next_object_number += 2

        y = 750
        commands = []
        for line in page_lines:
            safe_line = _escape(line[:105])
            commands.append(f"BT /F1 10 Tf 54 {y} Td ({safe_line}) Tj ET")
            y -= 14
        stream = "\n".join(commands)
        stream_bytes = stream.encode("latin-1", errors="replace")

        page_number = page_object_numbers[-1]
        content_number = content_object_numbers[-1]
        objects.append(
            f"{page_number} 0 obj\n"
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_number} 0 R "
            "/Resources << /Font << /F1 999 0 R >> >> >>\n"
            "endobj\n"
        )
        objects.append(
            f"{content_number} 0 obj\n"
            f"<< /Length {len(stream_bytes)} >>\n"
            "stream\n"
            f"{stream}\n"
            "endstream\n"
            "endobj\n"
        )

    font_object_number = next_object_number
    kids = " ".join(f"{number} 0 R" for number in page_object_numbers)
    pages_object = f"2 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>\nendobj\n"
    font_object = (
        f"{font_object_number} 0 obj\n"
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        "endobj\n"
    )

    objects.insert(1, pages_object)
    objects.append(font_object)
    objects = [obj.replace("999 0 R", f"{font_object_number} 0 R") for obj in objects]

    body = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(body.encode("latin-1")))
        body += obj

    xref_offset = len(body.encode("latin-1"))
    xref = ["xref", f"0 {len(objects) + 1}", "0000000000 65535 f "]
    xref.extend(f"{offset:010d} 00000 n " for offset in offsets[1:])
    trailer = "\n".join(xref)
    trailer += f"\ntrailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref_offset}\n%%EOF\n"
    path.write_bytes((body + trailer).encode("latin-1", errors="replace"))


def build_lines() -> list[str]:
    lines: list[str] = []
    for heading, paragraphs in CONTENT:
        lines.append(heading)
        lines.append("")
        for paragraph in paragraphs:
            for wrapped in textwrap.wrap(paragraph, width=92):
                lines.append(f"- {wrapped}")
        lines.append("")
    return lines


def main() -> None:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(OUTPUT), pagesize=letter)
        width, height = letter
        y = height - 54
        c.setFont("Helvetica", 10)
        for line in build_lines():
            if y < 54:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 54
            c.drawString(54, y, line[:115])
            y -= 14
        c.save()
    except Exception:
        _write_minimal_pdf(build_lines(), OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
