"""Port-Interfaces für Retrieval-Service (Hexagonal Architecture)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetrievedDoc:
    """Ein einzelnes Retrieval-Ergebnis."""

    source: str
    source_id: str
    title: str
    text_snippet: str
    similarity_score: float
    metadata: dict[str, str]


class VectorSearchPort(ABC):
    """Abstraktes Interface für Vektor-/Hybrid-Suche."""

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        technology: str,
        sources: list[str],
        top_k: int,
        threshold: float,
    ) -> list[RetrievedDoc]:
        """Führt Hybrid-Search (Keyword + Vektor) durch."""


class SparseSearchPort(ABC):
    """Abstraktes Interface für Sparse/BM25-Suche."""

    @abstractmethod
    async def search(
        self,
        query: str,
        sources: list[str],
        top_k: int,
    ) -> list[RetrievedDoc]:
        """Führt BM25/Full-Text-Suche durch.

        Gibt RetrievedDoc mit ts_rank als similarity_score zurück.
        """


class QueryEmbeddingPort(ABC):
    """Abstraktes Interface für Query-Embedding."""

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Erzeugt Embedding für eine einzelne Query."""


class RerankingPort(ABC):
    """Abstraktes Interface für Reranking von Retrieval-Ergebnissen."""

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[RetrievedDoc],
        top_k: int,
    ) -> list[RetrievedDoc]:
        """Rerankt Dokumente nach Relevanz zur Query. Gibt top_k zurück."""
