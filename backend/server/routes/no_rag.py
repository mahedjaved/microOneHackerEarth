"""
No-RAG baseline: Direct LLM without retrieval.
Serves as the simplest baseline for comparison per FR-002.
"""

from fastapi import APIRouter, Form, HTTPException
from ..modules.llm import get_direct_llm

router = APIRouter()


NO_RAG_SYSTEM_PROMPT = """You are a helpful assistant. Answer questions based on your general knowledge.
If you don't know, say so."""


@router.post("/no_rag/")
async def no_rag(question: str = Form(...)):
    """
    No-RAG baseline: Direct LLM without any retrieval or grounding.
    Returns response with only 'response' and 'system' fields per FR-002.
    """
    try:
        validated_question = question.strip()
        if not validated_question:
            raise HTTPException(status_code=422, detail="Question cannot be empty")

        llm = get_direct_llm()

        messages = [
            {
                "role": "system",
                "content": NO_RAG_SYSTEM_PROMPT,
            },
            {"role": "user", "content": validated_question},
        ]

        response = llm.invoke(messages)

        return {
            "response": response.content,
            "system": "no_rag",
            "safety_scope": "no_check",  # NoRAG has no safety gate
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No-RAG baseline failed: {str(e)}")
