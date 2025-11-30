import os
from typing import List, Dict, Any
from langchain_experimental.text_splitter import SemanticChunker
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter

class AgenticChunker:
    def __init__(self, strategy: str = "semantic"):
        self.strategy = strategy
        api_key = os.getenv("GOOGLE_API_KEY")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=api_key
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0
        )

    def chunk(self, text: str) -> List[str]:
        if self.strategy == "semantic":
            return self._semantic_chunking(text)
        elif self.strategy == "agentic": # Proposition-based
            return self._proposition_chunking(text)
        else:
            return self._recursive_chunking(text)

    def _recursive_chunking(self, text: str) -> List[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        return splitter.split_text(text)

    def _semantic_chunking(self, text: str) -> List[str]:
        """
        Hybrid semantic chunking: Creates large base chunks then semantically refines them.
        No fallbacks - always uses this approach for consistency.
        """
        # Create larger base chunks using RecursiveCharacterTextSplitter
        base_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        base_chunks = base_splitter.split_text(text)
        
        # For short documents, just return the base chunks
        if len(base_chunks) <= 2:
            return base_chunks
        
        # Apply semantic refinement with stricter thresholds to avoid over-splitting
        semantic_splitter = SemanticChunker(
            self.embeddings,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=90  # Stricter threshold (was 75) to split less often
        )
        
        docs = semantic_splitter.create_documents([text])
        raw_chunks = [doc.page_content.strip() for doc in docs]
        
        # Post-processing: Merge small chunks with neighbors
        # Instead of dropping small chunks (losing content), we merge them
        merged_chunks = []
        current_chunk = ""
        min_chunk_size = 350  # Target minimum size
        
        for chunk in raw_chunks:
            # Skip empty or garbage chunks
            if not chunk or len(set(chunk)) < 10:
                continue
                
            if not current_chunk:
                current_chunk = chunk
            else:
                # If current chunk is too small, or adding the next one keeps it under a reasonable limit
                if len(current_chunk) < min_chunk_size:
                    current_chunk += " " + chunk
                else:
                    # Current chunk is big enough, save it and start new
                    merged_chunks.append(current_chunk)
                    current_chunk = chunk
        
        # Don't forget the last chunk
        if current_chunk:
            # If the last chunk is too small and we have previous chunks, merge with the last one
            if len(current_chunk) < min_chunk_size and merged_chunks:
                merged_chunks[-1] += " " + current_chunk
            else:
                merged_chunks.append(current_chunk)
        
        return merged_chunks if merged_chunks else base_chunks

    def _proposition_chunking(self, text: str) -> List[str]:
        """
        Splits text into propositions using LLM, then chunks them.
        This is a simplified implementation of the "Agentic Chunking" concept.
        """
        # 1. Split into sentences (simple approximation)
        import re
        sentences = re.split(r'(?<=[.!?]) +', text)
        
        # 2. Generate propositions for each sentence (or batch of sentences)
        # For efficiency, we'll process in batches
        batch_size = 5
        propositions = []
        
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i+batch_size]
            batch_text = " ".join(batch)
            
            prompt = f"""
            Break down the following text into atomic, context-independent propositions. 
            Each proposition should be a self-contained sentence.
            Return ONLY the list of propositions, one per line.
            
            Text: {batch_text}
            """
            
            try:
                response = self.llm.invoke(prompt)
                batch_props = response.content.strip().split('\n')
                propositions.extend([p.strip() for p in batch_props if p.strip()])
            except Exception as e:
                print(f"Error generating propositions: {e}")
                propositions.extend(batch) # Fallback to original sentences
        
        # 3. Group propositions semantically
        # We can reuse SemanticChunker on the propositions
        combined_text = "\n".join(propositions)
        return self._semantic_chunking(combined_text)
