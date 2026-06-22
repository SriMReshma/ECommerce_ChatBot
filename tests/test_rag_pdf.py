from pathlib import Path

from src.rag.pdf_ingester import build_document_index
from src.rag.retriever import load_document_chunks, retrieve


def test_pdf_ingester_creates_metadata_index(tmp_path):
    index_path = tmp_path / "document_index.json"
    records = build_document_index(index_path=index_path)
    assert records
    assert index_path.exists()
    assert {"source_file", "document_title", "section", "page", "doc_type"}.issubset(records[0])


def test_retrieval_uses_pdf_chunks():
    load_document_chunks.cache_clear()
    chunks = retrieve("non metro delivery takes how many days", top_k=5)
    assert any(chunk["type"] == "document" for chunk in chunks)
