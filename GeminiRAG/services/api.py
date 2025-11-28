from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any

from .doc_store import GlobalDocStore
from .persistence import load_persisted_documents

try:
    from .semantic_search import FileSearchManager
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

import os
import json


app = FastAPI(title="Document Store API", version="1.0.0")

# --------------------------
# CORS (local dev friendly)
# --------------------------
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Global Document Store
# -------------------------
# Semantic search configuration from environment
SEMANTIC_SEARCH_ENABLED = str(os.getenv("SEMANTIC_SEARCH_ENABLED", "false")).lower() in ("1", "true", "yes", "y")
FILE_SEARCH_STORE_NAME = os.getenv("FILE_SEARCH_STORE_NAME", "GeminiRAG-Store")

# Initialize store with semantic search if enabled
store = GlobalDocStore(
    file_search_store_name=FILE_SEARCH_STORE_NAME if SEMANTIC_SEARCH_ENABLED else None,
    enable_semantic=SEMANTIC_SEARCH_ENABLED
)

# Initialize File Search Manager if available
file_search_manager = None
if SEMANTIC_SEARCH_AVAILABLE and SEMANTIC_SEARCH_ENABLED:
    try:
        file_search_manager = FileSearchManager()
        print(f"[API] File Search Manager initialized")
    except Exception as e:
        print(f"[API] Failed to initialize File Search Manager: {e}")

# -------------------------
# Auto-load knowledge/
# -------------------------
DOC_API_AUTOLOAD = str(os.getenv("DOC_API_AUTOLOAD", "true")).lower() in (
    "1",
    "true",
    "yes",
    "y",
)


def autoload_knowledge():
    """
    Load .txt/.md files from `knowledge/` directory if enabled.
    """
    if not DOC_API_AUTOLOAD:
        return

    root = "knowledge"
    if not os.path.exists(root):
        return

    for fname in os.listdir(root):
        if fname.lower().endswith((".txt", ".md")):
            path = os.path.join(root, fname)
            try:
                text = open(path, "r", encoding="utf-8", errors="ignore").read()

                store.add_document(
                    doc_id=f"auto_{fname.replace('.', '_')}",
                    name=fname,
                    content=text,
                    description=f"Auto-loaded from {fname}",
                )
            except Exception as exc:
                print(f"[API] Failed autoload {fname}: {exc}")


# Load persisted docs at startup
@app.on_event("startup")
def startup():
    load_persisted_documents(store)
    autoload_knowledge()


# -------------------------
# Health
# -------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------
# Add Document
# -------------------------
@app.post("/api/documents/add")
def add_document(payload: Dict[str, Any]):
    required = ["doc_id", "name", "content", "description"]
    for field in required:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    doc_id = payload["doc_id"]
    upload_to_semantic = payload.get("enable_semantic_search", False)

    try:
        store.add_document(
            doc_id=doc_id,
            name=payload["name"],
            content=payload["content"],
            description=payload["description"],
            persist=True,
            upload_to_semantic=upload_to_semantic
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "ok",
        "document": store.get_doc_summary(doc_id),
    }


# -------------------------
# List Documents
# -------------------------
@app.get("/api/documents/list")
def list_documents():
    docs = store.list_documents()
    return {
        "documents": docs,
        "count": len(docs),
    }


# -------------------------
# Search specific document
# -------------------------
@app.post("/api/documents/search")
def search_document(payload: Dict[str, Any]):
    doc_id = payload.get("doc_id")
    question = payload.get("question", "")
    k = int(payload.get("k", 5))

    if doc_id not in store.docs:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    snippets, indices, scores = store.search_document(doc_id, question, k)

    return {
        "snippets": snippets,
        "indices": indices,
        "scores": scores,
        "doc_id": doc_id,
        "doc_name": store.docs[doc_id]["name"],
    }


# -------------------------
# Search across all docs
# -------------------------
@app.post("/api/documents/search_all")
def search_all(payload: Dict[str, Any]):
    question = payload.get("question", "")
    k = int(payload.get("k", 5))

    results = []
    for doc_id in store.docs:
        snippets, indices, scores = store.search_document(doc_id, question, k)
        if snippets:
            results.append(
                {
                    "doc_id": doc_id,
                    "doc_name": store.docs[doc_id]["name"],
                    "snippets": snippets,
                    "indices": indices,
                    "scores": scores,
                }
            )

    return {
        "results": results,
        "total_docs_searched": len(store.docs),
        "docs_with_results": len(results),
    }


# -------------------------
# Semantic Search
# -------------------------
@app.post("/api/documents/search_semantic")
def search_semantic(payload: Dict[str, Any]):
    """Search using semantic search only."""
    if not store.semantic_search_enabled:
        raise HTTPException(
            status_code=501,
            detail="Semantic search is not enabled. Set SEMANTIC_SEARCH_ENABLED=true"
        )
    
    doc_id = payload.get("doc_id")
    question = payload.get("question", "")
    k = int(payload.get("k", 5))
    metadata_filter = payload.get("metadata_filter")
    
    if doc_id and doc_id not in store.docs:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    
    try:
        # Build metadata filter for specific doc if provided
        if doc_id and not metadata_filter:
            metadata_filter = f"doc_id={doc_id}"
        
        snippets, scores, citations = store.semantic_store.search(
            store_name=store.file_search_store_name,
            query=question,
            metadata_filter=metadata_filter
        )
        
        return {
            "snippets": snippets[:k],
            "scores": scores[:k],
            "citations": citations,
            "doc_id": doc_id,
            "doc_name": store.docs[doc_id]["name"] if doc_id else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


# -------------------------
# Hybrid Search
# -------------------------
@app.post("/api/documents/search_hybrid")
def search_hybrid(payload: Dict[str, Any]):
    """Search using hybrid approach (BM25 + semantic)."""
    doc_id = payload.get("doc_id")
    question = payload.get("question", "")
    k = int(payload.get("k", 5))
    bm25_weight = float(payload.get("bm25_weight", 0.4))
    semantic_weight = float(payload.get("semantic_weight", 0.6))
    
    if doc_id not in store.docs:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    
    snippets, indices, scores, individual_scores = store.search_hybrid(
        doc_id, question, k, bm25_weight, semantic_weight
    )
    
    return {
        "snippets": snippets,
        "indices": indices,
        "scores": scores,
        "bm25_scores": individual_scores.get("bm25", []),
        "semantic_scores": individual_scores.get("semantic", []),
        "doc_id": doc_id,
        "doc_name": store.docs[doc_id]["name"],
        "search_type": "hybrid" if store.semantic_search_enabled else "bm25_only",
    }


@app.post("/api/documents/search_all_hybrid")
def search_all_hybrid(payload: Dict[str, Any]):
    """Hybrid search across all documents."""
    question = payload.get("question", "")
    k = int(payload.get("k", 5))
    bm25_weight = float(payload.get("bm25_weight", 0.4))
    semantic_weight = float(payload.get("semantic_weight", 0.6))
    
    results = []
    for doc_id in store.docs:
        snippets, indices, scores, individual_scores = store.search_hybrid(
            doc_id, question, k, bm25_weight, semantic_weight
        )
        if snippets:
            results.append({
                "doc_id": doc_id,
                "doc_name": store.docs[doc_id]["name"],
                "snippets": snippets,
                "indices": indices,
                "scores": scores,
                "bm25_scores": individual_scores.get("bm25", []),
                "semantic_scores": individual_scores.get("semantic", []),
            })
    
    return {
        "results": results,
        "total_docs_searched": len(store.docs),
        "docs_with_results": len(results),
        "search_type": "hybrid" if store.semantic_search_enabled else "bm25_only",
    }


# -------------------------
# File Search Store Management
# -------------------------
@app.post("/api/file_search/create_store")
def create_file_search_store(payload: Dict[str, Any]):
    """Create a new File Search store."""
    if not SEMANTIC_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Semantic search is not available. Install google-genai."
        )
    
    if not file_search_manager:
        raise HTTPException(
            status_code=503,
            detail="File Search Manager not initialized"
        )
    
    display_name = payload.get("display_name", "RAG-Document-Store")
    
    try:
        store_name = file_search_manager.create_store(display_name)
        return {
            "success": True,
            "store_name": store_name,
            "display_name": display_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file_search/list_stores")
def list_file_search_stores():
    """List all File Search stores."""
    if not SEMANTIC_SEARCH_AVAILABLE:
        raise HTTPException(
            status_code=501,
            detail="Semantic search is not available. Install google-genai."
        )
    
    if not file_search_manager:
        raise HTTPException(
            status_code=503,
            detail="File Search Manager not initialized"
        )
    
    try:
        stores = file_search_manager.list_stores()
        return {
            "success": True,
            "stores": stores,
            "count": len(stores)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
