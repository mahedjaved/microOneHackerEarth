import time
from fastapi import APIRouter, Form, HTTPException
from langchain_groq import ChatGroq
from ..config import settings

router = APIRouter()


@router.post("/sota_ask/")
async def sota_ask(question: str = Form(...)):
    """SOTA baseline - direct LLM without retrieval for comparison"""
    try:
        validated_question = question.strip()
        if not validated_question:
            raise HTTPException(status_code=422, detail="Question cannot be empty")

        # Direct LLM without any retrieval
        llm = ChatGroq(
            model="groq/compound-mini",
            api_key=settings.groq_api_key_resolved,
        )

        # System prompt for direct answer (no RAG)
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Answer questions based on your general knowledge. If you don't know, say so.",
            },
            {"role": "user", "content": validated_question},
        ]

        response = llm.invoke(messages)

        return {
            "response": response.content,
            "sources": [],
            "system": "sota_direct_llm",
            "confidence": None,
            "doubt_certificate": None,
            "safety_check": "none",
            "emergency": False,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SOTA baseline failed: {str(e)}")
