"""PDF ingestion, chunking, and metadata enrichment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Iterable

from src.config.settings import PDF_DIR, RAG_DATA_DIR

INDEX_PATH = RAG_DATA_DIR / "document_index.json"
#Check for the parallel execution of retrieval logic and ingestion logic concurrency timelinesto address latency issues for agent response and querying in real time. Address immediately.
#Check on duration of rag generation, storage and retrieval in real time for the agent response and addressing
#Check the pdf ingester and retrieval logic
#Check the concurrency and orchestration of ingester and retrieval to address latency
@dataclass
class DocumentChunk:
    id: str
    text: str
    source_file: str
    document_title: str
    section: str
    page: int
    doc_type: str = "pdf"


def extract_pdf_pages(path: Path) -> list[tuple[int, str]]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = [(index, page.extract_text() or "") for index, page in enumerate(reader.pages, start=1)]
        if any(text.strip() for _, text in pages):
            return pages
    except Exception:
        pass

    raw = path.read_bytes().decode("latin-1", errors="ignore")
    strings = re.findall(r"\(([^()]*)\)\s*Tj", raw)
    text = "\n".join(value.replace("\\(", "(").replace("\\)", ")") for value in strings)
    return [(1, text)]

#Check with chunking logic of text data for logical sequence and fast retrieval...
def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + chunk_size)
        boundary = clean.rfind(". ", start, end)
        if boundary > start + 200:
            end = boundary + 1
        chunks.append(clean[start:end].strip())
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def infer_section(text: str) -> str:
    lowered = text.lower()
    for keyword, section in {
        "return": "Returns",
        "refund": "Refunds",
        "warranty": "Warranty",
        "delivery": "Delivery",
        "shipping": "Delivery",
        "installation": "Installation",
        "setup": "Setup",
        "battery": "Product Fit",
        "camera": "Product Fit",
        "budget": "Product Fit",
    }.items():
        if keyword in lowered:
            return section
    return "General"


def ingest_pdf(path: Path) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    title = path.stem.replace("_", " ").replace("-", " ").title()
    for page_number, text in extract_pdf_pages(path):
        for index, chunk in enumerate(chunk_text(text), start=1):
            chunks.append(
                DocumentChunk(
                    id=f"{path.stem}-p{page_number}-c{index}",
                    text=chunk,
                    source_file=path.name,
                    document_title=title,
                    section=infer_section(chunk),
                    page=page_number,
                )
            )
    return chunks


def ingest_directory(pdf_dir: Path = PDF_DIR) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        chunks.extend(ingest_pdf(pdf_path))
    return chunks


def write_index(chunks: Iterable[DocumentChunk], index_path: Path = INDEX_PATH) -> list[dict]:
    records = [asdict(chunk) for chunk in chunks]
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return records


def build_document_index(pdf_dir: Path = PDF_DIR, index_path: Path = INDEX_PATH) -> list[dict]:
    return write_index(ingest_directory(pdf_dir), index_path)


if __name__ == "__main__":
    records = build_document_index()
    print(f"Ingested {len(records)} PDF chunks into {INDEX_PATH}")

