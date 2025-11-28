"""
Semantic Search Service using Gemini File Search API.

This module provides semantic search capabilities through Gemini's File Search API,
enabling vector-based document retrieval that understands meaning and context.
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple
from google import genai
from google.genai import types


class FileSearchManager:
    """Manages Gemini File Search stores."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize File Search Manager.
        
        Args:
            api_key: Google API key. If None, uses GOOGLE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        self.client = genai.Client(api_key=self.api_key)
    
    def create_store(self, display_name: str) -> str:
        """
        Create a new File Search store.
        
        Args:
            display_name: Human-readable name for the store
            
        Returns:
            Store name (ID) for use in subsequent operations
        """
        try:
            store = self.client.file_search_stores.create(
                config={'display_name': display_name}
            )
            return store.name
        except Exception as e:
            raise RuntimeError(f"Failed to create File Search store: {e}")
    
    def list_stores(self) -> List[Dict[str, str]]:
        """
        List all File Search stores.
        
        Returns:
            List of stores with name and display_name
        """
        try:
            stores = []
            for store in self.client.file_search_stores.list():
                stores.append({
                    "name": store.name,
                    "display_name": getattr(store, 'display_name', store.name)
                })
            return stores
        except Exception as e:
            raise RuntimeError(f"Failed to list File Search stores: {e}")
    
    def delete_store(self, store_name: str, force: bool = True) -> bool:
        """
        Delete a File Search store.
        
        Args:
            store_name: Name (ID) of the store to delete
            force: Force delete even if store has documents
            
        Returns:
            True if successful
        """
        try:
            self.client.file_search_stores.delete(
                name=store_name,
                config={'force': force}
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to delete File Search store: {e}")
    
    def get_store(self, store_name: str) -> Dict[str, Any]:
        """
        Get details of a specific File Search store.
        
        Args:
            store_name: Name (ID) of the store
            
        Returns:
            Store details
        """
        try:
            store = self.client.file_search_stores.get(name=store_name)
            return {
                "name": store.name,
                "display_name": getattr(store, 'display_name', store.name)
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get File Search store: {e}")


class SemanticDocStore:
    """Manages documents in Gemini File Search with semantic search capabilities."""
    
    # Chunking configuration
    DEFAULT_MAX_TOKENS_PER_CHUNK = 200
    DEFAULT_MAX_OVERLAP_TOKENS = 20
    
    # Default model for semantic search
    DEFAULT_MODEL = "gemini-2.5-flash"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Document Store.
        
        Args:
            api_key: Google API key. If None, uses GOOGLE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        self.client = genai.Client(api_key=self.api_key)
        self.manager = FileSearchManager(api_key=self.api_key)
    
    def upload_document(
        self,
        file_path: str,
        store_name: str,
        display_name: Optional[str] = None,
        metadata: Optional[List[Dict[str, Any]]] = None,
        max_tokens_per_chunk: int = DEFAULT_MAX_TOKENS_PER_CHUNK,
        max_overlap_tokens: int = DEFAULT_MAX_OVERLAP_TOKENS,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Upload a file directly to File Search store.
        
        Args:
            file_path: Path to the file to upload
            store_name: Name (ID) of the File Search store
            display_name: Display name for the file (used in citations)
            metadata: Custom metadata as list of key-value dicts
            max_tokens_per_chunk: Maximum tokens per chunk
            max_overlap_tokens: Overlap between chunks
            wait_for_completion: Wait for indexing to complete
            
        Returns:
            Operation result with status
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Prepare config
        config = {
            'display_name': display_name or os.path.basename(file_path),
            'chunking_config': {
                'white_space_config': {
                    'max_tokens_per_chunk': max_tokens_per_chunk,
                    'max_overlap_tokens': max_overlap_tokens
                }
            }
        }
        
        # Add metadata if provided
        if metadata:
            config['custom_metadata'] = metadata
        
        try:
            # Upload and import to File Search store
            operation = self.client.file_search_stores.upload_to_file_search_store(
                file=file_path,
                file_search_store_name=store_name,
                config=config
            )
            
            # Wait for completion if requested
            if wait_for_completion:
                while not operation.done:
                    time.sleep(2)
                    operation = self.client.operations.get(operation)
            
            return {
                "success": operation.done,
                "operation_name": operation.name,
                "file_display_name": config['display_name']
            }
        except Exception as e:
            raise RuntimeError(f"Failed to upload document to File Search: {e}")
    
    def import_file(
        self,
        file_name: str,
        store_name: str,
        metadata: Optional[List[Dict[str, Any]]] = None,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Import an already-uploaded file into File Search store.
        
        Args:
            file_name: Name of the file in Files API
            store_name: Name (ID) of the File Search store
            metadata: Custom metadata as list of key-value dicts
            wait_for_completion: Wait for indexing to complete
            
        Returns:
            Operation result with status
        """
        try:
            # Import file into store
            operation = self.client.file_search_stores.import_file(
                file_search_store_name=store_name,
                file_name=file_name,
                custom_metadata=metadata or []
            )
            
            # Wait for completion if requested
            if wait_for_completion:
                while not operation.done:
                    time.sleep(2)
                    operation = self.client.operations.get(operation)
            
            return {
                "success": operation.done,
                "operation_name": operation.name,
                "file_name": file_name
            }
        except Exception as e:
            raise RuntimeError(f"Failed to import file to File Search: {e}")
    
    def search(
        self,
        store_name: str,
        query: str,
        metadata_filter: Optional[str] = None,
        model: str = DEFAULT_MODEL
    ) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
        """
        Perform semantic search on a File Search store.
        
        Args:
            store_name: Name (ID) of the File Search store to search
            query: Search query
            metadata_filter: Optional metadata filter (e.g., "author=John")
            model: Model to use for search
            
        Returns:
            Tuple of (snippets, scores, citations)
        """
        try:
            # Build File Search tool config
            file_search_config = {
                'file_search_store_names': [store_name]
            }
            
            if metadata_filter:
                file_search_config['metadata_filter'] = metadata_filter
            
            # Execute search via generate_content
            response = self.client.models.generate_content(
                model=model,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(**file_search_config)
                        )
                    ]
                )
            )
            
            # Extract results
            snippets, scores, citations = self._extract_search_results(response)
            
            return snippets, scores, citations
        
        except Exception as e:
            raise RuntimeError(f"Failed to perform semantic search: {e}")
    
    def _extract_search_results(
        self,
        response: Any
    ) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
        """
        Extract search results and citations from File Search response.
        
        Args:
            response: Gemini API response object
            
        Returns:
            Tuple of (snippets, scores, citations)
        """
        snippets = []
        scores = []
        citations = []
        
        try:
            # Get grounding metadata if available
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Extract grounding metadata
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding = candidate.grounding_metadata
                    
                    # Extract grounding chunks
                    if hasattr(grounding, 'grounding_chunks'):
                        for chunk in grounding.grounding_chunks:
                            # Extract chunk content
                            if hasattr(chunk, 'web') and chunk.web:
                                snippet_text = getattr(chunk.web, 'title', '') or ''
                            else:
                                snippet_text = str(chunk)
                            
                            snippets.append(snippet_text)
                            
                            # Extract score if available
                            score = getattr(chunk, 'score', 0.5)
                            scores.append(float(score))
                    
                    # Extract grounding supports (citations)
                    if hasattr(grounding, 'grounding_supports'):
                        for support in grounding.grounding_supports:
                            citation = {
                                'segment': getattr(support, 'segment', None),
                                'grounding_chunk_indices': getattr(support, 'grounding_chunk_indices', []),
                                'confidence_scores': getattr(support, 'confidence_scores', [])
                            }
                            citations.append(citation)
            
            # If no structured results, extract from response text
            if not snippets and response.text:
                snippets.append(response.text)
                scores.append(1.0)  # Default high score for response text
        
        except Exception as e:
            print(f"Warning: Failed to extract search results: {e}")
            # Return response text as fallback
            if response.text:
                snippets.append(response.text)
                scores.append(1.0)
        
        return snippets, scores, citations


# Convenience functions for quick usage

def create_file_search_store(display_name: str, api_key: Optional[str] = None) -> str:
    """
    Quick helper to create a File Search store.
    
    Args:
        display_name: Display name for the store
        api_key: Optional API key
        
    Returns:
        Store name (ID)
    """
    manager = FileSearchManager(api_key=api_key)
    return manager.create_store(display_name)


def semantic_search(
    store_name: str,
    query: str,
    api_key: Optional[str] = None
) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
    """
    Quick helper to perform semantic search.
    
    Args:
        store_name: Store name (ID)
        query: Search query
        api_key: Optional API key
        
    Returns:
        Tuple of (snippets, scores, citations)
    """
    store = SemanticDocStore(api_key=api_key)
    return store.search(store_name, query)
