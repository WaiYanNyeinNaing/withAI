from __future__ import annotations

"""
HTTP-based retrieval tools.

This module is intentionally generic:
- It shows how you might structure functions that talk to external HTTP services
  (search endpoints, document services, etc.).
- You can plug in your own URLs and authentication.

In a production system, these functions might:
- Call a vector search / RAG service
- Call a document search index
- Call custom HTTP APIs for domain-specific data
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class HttpDocument:
    """
    A generic HTTP document representation returned by a remote service.
    Extend this as needed for your domain.
    """

    doc_id: str
    title: str
    snippet: str
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def _get_base_url() -> str:
    """
    Returns the base URL of your document service.

    In a real setup, this might be in config or env vars.
    """
    # Placeholder. Replace with your own base URL or config source.
    # Example: return os.getenv("DOC_SERVICE_URL", "https://your-doc-service")
    return "http://localhost:8000"  # Defaulting to local service for this setup


def search_documents_http(
    query: str,
    top_k: int = 5,
    timeout: int = 10,
    extra_params: Optional[Dict[str, Any]] = None,
) -> List[HttpDocument]:
    """
    Perform a search against an HTTP-based document/search service.

    Parameters
    ----------
    query:
        The user query or search phrase.
    top_k:
        Maximum number of results to return.
    timeout:
        HTTP timeout in seconds.
    extra_params:
        Additional query parameters to send to the service.

    Returns
    -------
    List[HttpDocument]
        A list of documents that can be used by your agents.
    """
    base_url = _get_base_url()
    url = f"{base_url}/api/documents/search_all" # Updated to match service API

    # The service expects a POST with JSON payload
    payload: Dict[str, Any] = {"question": query, "k": top_k}
    if extra_params:
        payload.update(extra_params)

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # pragma: no cover - you can refine for production
        # In a real app, you'd use logging with more structured context.
        print(f"[http_tools.search_documents_http] Error: {exc}")
        return []

    docs: List[HttpDocument] = []
    # The service returns "results" which is a list of dicts with "snippets"
    for item in data.get("results", []):
        # Flatten snippets into individual HttpDocuments or keep as one?
        # The planner expects snippets.
        # Let's create one HttpDocument per result, joining snippets.
        snippets = "\n...\n".join(item.get("snippets", []))
        docs.append(
            HttpDocument(
                doc_id=str(item.get("doc_id", "")),
                title=item.get("doc_name", ""),
                snippet=snippets,
                url=None, # Service doesn't return URL yet
                metadata={"score": item.get("scores", [])},
            )
        )
    return docs


def get_document_http(doc_id: str, timeout: int = 10) -> Optional[HttpDocument]:
    """
    Fetch a single document by ID via HTTP.

    Parameters
    ----------
    doc_id:
        The document identifier.
    timeout:
        HTTP timeout in seconds.

    Returns
    -------
    Optional[HttpDocument]
        The document if found, otherwise None.
    """
    base_url = _get_base_url()
    # The service doesn't have a direct "get document" endpoint in the provided code,
    # but it has /api/documents/search which takes a doc_id.
    url = f"{base_url}/api/documents/search"

    payload = {"doc_id": doc_id, "k": 100} # Get all chunks

    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        item = resp.json()
    except Exception as exc:  # pragma: no cover
        print(f"[http_tools.get_document_http] Error: {exc}")
        return None

    snippets = "\n".join(item.get("snippets", []))
    return HttpDocument(
        doc_id=str(item.get("doc_id", "")),
        title=item.get("doc_name", ""),
        snippet=snippets,
        url=None,
        metadata={"scores": item.get("scores")},
    )


def list_documents_http(timeout: int = 10) -> List[Dict[str, Any]]:
    """
    List all available documents.
    """
    base_url = _get_base_url()
    url = f"{base_url}/api/documents/list"

    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("documents", [])
    except Exception as exc:
        print(f"[http_tools.list_documents_http] Error: {exc}")
        return []


def search_document_http(
    doc_id: str,
    query: str,
    top_k: int = 5,
    timeout: int = 10,
) -> List[HttpDocument]:
    """
    Search within a specific document.
    """
    base_url = _get_base_url()
    url = f"{base_url}/api/documents/search"
    
    payload = {"doc_id": doc_id, "question": query, "k": top_k}
    
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        item = resp.json()
    except Exception as exc:
        print(f"[http_tools.search_document_http] Error: {exc}")
        return []

    # The API returns snippets. We can return them as separate HttpDocuments or one.
    # The planner expects a list of results.
    docs = []
    snippets = item.get("snippets", [])
    scores = item.get("scores", [])
    
    for i, snippet in enumerate(snippets):
        docs.append(
            HttpDocument(
                doc_id=doc_id,
                title=item.get("doc_name", ""),
                snippet=snippet,
                url=None,
                metadata={"score": scores[i] if i < len(scores) else 0},
            )
        )
    return docs


def search_document_hybrid_http(
    doc_id: str,
    query: str,
    top_k: int = 5,
    bm25_weight: float = 0.4,
    semantic_weight: float = 0.6,
    timeout: int = 10,
) -> List[HttpDocument]:
    """
    Search within a specific document using hybrid approach (BM25 + semantic).
    
    Parameters
    ----------
    doc_id:
        The document identifier.
    query:
        The search query.
    top_k:
        Maximum number of results to return.
    bm25_weight:
        Weight for BM25 scores (0-1).
    semantic_weight:
        Weight for semantic scores (0-1).
    timeout:
        HTTP timeout in seconds.
    
    Returns
    -------
    List[HttpDocument]
        Search results combining BM25 and semantic search.
    """
    base_url = _get_base_url()
    url = f"{base_url}/api/documents/search_hybrid"
    
    payload = {
        "doc_id": doc_id,
        "question": query,
        "k": top_k,
        "bm25_weight": bm25_weight,
        "semantic_weight": semantic_weight
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        item = resp.json()
    except Exception as exc:
        print(f"[http_tools.search_document_hybrid_http] Error: {exc}")
        return []
    
    docs = []
    snippets = item.get("snippets", [])
    scores = item.get("scores", [])
    bm25_scores = item.get("bm25_scores", [])
    semantic_scores = item.get("semantic_scores", [])
    
    for i, snippet in enumerate(snippets):
        metadata = {
            "score": scores[i] if i < len(scores) else 0,
            "bm25_score": bm25_scores[i] if i < len(bm25_scores) else 0,
            "semantic_score": semantic_scores[i] if i < len(semantic_scores) else 0,
            "search_type": item.get("search_type", "unknown")
        }
        docs.append(
            HttpDocument(
                doc_id=doc_id,
                title=item.get("doc_name", ""),
                snippet=snippet,
                url=None,
                metadata=metadata,
            )
        )
    return docs


def search_all_hybrid_http(
    query: str,
    top_k: int = 5,
    bm25_weight: float = 0.4,
    semantic_weight: float = 0.6,
    timeout: int = 10,
) -> List[HttpDocument]:
    """
    Hybrid search across all documents.
    
    Parameters
    ----------
    query:
        The search query.
    top_k:
        Maximum number of results per document.
    bm25_weight:
        Weight for BM25 scores (0-1).
    semantic_weight:
        Weight for semantic scores (0-1).
    timeout:
        HTTP timeout in seconds.
    
    Returns
    -------
    List[HttpDocument]
        Search results from all documents.
    """
    base_url = _get_base_url()
    url = f"{base_url}/api/documents/search_all_hybrid"
    
    payload = {
        "question": query,
        "k": top_k,
        "bm25_weight": bm25_weight,
        "semantic_weight": semantic_weight
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"[http_tools.search_all_hybrid_http] Error: {exc}")
        return []
    
    docs = []
    for item in data.get("results", []):
        snippets = item.get("snippets", [])
        scores = item.get("scores", [])
        
        for i, snippet in enumerate(snippets):
            docs.append(
                HttpDocument(
                    doc_id=str(item.get("doc_id", "")),
                    title=item.get("doc_name", ""),
                    snippet=snippet,
                    url=None,
                    metadata={
                        "score": scores[i] if i < len(scores) else 0,
                        "search_type": data.get("search_type", "unknown")
                    },
                )
            )
    return docs

