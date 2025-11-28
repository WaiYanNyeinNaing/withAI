import threading
import json
import os
from typing import List, Tuple, Dict, Optional
from rank_bm25 import BM25Okapi

try:
    from .semantic_search import SemanticDocStore
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    print("Warning: Semantic search not available")


class GlobalDocStore:
    """
    Thread-safe in-memory document store.

    Each document is chunked into text segments,
    which are then searchable using Jaccard similarity + term-frequency.
    """

    def __init__(self, file_search_store_name: Optional[str] = None, enable_semantic: bool = False):
        self.lock = threading.RLock()
        self.docs = {}  # doc_id -> metadata + chunks
        self.bm25_indices: Dict[str, BM25Okapi] = {}  # doc_id -> BM25 index
        
        # Semantic search configuration
        self.file_search_store_name = file_search_store_name
        self.semantic_search_enabled = enable_semantic and SEMANTIC_SEARCH_AVAILABLE
        self.semantic_store = None
        
        if self.semantic_search_enabled:
            try:
                self.semantic_store = SemanticDocStore()
                print(f"Semantic search enabled with store: {file_search_store_name}")
            except Exception as e:
                print(f"Failed to initialize semantic search: {e}")
                self.semantic_search_enabled = False

    # -------------------------
    # Document Management
    # -------------------------
    def add_document(self, doc_id: str, name: str, content: str, description: str, persist=False, upload_to_semantic=False):
        if not content or not content.strip():
            raise ValueError("Document content cannot be empty")

        with self.lock:
            chunks = self._chunk_text(content)

            self.docs[doc_id] = {
                "id": doc_id,
                "name": name,
                "description": description,
                "content": content,
                "chunks": chunks,
            }

            # Build BM25 index for this document
            self._build_bm25_index(doc_id)

            # Upload to semantic search if enabled
            if upload_to_semantic and self.semantic_search_enabled and self.file_search_store_name:
                try:
                    # Save content to temp file for upload
                    temp_path = f"temp_{doc_id}.txt"
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Upload to File Search
                    result = self.semantic_store.upload_document(
                        file_path=temp_path,
                        store_name=self.file_search_store_name,
                        display_name=name,
                        metadata=[
                            {"key": "doc_id", "string_value": doc_id},
                            {"key": "description", "string_value": description}
                        ]
                    )
                    
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    
                    print(f"Uploaded {doc_id} to semantic search: {result}")
                except Exception as e:
                    print(f"Failed to upload {doc_id} to semantic search: {e}")

            if persist:
                self._persist_document(doc_id, name, description, content)

    def list_documents(self) -> List[Dict]:
        with self.lock:
            return [
                {
                    "id": d["id"],
                    "name": d["name"],
                    "description": d["description"],
                    "chunk_count": len(d["chunks"]),
                }
                for d in self.docs.values()
            ]

    def get_doc_summary(self, doc_id: str) -> Dict:
        d = self.docs[doc_id]
        return {
            "id": d["id"],
            "name": d["name"],
            "description": d["description"],
            "chunk_count": len(d["chunks"]),
        }

    # -------------------------
    # Chunking
    # -------------------------
    def _chunk_text(self, text: str, max_len=800) -> List[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []

        for p in paragraphs:
            if len(p) <= max_len:
                chunks.append(p)
            else:
                # sentence split fallback
                sentences = [s.strip() for s in p.split(". ") if s.strip()]
                buf = ""
                for s in sentences:
                    if len(buf) + len(s) + 2 <= max_len:
                        buf += s + ". "
                    else:
                        if buf:
                            chunks.append(buf.strip())
                        buf = s + ". "
                if buf:
                    chunks.append(buf.strip())

        return chunks

    # -------------------------
    # Search
    # -------------------------
    def search_document(self, doc_id: str, query: str, k: int) -> Tuple[List[str], List[int], List[float]]:
        # Ensure BM25 index exists for the document
        if doc_id not in self.bm25_indices:
            self._build_bm25_index(doc_id)

        bm25 = self.bm25_indices[doc_id]
        query_tokens = self._tokenize(query)
        scores = bm25.get_scores(query_tokens)

        # Get top-k indices sorted by score descending
        top_idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        snippets = [self.docs[doc_id]["chunks"][i] for i in top_idxs]
        indices = top_idxs
        top_scores = [scores[i] for i in top_idxs]
        return snippets, indices, top_scores

    # -------------------------
    # Helpers
    # -------------------------
    def _tokenize(self, text: str) -> List[str]:
        return [t.lower() for t in text.split() if t.strip()]

    # Build BM25 index for a given document ID
    def _build_bm25_index(self, doc_id: str) -> None:
        chunks = self.docs[doc_id]["chunks"]
        tokenized_chunks = [self._tokenize(chunk) for chunk in chunks]
        self.bm25_indices[doc_id] = BM25Okapi(tokenized_chunks)
    
    # -------------------------
    # Hybrid Search
    # -------------------------
    def search_hybrid(
        self,
        doc_id: str,
        query: str,
        k: int,
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6
    ) -> Tuple[List[str], List[int], List[float], Dict[str, List[float]]]:
        """
        Perform hybrid search combining BM25 and semantic search.
        
        Args:
            doc_id: Document ID to search
            query: Search query
            k: Number of top results to return
            bm25_weight: Weight for BM25 scores (0-1)
            semantic_weight: Weight for semantic scores (0-1)
            
        Returns:
            Tuple of (snippets, indices, combined_scores, individual_scores_dict)
        """
        if not self.semantic_search_enabled or not self.file_search_store_name:
            # Fallback to BM25 only
            snippets, indices, scores = self.search_document(doc_id, query, k)
            return snippets, indices, scores, {"bm25": scores, "semantic": []}
        
        # Get BM25 results
        bm25_snippets, bm25_indices, bm25_scores = self.search_document(doc_id, query, k * 2)
        
        # Get semantic search results
        try:
            # Search using semantic store with metadata filter for this doc
            metadata_filter = f"doc_id={doc_id}"
            semantic_results, semantic_scores_raw, citations = self.semantic_store.search(
                store_name=self.file_search_store_name,
                query=query,
                metadata_filter=metadata_filter
            )
        except Exception as e:
            print(f"Semantic search failed, falling back to BM25: {e}")
            snippets, indices, scores = self.search_document(doc_id, query, k)
            return snippets, indices, scores, {"bm25": scores, "semantic": []}
        
        # Normalize scores
        bm25_norm = self._normalize_scores(bm25_scores)
        semantic_norm = self._normalize_scores(semantic_scores_raw) if semantic_scores_raw else []
        
        # Create a mapping of chunks to their scores
        chunk_scores = {}
        
        # Add BM25 scores
        for idx, score_norm in zip(bm25_indices, bm25_norm):
            chunk_text = self.docs[doc_id]["chunks"][idx]
            if chunk_text not in chunk_scores:
                chunk_scores[chunk_text] = {"bm25": 0.0, "semantic": 0.0, "index": idx}
            chunk_scores[chunk_text]["bm25"] = score_norm
        
        # Add semantic scores by matching text
        for result_text, score_norm in zip(semantic_results, semantic_norm):
            # Try to find matching chunk
            best_match_chunk = None
            best_match_score = 0.0
            
            for chunk_text in chunk_scores:
                # Simple overlap matching
                overlap = len(set(result_text.lower().split()) & set(chunk_text.lower().split()))
                if overlap > best_match_score:
                    best_match_score = overlap
                    best_match_chunk = chunk_text
            
            if best_match_chunk:
                chunk_scores[best_match_chunk]["semantic"] = score_norm
        
        # Combine scores
        combined_results = []
        for chunk_text, scores_dict in chunk_scores.items():
            combined_score = (
                bm25_weight * scores_dict["bm25"] +
                semantic_weight * scores_dict["semantic"]
            )
            combined_results.append({
                "text": chunk_text,
                "index": scores_dict["index"],
                "combined_score": combined_score,
                "bm25_score": scores_dict["bm25"],
                "semantic_score": scores_dict["semantic"]
            })
        
        # Sort by combined score and take top k
        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
        top_results = combined_results[:k]
        
        # Extract final results
        final_snippets = [r["text"] for r in top_results]
        final_indices = [r["index"] for r in top_results]
        final_scores = [r["combined_score"] for r in top_results]
        
        individual_scores = {
            "bm25": [r["bm25_score"] for r in top_results],
            "semantic": [r["semantic_score"] for r in top_results]
        }
        
        return final_snippets, final_indices, final_scores, individual_scores
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            scores: Raw scores
            
        Returns:
            Normalized scores (0-1)
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same
            return [1.0] * len(scores)
        
        # Min-max normalization
        normalized = [(s - min_score) / (max_score - min_score) for s in scores]
        return normalized

    # -------------------------
    # Persistence
    # -------------------------
    def _persist_document(self, doc_id: str, name: str, description: str, content: str):
        os.makedirs("documents", exist_ok=True)

        path = os.path.join("documents", f"{doc_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "id": doc_id,
                    "name": name,
                    "description": description,
                    "content": content,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
