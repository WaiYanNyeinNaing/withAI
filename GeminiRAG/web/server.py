#!/usr/bin/env python3
"""
Standalone Qdrant Semantic Search Test Server
Runs on port 6000
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.vector_store import DocumentStore
from backend.chunking import AgenticChunker

app = FastAPI(title="Qdrant Test Server")

# Initialize DocumentStore (shared with main app)
doc_store = DocumentStore()

class AddDocumentRequest(BaseModel):
    text: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

@app.get("/")
async def index():
    return FileResponse("index.html")

@app.post("/add")
async def add_document(request: AddDocumentRequest):
    try:
        # Chunk the text - always use default (semantic) strategy
        chunker = AgenticChunker(strategy="semantic")
        chunks = chunker.chunk(request.text)
        
        print(f"[Qdrant Test] Chunked text into {len(chunks)} chunks using semantic strategy")
        
        # Create metadata
        metadatas = []
        for i in range(len(chunks)):
            metadatas.append({
                'chunk_index': i,
                'strategy': 'semantic',
                'source': 'test_ui'
            })
        
        # Add to Qdrant
        doc_store.add_documents(texts=chunks, metadatas=metadatas)
        
        print(f"[Qdrant Test] Successfully added {len(chunks)} chunks to vector store")
        
        return {'success': True, 'chunks': len(chunks)}
    except Exception as e:
        print(f"[Qdrant Test] Error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    try:
        from pypdf import PdfReader
        import io
        
        results = []
        total_chunks = 0
        
        print(f"[Qdrant Test] Uploading {len(files)} files")
        
        for file in files:
            try:
                print(f"[Qdrant Test] Processing file: {file.filename}")
                
                # Read file content
                content = await file.read()
                
                # Extract text based on file type
                text = ""
                if file.filename.endswith('.pdf'):
                    # Extract text from PDF
                    pdf_reader = PdfReader(io.BytesIO(content))
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                elif file.filename.endswith(('.txt', '.md')):
                    # Read as text
                    text = content.decode('utf-8')
                else:
                    results.append({'filename': file.filename, 'status': 'skipped', 'reason': 'Unsupported file type'})
                    continue
                
                print(f"[Qdrant Test] Extracted {len(text)} characters from {file.filename}")
                
                # Chunk the text - always use default (semantic) strategy
                chunker = AgenticChunker(strategy="semantic")
                chunks = chunker.chunk(text)
                
                print(f"[Qdrant Test] Chunked into {len(chunks)} chunks using semantic strategy")
                
                # Create metadata
                metadatas = []
                for i in range(len(chunks)):
                    metadatas.append({
                        'chunk_index': i,
                        'strategy': 'semantic',
                        'source': file.filename
                    })
                
                # Add to Qdrant
                doc_store.add_documents(texts=chunks, metadatas=metadatas)
                
                print(f"[Qdrant Test] Successfully added {len(chunks)} chunks from {file.filename}")
                total_chunks += len(chunks)
                results.append({'filename': file.filename, 'status': 'success', 'chunks': len(chunks)})
                
            except Exception as e:
                print(f"[Qdrant Test] Error processing {file.filename}: {e}")
                results.append({'filename': file.filename, 'status': 'error', 'error': str(e)})
        
        return {'success': True, 'results': results, 'total_chunks': total_chunks}
    except Exception as e:
        print(f"[Qdrant Test] Upload error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@app.post("/search")
async def search(request: SearchRequest):
    try:
        print(f"[Qdrant Test] Searching for: '{request.query}' with top_k={request.top_k}")
        # Use Hybrid Search
        results = doc_store.hybrid_search(request.query, top_k=request.top_k)
        
        print(f"[Qdrant Test] Found {len(results)} results")
        for i, r in enumerate(results):
            print(f"  Result {i+1}: score={r.get('score', 'N/A')}, content_length={len(r.get('content', ''))}")
        
        return {'results': results}
    except Exception as e:
        print(f"[Qdrant Test] Search error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

@app.post("/ask")
async def ask_question(request: SearchRequest):
    """RAG endpoint: Search + Synthesize answer with Gemini"""
    try:
        import google.generativeai as genai
        import os
        
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {'error': 'GOOGLE_API_KEY not found in environment'}
        
        genai.configure(api_key=api_key)
        
        print(f"[Qdrant Test] RAG Query: '{request.query}'")
        
        # Use Hybrid Search for better retrieval
        results = doc_store.hybrid_search(request.query, top_k=request.top_k)
        
        if not results:
            return {
                'question': request.query,
                'answer': "I couldn't find any relevant information in the document store to answer your question.",
                'sources': []
            }
        
        # Build context from search results
        context = "\n\n".join([
            f"[Source {i+1}]: {r['content']}" 
            for i, r in enumerate(results)
        ])
        
        # Generate answer with Gemini
        prompt = f"""Based on the following context, provide a detailed and comprehensive answer to the question. 
        Explain the concepts thoroughly, citing specific details from the context where appropriate.
        If the context contains examples, include them in your explanation.

Context:
{context}

Question: {request.query}

Answer:"""
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        answer = response.text
        
        # Format sources
        sources = [
            {
                'content': r['content'],
                'score': r['score'],
                'metadata': r['metadata'],
                'source_type': r.get('source_type', 'unknown'),
                'rank_info': r.get('rank_info', '')
            }
            for r in results
        ]
        
        print(f"[Qdrant Test] Generated answer: {answer[:100]}...")
        
        return {
            'question': request.query,
            'answer': answer,
            'sources': sources
        }
    except Exception as e:
        print(f"[Qdrant Test] RAG error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

@app.get("/stats")
async def stats():
    try:
        collection_info = doc_store.client.get_collection(doc_store.collection_name)
        return {
            'collection_name': doc_store.collection_name,
            'points_count': collection_info.points_count,
            'vector_size': collection_info.config.params.vectors.size
        }
    except Exception as e:
        print(f"[Qdrant Test] Stats error: {e}")
        return {'error': str(e)}

@app.post("/clear")
async def clear_collection():
    """Delete all documents from the collection"""
    try:
        print(f"[Qdrant Test] Clearing all documents from collection: {doc_store.collection_name}")
        
        # Delete the collection and recreate it
        doc_store.client.delete_collection(collection_name=doc_store.collection_name)
        
        # Recreate the collection
        from qdrant_client.models import Distance, VectorParams
        doc_store.client.create_collection(
            collection_name=doc_store.collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        
        print(f"[Qdrant Test] Collection cleared and recreated")
        
        return {'success': True, 'message': 'All documents cleared'}
    except Exception as e:
        print(f"[Qdrant Test] Clear error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    import uvicorn
    print("=" * 60)
    print("🚀 Starting Qdrant Test Server")
    print("   URL: http://localhost:6001")
    print("   This UI allows you to:")
    print("   - Add text documents with different chunking strategies")
    print("   - Search using semantic similarity")
    print("   - View Qdrant collection statistics")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=6001)
