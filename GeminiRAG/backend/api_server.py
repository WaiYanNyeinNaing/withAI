"""
FastAPI server for GeminiRAG frontend integration.

This server bridges the professional HTML/CSS/JS frontend with the
existing orchestrator backend, providing streaming responses and
file upload handling.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
import os
import io
from pypdf import PdfReader
import sys

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.orchestrator import orchestrate_planner_judge
from backend.agents import create_planner_agent, create_judge_agent
from backend.agents.synthesizer import create_synthesizer_agent
from backend.http_tools import (
    search_documents_http,
    get_document_http,
    list_documents_http,
    search_document_http,
    search_document_hybrid_http,
    search_all_hybrid_http,
)
from backend.models import PlannerResult, JudgeResult, SynthesizerResult
from backend.logger import default_logger
from backend.config import AppConfig, export_google_env
import requests
from google import genai
from google.genai import types

# Initialize FastAPI app
app = FastAPI(title="GeminiRAG API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config = AppConfig.from_env()
export_google_env(config.google_api_key)

# Document service base URL
DOC_SERVICE_URL = "http://localhost:8000"

# Default model
DEFAULT_MODEL = "gemini-2.0-flash"


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateStoreRequest(BaseModel):
    display_name: str = "RAG-Document-Store"


class AskQuestionRequest(BaseModel):
    question: str


# ============================================================================
# Helper Functions
# ============================================================================

def adapt_planner(user_query: str, previous_evidence: Optional[List] = None, last_judge_result=None, is_last_attempt=False, **kwargs):
    """Adapter for planner agent."""
    prompt = f"Question: {user_query}\n"
    
    if last_judge_result and last_judge_result.verdict == "retry":
        prompt += "\nCRITIQUE FROM PREVIOUS ATTEMPT:\n"
        prompt += f"The Judge rejected your previous answer. Reason:\n{last_judge_result.explanation}\n"
        prompt += "You must address this critique. If you need more information, call tools.\n"
    
    if previous_evidence:
        prompt += "\nEvidence collected so far:\n"
        for ev in previous_evidence:
            prompt += f"- {ev}\n"
    
    prompt += "\nINSTRUCTIONS:\n"
    prompt += "1. Review the evidence above.\n"
    
    if is_last_attempt:
        prompt += "2. THIS IS YOUR LAST ATTEMPT. DO NOT CALL TOOLS. You MUST synthesize the best possible answer from the evidence provided.\n"
        prompt += "3. If evidence is missing, state what is known and what is missing, but DO NOT call tools.\n"
        prompt += "4. Write your final answer inside the DRAFT_ANSWER block.\n"
    else:
        prompt += "2. If the evidence is sufficient to FULLY answer the question, SYNTHESIZE the final answer inside the DRAFT_ANSWER block.\n"
        prompt += "3. If you need more info, call tools. DO NOT generate a DRAFT_ANSWER if you are calling tools.\n"
        prompt += "4. If you are just stating what you will do, DO NOT put it in DRAFT_ANSWER. Just call the tools.\n"
    
    # Create planner agent
    planner_agent = create_planner_agent(
        model=DEFAULT_MODEL,
        top_k=5,
        tools=[],
    )
    
    # Define tools - now including hybrid search
    tools_list = [
        list_documents_http,
        search_document_http,
        search_documents_http,
        search_document_hybrid_http,
        search_all_hybrid_http,
        get_document_http,
    ]
    
    response = planner_agent.generate_content(prompt, tools=tools_list)
    
    # Extract text and tool calls
    raw_text = response.text or ""
    tool_calls = []
    
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                # If it's the last attempt, ignore tool calls!
                if is_last_attempt:
                    print("Ignoring tool call on last attempt")
                    continue
                
                fc = part.function_call
                tool_calls.append({
                    "name": fc.name,
                    "arguments": dict(fc.args)
                })
    
    return PlannerResult(
        raw_text=raw_text,
        draft_answer="",
        tool_calls=tool_calls,
        evidence=[]
    )


def adapt_judge(planner_result, **kwargs):
    """Adapter for judge agent."""
    prompt = f"Draft Answer: {planner_result.draft_answer}\n"
    prompt += "Evidence:\n"
    for ev in planner_result.evidence:
        prompt += f"- {ev}\n"
    
    judge_agent = create_judge_agent(model=DEFAULT_MODEL)
    response = judge_agent.generate_content(prompt)
    text = response.text or "{}"
    
    try:
        # Clean markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(text)
        return JudgeResult(
            verdict=data.get("verdict", "retry"),
            explanation=data.get("critique", "") + "\n" + data.get("missing", ""),
            requires_more_evidence=data.get("verdict") == "retry"
        )
    except Exception as e:
        return JudgeResult(
            verdict="retry",
            explanation=f"Failed to parse judge output: {text}",
            requires_more_evidence=False
        )


def adapt_synthesizer(user_query: str, draft_answer: str, evidence: List[Dict[str, Any]], runs: List[Any], **kwargs) -> SynthesizerResult:
    """Adapter for synthesizer agent."""
    prompt = f"USER_QUESTION: {user_query}\n"
    prompt += f"LATEST_DRAFT_ANSWER: {draft_answer}\n"
    
    prompt += "\nCONTEXT_SNIPPETS:\n"
    
    # Limit to top 5 chunks
    evidence = evidence[:5]
    print(f"Synthesizer using {len(evidence)} context chunks")
    
    for ev in evidence:
        # Create a safe copy for the prompt
        safe_ev = ev.copy()
        if "snippet" in safe_ev and isinstance(safe_ev["snippet"], str):
            # Truncate snippet to avoid token limits (approx 20k chars ~ 5k tokens)
            if len(safe_ev["snippet"]) > 20000:
                safe_ev["snippet"] = safe_ev["snippet"][:20000] + "... [TRUNCATED]"
        
        prompt += f"- {safe_ev}\n"
    
    synthesizer_agent = create_synthesizer_agent(model=DEFAULT_MODEL)
    response = synthesizer_agent.generate_content(prompt)
    
    # Extract draft answer from block
    raw_text = response.text or ""
    final_answer = raw_text
    
    marker_start = "=== DRAFT_ANSWER ==="
    marker_end = "=== END_DRAFT_ANSWER ==="
    
    if marker_start in raw_text and marker_end in raw_text:
        start_idx = raw_text.index(marker_start) + len(marker_start)
        end_idx = raw_text.index(marker_end, start_idx)
        final_answer = raw_text[start_idx:end_idx].strip()
    
    return SynthesizerResult(
        raw_text=raw_text,
        draft_answer=final_answer,
        evidence=evidence # Pass the filtered evidence
    )


def create_tool_executor(event_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """Create a tool executor that emits events to the queue."""
    
    def tool_executor(tool_calls):
        evidence = []
        
        for call in tool_calls:
            name = call.get("name")
            args = call.get("arguments", {})
            
            # Emit tool call event
            try:
                event_data = {
                    "type": "tool_call",
                    "tool": name,
                    "args": args
                }
                loop.call_soon_threadsafe(event_queue.put_nowait, event_data)
            except:
                pass
            
            result = None
            
            if name == "search_documents_http" or name == "search_all_documents_http":
                q = args.get("query") or args.get("question")
                res = search_documents_http(query=q, top_k=5)
                new_evidence = [{"doc_id": d.doc_id, "snippet": d.snippet} for d in res]
                evidence.extend(new_evidence)
                result = {"count": len(new_evidence), "evidence": new_evidence}
            
            elif name == "search_document_http":
                doc_id = args.get("doc_id")
                q = args.get("query")
                res = search_document_http(doc_id, q, top_k=5)
                new_evidence = [{"doc_id": d.doc_id, "snippet": d.snippet} for d in res]
                evidence.extend(new_evidence)
                result = {"count": len(new_evidence), "evidence": new_evidence}
            
            elif name == "search_document_hybrid_http":
                doc_id = args.get("doc_id")
                q = args.get("query")
                res = search_document_hybrid_http(doc_id, q, top_k=5)
                new_evidence = [{"doc_id": d.doc_id, "snippet": d.snippet, "search_type": d.metadata.get("search_type", "hybrid")} for d in res]
                evidence.extend(new_evidence)
                result = {"count": len(new_evidence), "evidence": new_evidence, "search_type": "hybrid"}
            
            elif name == "search_all_hybrid_http":
                q = args.get("query") or args.get("question")
                res = search_all_hybrid_http(query=q, top_k=5)
                new_evidence = [{"doc_id": d.doc_id, "snippet": d.snippet, "search_type": d.metadata.get("search_type", "hybrid")} for d in res]
                evidence.extend(new_evidence)
                result = {"count": len(new_evidence), "evidence": new_evidence, "search_type": "hybrid"}
            
            elif name == "get_document_http":
                doc_id = args.get("doc_id")
                d = get_document_http(doc_id)
                if d:
                    evidence.append({"doc_id": d.doc_id, "snippet": d.snippet})
                    result = {"doc_id": d.doc_id}
            
            elif name == "list_documents_http":
                docs = list_documents_http()
                new_evidence = {"documents": [{"id": d['id'], "name": d['name']} for d in docs]}
                evidence.append(new_evidence)
                result = {"count": len(docs)}
            
            # Emit tool result event
            try:
                event_data = {
                    "type": "tool_result",
                    "tool": name,
                    "result": result
                }
                loop.call_soon_threadsafe(event_queue.put_nowait, event_data)
            except:
                pass
        
        return evidence
    
    return tool_executor


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/create-store")
async def create_store(request: CreateStoreRequest):
    """
    Initialize file search store.
    Creates actual File Search store if semantic search is enabled.
    """
    try:
        # Check if semantic search is enabled in document service
        doc_service_response = requests.get(f"{DOC_SERVICE_URL}/health", timeout=5)
        
        if not doc_service_response.ok:
            return {
                "success": False,
                "message": "Document service not available",
                "store_name": request.display_name
            }
        
        # Try to create File Search store if semantic search is available
        try:
            store_response = requests.post(
                f"{DOC_SERVICE_URL}/api/file_search/create_store",
                json={"display_name": request.display_name},
                timeout=10
            )
            
            if store_response.ok:
                data = store_response.json()
                print(f"File Search store created: {data.get('store_name')}")
                return {
                    "success": True,
                    "store_name": data.get("store_name", request.display_name),
                    "message": "File Search store ready"
                }
            else:
                # Semantic search not available, but that's okay
                print("Semantic search not available, using BM25 only")
                return {
                    "success": True,
                    "store_name": request.display_name,
                    "message": "Store ready (BM25 mode)"
                }
        except Exception as e:
            print(f"Could not create File Search store: {e}")
            # Graceful fallback
            return {
                "success": True,
                "store_name": request.display_name,
                "message": "Store ready (BM25 mode)"
            }
    
    except Exception as e:
        print(f"Create store error: {e}")
        return {
            "success": True,
            "store_name": request.display_name,
            "message": "Store ready"
        }


@app.get("/api/list-files")
async def list_files():
    """List all uploaded files with metadata."""
    try:
        response = requests.get(f"{DOC_SERVICE_URL}/api/documents/list", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Transform to frontend format
        files = []
        for doc in data.get("documents", []):
            files.append({
                "id": doc["id"],
                "name": doc["name"],
                "summary": doc.get("description", ""),
                "topics": [],  # Could extract from content if needed
            })
        
        return {
            "success": True,
            "files": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/api/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload and index a document file (TXT, MD, PDF)."""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.txt', '.md', '.pdf')):
            raise HTTPException(
                status_code=400,
                detail="Only .txt, .md, and .pdf files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        if file.filename.lower().endswith('.pdf'):
            # Extract text from PDF
            try:
                pdf_file = io.BytesIO(content)
                reader = PdfReader(pdf_file)
                text = ""
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                print(f"Extracted {len(text)} characters from PDF: {file.filename}")
                
                if not text.strip():
                    raise HTTPException(
                        status_code=400, 
                        detail="Could not extract text from PDF. The file might be scanned images or empty."
                    )
            except HTTPException:
                raise
            except Exception as e:
                print(f"PDF Error: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")
        else:
            # Handle text files
            text = content.decode('utf-8')
        
        # Generate doc_id from filename
        doc_id = file.filename.replace(".", "_")
        
        # Generate summary using Gemini 2.0 Flash
        description = f"Uploaded file: {file.filename}"
        try:
            print(f"Generating summary for {file.filename}...")
            client = genai.Client(api_key=config.google_api_key)
            
            # Truncate text if too long for context window (though 2.0 Flash has 1M context)
            # Just to be safe and efficient, we can limit to first 100k chars for summary
            summary_context = text[:100000]
            
            prompt = (
                f"You are a helpful assistant. Please provide a concise 1-2 sentence summary "
                f"of the following document content. This summary will be used for retrieval context.\n\n"
                f"Document Name: {file.filename}\n"
                f"Content:\n{summary_context}"
            )
            
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=200
                )
            )
            
            if response.text:
                description = response.text.strip()
                print(f"Generated summary: {description}")
        except Exception as e:
            print(f"Failed to generate summary: {e}")
            # Fallback to default description
        
        # Chunking Logic
        CHUNK_SIZE = 50000
        
        if len(text) > CHUNK_SIZE:
            print(f"File {file.filename} is large ({len(text)} chars). Splitting into chunks...")
            
            # Split text into chunks
            chunks = [text[i:i+CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
            total_chunks = len(chunks)
            
            uploaded_docs = []
            
            for i, chunk_content in enumerate(chunks):
                part_num = i + 1
                part_doc_id = f"{doc_id}_part_{part_num}"
                part_name = f"{file.filename} (Part {part_num}/{total_chunks})"
                part_description = f"{description} [Part {part_num} of {total_chunks}]"
                
                payload = {
                    "doc_id": part_doc_id,
                    "name": part_name,
                    "content": chunk_content,
                    "description": part_description,
                    "enable_semantic_search": True
                }
                
                print(f"Uploading part {part_num}/{total_chunks}...")
                
                response = requests.post(
                    f"{DOC_SERVICE_URL}/api/documents/add",
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                uploaded_docs.append(part_doc_id)
            
            # Extract metadata (simple version)
            metadata = {
                "summary": description,
                "topics": [],
                "parts": total_chunks,
                "doc_ids": uploaded_docs
            }
            
            print(f"Upload complete for {file.filename}. Split into {total_chunks} parts.")
            
            return {
                "success": True,
                "doc_id": doc_id, # Return base ID
                "metadata": metadata
            }
            
        else:
            # Standard single file upload
            # Add to document service
            payload = {
                "doc_id": doc_id,
                "name": file.filename,
                "content": text,
                "description": description
            }
            
            # Enable semantic search for uploaded files
            # This allows hybrid search to work with full semantic capabilities
            payload["enable_semantic_search"] = True
            
            print(f"Uploading {file.filename} to document service with semantic search enabled...")
            
            response = requests.post(
                f"{DOC_SERVICE_URL}/api/documents/add",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Extract metadata (simple version)
            metadata = {
                "summary": description,
                "topics": []  # Could use LLM to extract topics
            }
            
            print(f"Upload complete for {file.filename}. Semantic search indexing initiated.")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "metadata": metadata
            }
        

    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
async def ask_question(request: AskQuestionRequest):
    """
    Answer a question using the orchestrator with streaming response.
    
    Streams JSON objects line-by-line:
    - {"type": "tool_call", "tool": "...", "args": {...}}
    - {"type": "tool_result", "tool": "...", "result": {...}}
    - {"type": "chunk", "text": "..."}
    - {"type": "complete", "citations": [...], "retrieval_info": {...}}
    - {"type": "error", "error": "..."}
    """
    
    async def generate_stream():
        try:
            # Create event queue for streaming
            event_queue = asyncio.Queue()
            
            # Run orchestrator in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Create tool executor with event emission
            tool_executor = create_tool_executor(event_queue, loop)
            
            # Start orchestration in background
            async def run_orchestration():
                try:
                    # Callback to stream judge results
                    def on_judge_result(judge_result: JudgeResult):
                        try:
                            event_data = {
                                "type": "judge_result",
                                "verdict": judge_result.verdict,
                                "explanation": judge_result.explanation,
                                "requires_more_evidence": judge_result.requires_more_evidence
                            }
                            loop.call_soon_threadsafe(event_queue.put_nowait, event_data)
                        except Exception as e:
                            print(f"Error in on_judge_result: {e}")

                    import functools
                    
                    # Create a partial function with keyword arguments
                    orchestrate_partial = functools.partial(
                        orchestrate_planner_judge,
                        planner=adapt_planner,
                        judge=adapt_judge,
                        tool_executor=tool_executor,
                        user_query=request.question,
                        max_attempts=5,
                        logger=None,
                        synthesizer=adapt_synthesizer,
                        on_judge_result=on_judge_result
                    )
                    
                    result = await loop.run_in_executor(
                        None,
                        orchestrate_partial
                    )
                    
                    # Signal completion
                    await event_queue.put({
                        "type": "_complete",
                        "result": result
                    })
                except Exception as e:
                    await event_queue.put({
                        "type": "error",
                        "error": str(e)
                    })
            
            # Start orchestration task
            orchestration_task = asyncio.create_task(run_orchestration())
            
            # Stream events as they arrive
            while True:
                try:
                    # Wait for event with timeout
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    
                    if event["type"] == "_complete":
                        # Final result - stream the answer in chunks
                        result = event["result"]
                        answer = result.final_answer
                        
                        # Stream answer in chunks
                        chunk_size = 50
                        for i in range(0, len(answer), chunk_size):
                            chunk = answer[i:i + chunk_size]
                            yield json.dumps({"type": "chunk", "text": chunk}) + "\n"
                            await asyncio.sleep(0.05)  # Simulate streaming delay
                        
                        # Send completion event with metadata
                        citations = []
                        
                        # Use evidence from synthesizer if available (this is the exact context used)
                        if hasattr(result, "synthesizer_result") and result.synthesizer_result and result.synthesizer_result.evidence:
                            for ev in result.synthesizer_result.evidence:
                                if isinstance(ev, dict) and "doc_id" in ev:
                                    citations.append({
                                        "title": ev.get("doc_id", "Unknown"),
                                        "chunks_used": 1,
                                        "snippet": ev.get("snippet", "") # Include snippet for UI
                                    })
                        else:
                            # Fallback to planner evidence
                            for run in result.runs:
                                for ev in run.planner_result.evidence:
                                    if isinstance(ev, dict) and "doc_id" in ev:
                                        citations.append({
                                            "title": ev.get("doc_id", "Unknown"),
                                            "chunks_used": 1,
                                            "snippet": ev.get("snippet", "")
                                        })
                        
                        yield json.dumps({
                            "type": "complete",
                            "citations": citations,
                            "retrieval_info": {
                                "total_chunks_used": len(citations),
                                "question_analysis": {
                                    "intent": "Document search and synthesis"
                                }
                            }
                        }) + "\n"
                        break
                    
                    elif event["type"] == "error":
                        yield json.dumps(event) + "\n"
                        break
                    
                    else:
                        # Stream tool events
                        yield json.dumps(event) + "\n"
                
                except asyncio.TimeoutError:
                    # Check if orchestration is still running
                    if orchestration_task.done():
                        break
                    continue
            
            # Ensure task is complete
            await orchestration_task
        
        except Exception as e:
            yield json.dumps({"type": "error", "error": str(e)}) + "\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson"
    )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_SERVER_PORT", 5001))
    
    print(f"🚀 Starting GeminiRAG API Server on port {port}")
    print(f"📚 Document Service: {DOC_SERVICE_URL}")
    print(f"🤖 Default Model: {DEFAULT_MODEL}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
