"""
MedRAG-style baseline for comparison.
Replicates the approach from:
- Paper: "MedRAG: A Systematic Toolkit for Medical RAG" (ACL 2024)
- Paper: "MIRAGE: Medical Information RAG Evaluation"
- Code: https://github.com/gzxiong/MedRAG

Key differences from our UQ-RAG:
1. No safety gate
2. No claim verification
3. No conformal prediction
4. No doubt certificates
5. Standard retrieval + generation only
"""

from fastapi import APIRouter, Form, HTTPException
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from pinecone import Pinecone
from ..modules.load_vectorstore import embedding_model, PINECONE_INDEX_NAME
from ..modules.llm import get_direct_llm
from ..config import settings

router = APIRouter()


class MedRRetriever(BaseRetriever):
    """Standard retriever without UQ enhancements"""
    def __init__(self, documents):
        self._docs = documents

    def _get_relevant_documents(self, query):
        return self._docs


MEDRAG_SYSTEM_PROMPT = """You are a medical assistant. Answer the question based on the provided context.
If the context does not contain enough information, say so clearly.

Context:
{context}

Question: {question}

Answer:"""


@router.post("/medrag_baseline/")
async def medrag_baseline(question: str = Form(...)):
    """
    MedRAG-style baseline: Standard RAG without uncertainty quantification.
    This replicates the baseline approach from the MedRAG paper (ACL 2024).
    """
    try:
        validated_question = question.strip()
        if not validated_question:
            raise HTTPException(status_code=422, detail="Question cannot be empty")

        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(PINECONE_INDEX_NAME)
        embedding_query = embedding_model.embed_query(validated_question)
        pinecone_response = index.query(
            vector=embedding_query,
            top_k=3,  # Reduced from 5 to save tokens
            include_metadata=True,
        )

        docs = [
            Document(
                page_content=match["metadata"].get("text", "")[:500],  # Truncate passages to save tokens
                metadata=match["metadata"],
            )
            for match in pinecone_response["matches"]
        ]

        context = "\n\n".join([doc.page_content for doc in docs])

        llm = get_direct_llm()

        prompt = ChatPromptTemplate.from_template(MEDRAG_SYSTEM_PROMPT)
        messages = prompt.format_messages(
            context=context,
            question=validated_question
        )

        response = llm.invoke(messages)

        return {
            "response": response.content,
            "sources": [doc.metadata.get("source", "Unknown") for doc in docs],
            "system": "medrag_baseline",
            "confidence": None,
            "doubt_certificate": None,
            "safety_check": "none",
            "safety_scope": "no_check",  # MedRAG has no safety gate
            "emergency": False,
            "retrieval_scores": [match["score"] for match in pinecone_response.get("matches", [])],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MedRAG baseline failed: {str(e)}")
