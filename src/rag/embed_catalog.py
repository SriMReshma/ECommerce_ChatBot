"""Refresh the local PDF index and optional ChromaDB collection."""

from __future__ import annotations

from src.rag.pdf_ingester import build_document_index
from src.rag.langchain_rag import rebuild_chroma
from src.rag.retriever import load_document_chunks, load_faq, load_products


def main() -> None:
    records = build_document_index()
    load_document_chunks.cache_clear()
    print(f"Indexed {len(load_products())} products, {len(load_faq())} FAQ entries, {len(records)} PDF chunks.")

    try:
        count = rebuild_chroma()
        print(f"LangChain/ChromaDB collection refreshed with {count} records.")
    except Exception as exc:
        print(f"ChromaDB refresh skipped: {exc}")


if __name__ == "__main__":
    main()
