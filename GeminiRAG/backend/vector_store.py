import os
from typing import List, Dict, Any, Optional
from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

class DocumentStore:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.collection_name = "gemini_rag_docs"
        self.qdrant_path = os.path.join(os.path.dirname(__file__), "..", "qdrant_db")
        
        # Initialize Qdrant Client
        self.client = QdrantClient(path=self.qdrant_path)
        
        # Ensure collection exists (from original code, adapted)
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )

        # Initialize Vector Store
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        
        # Initialize BM25
        self.bm25 = None
        self.bm25_corpus = []
        self.bm25_mapping = []
        self._load_bm25()

    def _load_bm25(self):
        """Load or rebuild BM25 index from Qdrant"""
        try:
            print("[DocumentStore] Rebuilding BM25 index from Qdrant...")
            # Fetch all documents from Qdrant
            # Note: For large collections, this should be done in batches or cached to disk
            all_docs = []
            next_offset = None
            
            while True:
                records, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=100,
                    offset=next_offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                for record in records:
                    if record.payload and 'page_content' in record.payload:
                        all_docs.append({
                            'content': record.payload['page_content'],
                            'metadata': record.payload.get('metadata', {})
                        })
                
                if not next_offset:
                    break
            
            if all_docs:
                self.bm25_corpus = [doc['content'].lower().split() for doc in all_docs]
                self.bm25_mapping = []
                for i, doc in enumerate(all_docs):
                    self.bm25_mapping.append({
                        'content': doc['content'],
                        'metadata': doc['metadata'],
                        'id': i
                    })
                
                from rank_bm25 import BM25Okapi
                self.bm25 = BM25Okapi(self.bm25_corpus)
                print(f"[DocumentStore] BM25 index rebuilt with {len(all_docs)} documents")
            else:
                print("[DocumentStore] No documents found in Qdrant to build BM25 index")
                
        except Exception as e:
            print(f"[DocumentStore] Error loading BM25: {e}")
            import traceback
            traceback.print_exc()

    def add_documents(self, texts: List[str], metadatas: List[dict]):
        # Add to Qdrant
        self.vector_store.add_texts(texts, metadatas=metadatas)
        
        # Update BM25 Index
        self.bm25_corpus.extend([text.lower().split() for text in texts])
        
        # Store mapping
        start_idx = len(self.bm25_mapping)
        for i, (text, meta) in enumerate(zip(texts, metadatas)):
            self.bm25_mapping.append({
                'content': text,
                'metadata': meta,
                'id': start_idx + i
            })
            
        # Rebuild BM25
        if self.bm25_corpus:
            from rank_bm25 import BM25Okapi
            self.bm25 = BM25Okapi(self.bm25_corpus)
            print(f"[DocumentStore] BM25 index updated with {len(texts)} new documents")

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Legacy semantic search"""
        docs = self.vector_store.similarity_search_with_score(query, k=top_k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata, "score": score}
            for doc, score in docs
        ]

    def hybrid_search(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[dict]:
        """
        Hybrid Search: Combines Semantic Search (Qdrant) and Keyword Search (BM25)
        Returns a combined list of unique results (up to top_k * 2)
        """
        # 1. Semantic Search
        semantic_results = self.search(query, top_k=top_k)
        for res in semantic_results:
            res['source_type'] = 'semantic'
            res['rank_info'] = f"Semantic Score: {res['score']:.4f}"
        
        # 2. Keyword Search (BM25)
        bm25_results = []
        if self.bm25:
            tokenized_query = query.lower().split()
            # Get top N scores
            doc_scores = self.bm25.get_scores(tokenized_query)
            # Get top indices
            top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
            
            for idx in top_indices:
                if doc_scores[idx] > 0:
                    entry = self.bm25_mapping[idx]
                    bm25_results.append({
                        "content": entry['content'],
                        "metadata": entry['metadata'],
                        "score": doc_scores[idx],
                        "source_type": 'bm25',
                        "rank_info": f"BM25 Score: {doc_scores[idx]:.4f}"
                    })
        
        # 3. Combine Results (Deduplicate by content)
        combined_results = []
        seen_content = set()
        
        # Add semantic results first
        for res in semantic_results:
            if res['content'] not in seen_content:
                combined_results.append(res)
                seen_content.add(res['content'])
                
        # Add BM25 results
        for res in bm25_results:
            if res['content'] not in seen_content:
                combined_results.append(res)
                seen_content.add(res['content'])
            else:
                # If already exists (from semantic), update info to show it matched both
                for existing in combined_results:
                    if existing['content'] == res['content']:
                        existing['source_type'] = 'hybrid'
                        existing['rank_info'] += f" | BM25 Score: {res['score']:.4f}"
                        break
        
        return combined_results

    def delete_collection(self):
        """Delete the entire collection (useful for reset)."""
        self.client.delete_collection(self.collection_name)
