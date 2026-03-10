"""
AI routes — Workflow generation from natural language.

POST /ai/generate — Takes a natural language description, returns a generated workflow.
                    (Currently returns a rule-based mock; will be replaced with Gemini LLM in Phase 3)
GET  /ai/ping    — Health check
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.authorization import require_permission
from app.dependencies import get_db
import uuid
import json

router = APIRouter(prefix="/ai", tags=["AI"])


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000, description="Natural language workflow description")


class GeneratedWorkflow(BaseModel):
    name: str
    nodes: list
    edges: list
    explanation: str


@router.get("/ping")
def ping():
    return {"status": "ok", "message": "AI service ready"}


from app.ai.llm_client import llm_client
from app.ai.prompts import WORKFLOW_GENERATION_PROMPT
from app.ai.schemas import GeneratedWorkflowResult

@router.post("/generate", response_model=GeneratedWorkflowResult)
def generate_workflow(
    req: GenerateRequest,
    user: dict = Depends(require_permission("read:workflow")),
    db: Session = Depends(get_db)
):
    """
    Generate a workflow from a natural language description using Gemini 2.5.
    """
    if not llm_client.is_configured():
        raise HTTPException(
            status_code=503, 
            detail="AI generation is currently unavailable. Please configure GEMINI_API_KEY in the environment."
        )

    try:
        # We explicitly ask for the Pydantic model back
        result = llm_client.generate_structured(
            system_prompt=WORKFLOW_GENERATION_PROMPT,
            user_prompt=f"Create a workflow for the following request:\n{req.prompt}",
            response_model=GeneratedWorkflowResult,
            temperature=0.2, # low temp since we want standard node configurations
            db=db,
            user_id=user.get("user_id")
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation failed: {str(e)}")


@router.post("/stream")
async def stream_ai_chat(
    req: GenerateRequest,
    user: dict = Depends(require_permission("read:workflow")),
):
    """
    Stream an AI response token-by-token using Server-Sent Events (SSE).
    """
    system_prompt = "You are a helpful AI assistant for HealthOps Studio. Be concise and professional."
    
    # We get the async generator from the LLM client
    # If no API key is provided, this handles returning a mock generator!
    streamer = llm_client.generate_stream(
        system_prompt=system_prompt,
        user_prompt=req.prompt,
        temperature=0.7
    )
    
    async def event_generator():
        try:
            # We await the streamer since it returns an async generator
            async for chunk in await streamer:
                # SSE format requires "data: <content>\n\n"
                # Wrapping in JSON prevents internal newlines in the chunk from breaking the stream
                payload = json.dumps({"chunk": chunk})
                yield f"data: {payload}\n\n"
            
            # Send an explicit "[DONE]" message so the client knows when to close the connection
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
