"""LangChain Runnable backed by a local ChromaDB knowledge collection."""

from __future__ import annotations

import hashlib
import json
import math
import re
from functools import lru_cache
from typing import Any

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool

from src.config.settings import CHROMA_DIR, DATA_DIR, RAG_DATA_DIR, settings

COLLECTION_NAME = "ecombot_kb_v2"
EMBEDDING_DIMENSIONS = 256


def _embedding(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        vector[index] += 1.0 if digest[4] % 2 == 0 else -1.0
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


def _records() -> list[dict[str, Any]]:
    products = json.loads((DATA_DIR / "products.json").read_text(encoding="utf-8"))
    faqs = json.loads((DATA_DIR / "faq.json").read_text(encoding="utf-8"))
    index_path = RAG_DATA_DIR / "document_index.json"
    chunks = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    records: list[dict[str, Any]] = []
    for product in products:
        text = " ".join(
            [
                product["id"], product["sku"], product["name"], product["brand"], product["category"],
                str(product["price_inr"]), product["best_for"], *product["features"], *product["pros"], *product["cons"],
            ]
        )
        records.append({"id": f"product:{product['id']}", "type": "product", "source": product["id"], "text": text, "data": product})
    for faq in faqs:
        text = f"{faq['category']} {faq['question']} {faq['answer']} {' '.join(faq.get('keywords', []))}"
        records.append({"id": f"faq:{faq['id']}", "type": "faq", "source": faq["id"], "text": text, "data": faq})
    for chunk in chunks:
        records.append({"id": f"document:{chunk['id']}", "type": "document", "source": chunk["id"], "text": chunk["text"], "data": chunk})
    return records


def rebuild_chroma() -> int:
    import chromadb

    records = _records()
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(COLLECTION_NAME, metadata={"embedding": "sha256-token-v1"})
    collection.upsert(
        ids=[record["id"] for record in records],
        documents=[record["text"] for record in records],
        embeddings=[_embedding(record["text"]) for record in records],
        metadatas=[
            {
                "type": record["type"],
                "source": record["source"],
                "payload": json.dumps(record["data"]),
            }
            for record in records
        ],
    )
    get_rag_chain.cache_clear()
    return len(records)


class LangChainChromaRetriever:
    def __init__(self) -> None:
        import chromadb

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = client.get_or_create_collection(COLLECTION_NAME)
        if self.collection.count() == 0:
            rebuild_chroma()
            self.collection = client.get_or_create_collection(COLLECTION_NAME)
        self.runnable = RunnableLambda(self._retrieve, name="ecombot_chroma_retriever")
        self.tool = StructuredTool.from_function(
            func=self.search,
            name="search_ecombot_knowledge",
            description="Search the grounded eComBot product, FAQ, and policy knowledge base.",
        )

    def _retrieve(self, request: dict[str, Any]) -> list[Document]:
        query = str(request.get("query", ""))
        top_k = int(request.get("top_k", settings.rag_top_k))
        if not query.strip() or self.collection.count() == 0:
            return []
        result = self.collection.query(query_embeddings=[_embedding(query)], n_results=max(1, top_k))
        documents: list[Document] = []
        for text, metadata, distance in zip(
            result.get("documents", [[]])[0],
            result.get("metadatas", [[]])[0],
            result.get("distances", [[]])[0],
        ):
            if not metadata or "payload" not in metadata:
                continue
            if distance is not None and float(distance) > 1.75:
                continue
            documents.append(Document(page_content=text, metadata={**metadata, "distance": distance}))
        return documents

    def search(self, query: str, top_k: int = 4) -> list[dict[str, Any]]:
        documents = self.runnable.invoke({"query": query, "top_k": top_k})
        return [
            {
                "type": document.metadata["type"],
                "source": document.metadata["source"],
                "text": document.page_content,
                "data": json.loads(document.metadata["payload"]),
                "distance": document.metadata.get("distance"),
            }
            for document in documents
        ]


@lru_cache(maxsize=1)
def get_rag_chain() -> LangChainChromaRetriever:
    return LangChainChromaRetriever()
