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
        from google import genai
        from google.genai import types
        import os
        
        # Get API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {'error': 'GOOGLE_API_KEY not found in environment'}
        
        client = genai.Client(api_key=api_key)
        
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
        prompt = f"""You are an expert AI assistant designed to provide accurate, detailed, and helpful answers based *strictly* on the provided context.

Your goal is to understand the user's intent and provide a comprehensive answer that directly addresses their needs.

Instructions:
1.  **Analyze the Request**: Carefully read the user's question to understand what they are asking.
2.  **Analyze the Context**: Review the provided context to find relevant information.
3.  **Think Step-by-Step**: Formulate a logical answer. Connect different pieces of information from the context.
4.  **Formulate Answer**: Write a detailed answer.
    *   Use clear and professional language.
    *   Use Markdown formatting (bolding, lists, code blocks, tables) to make the answer readable.
    *   If the context contains code, explain it clearly.
    *   **Do NOT** include information that is not present in the context. If the context doesn't contain the answer, state that clearly.

Context:
{context}

Question: {request.query}

Answer:"""
        
        response = client.models.generate_content(
            model="gemini-2.5-pro", # Using gemini-2.5-pro as requested
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    include_thoughts=True
                )
            )
        )
        
        answer = ""
        thoughts = ""
        
        for part in response.candidates[0].content.parts:
            if part.thought:
                thoughts += part.text + "\n"
            else:
                answer += part.text
        
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
            'thoughts': thoughts,
            'sources': sources
        }
    except Exception as e:
        print(f"[Qdrant Test] RAG error: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

@app.post("/ask_stream")
async def ask_question_stream(request: SearchRequest):
    """RAG endpoint with streaming: Search + Synthesize answer with Gemini (streamed)"""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def generate():
        try:
            from google import genai
            from google.genai import types
            import os
            
            # Get API key
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                yield f"data: {json.dumps({'error': 'GOOGLE_API_KEY not found in environment'})}\n\n"
                return
            
            client = genai.Client(api_key=api_key)
            
            print(f"[Qdrant Test] Streaming RAG Query: '{request.query}'")
            
            # Use Hybrid Search for better retrieval
            results = doc_store.hybrid_search(request.query, top_k=request.top_k)
            
            # First, send sources
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
            
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
            
            if not results:
                no_info_msg = "I couldn't find any relevant information in the document store to answer your question."
                yield f"data: {json.dumps({'type': 'content', 'content': no_info_msg})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return
            
            # Build context from search results
            context = "\n\n".join([
                f"[Source {i+1}]: {r['content']}" 
                for i, r in enumerate(results)
            ])
            
            # ============================================================
            # STAGE 1: Initial Thinking (Flash Thinking Model)
            # ============================================================
            yield f"data: {json.dumps({'type': 'stage_marker', 'stage': 1, 'name': 'Initial Thinking'})}\n\n"
            
            stage1_prompt = f"""You are an expert AI assistant. Analyze the user's question and the provided context.

Think step-by-step about:
1. What is the user really asking?
2. What information from the context is relevant?
3. What would be a good initial answer?

Context:
{context}

Question: {request.query}

Provide your thoughts and a draft answer."""
            
            stage1_response = client.models.generate_content_stream(
                model="gemini-2.0-flash-thinking-exp-1219",
                contents=stage1_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=True
                    )
                )
            )
            
            stage1_thoughts = ""
            stage1_draft = ""
            
            for chunk in stage1_response:
                for part in chunk.candidates[0].content.parts:
                    if part.thought:
                        stage1_thoughts += part.text
                        yield f"data: {json.dumps({'type': 'stage1_thinking', 'content': part.text})}\n\n"
                    elif part.text:
                        stage1_draft += part.text
                        yield f"data: {json.dumps({'type': 'stage1_draft', 'content': part.text})}\n\n"
                await asyncio.sleep(0.01)
            
            # ============================================================
            # STAGE 2: Reflection (Pro Model)
            # ============================================================
            yield f"data: {json.dumps({'type': 'stage_marker', 'stage': 2, 'name': 'Reflection'})}\n\n"
            
            stage2_prompt = f"""You are a critical reviewer. Analyze the draft answer below.

User's Question: {request.query}

Draft Answer:
{stage1_draft}

Available Context:
{context}

Your task:
1. Does the draft answer FULLY address the user's intent?
2. Are there any gaps or missing details?
3. Should we ask follow-up questions or retrieve more information?

Provide a brief reflection (2-3 sentences) on the quality and completeness of the draft."""
            
            stage2_response = client.models.generate_content(
                model="gemini-2.5-pro",  # Using Pro for reflection
                contents=stage2_prompt
            )
            
            stage2_reflection = stage2_response.candidates[0].content.parts[0].text
            yield f"data: {json.dumps({'type': 'stage2_reflection', 'content': stage2_reflection})}\n\n"
            
            # ============================================================
            # STAGE 3: Final Synthesis (Pro Model with Thinking)
            # ============================================================
            yield f"data: {json.dumps({'type': 'stage_marker', 'stage': 3, 'name': 'Final Answer'})}\n\n"
            
            stage3_prompt = f"""You are an expert AI assistant. Synthesize a final, comprehensive answer.

User's Question: {request.query}

Context:
{context}

Initial Thoughts:
{stage1_thoughts}

Draft Answer:
{stage1_draft}

Reflection:
{stage2_reflection}

Now, provide a polished, detailed final answer that:
1. Fully addresses the user's intent
2. Incorporates insights from the reflection
3. Uses clear Markdown formatting
4. Stays strictly within the provided context

Final Answer:"""
            
            stage3_response = client.models.generate_content_stream(
                model="gemini-2.5-pro",  # Using Pro for final synthesis
                contents=stage3_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=True
                    )
                )
            )
            
            # Stream the final response
            for chunk in stage3_response:
                for part in chunk.candidates[0].content.parts:
                    if part.thought:
                        yield f"data: {json.dumps({'type': 'stage3_thinking', 'content': part.text})}\n\n"
                    elif part.text:
                        yield f"data: {json.dumps({'type': 'content', 'content': part.text})}\n\n"
                await asyncio.sleep(0.01)
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            print(f"[Qdrant Test] Streaming RAG error: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


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
