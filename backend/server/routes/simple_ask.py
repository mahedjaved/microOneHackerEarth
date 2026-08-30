import time
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from ..modules.llm import get_llm_chain
from ..modules.load_vectorstore import embedding_model, PINECONE_INDEX_NAME
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pinecone import Pinecone
from ..config import settings

router = APIRouter()


class SimpleRetriever(BaseRetriever):
    def __init__(self, documents):
        super().__init__()
        self._docs = documents

    def _get_relevant_documents(self, query):
        return self._docs


@router.post("/simple_ask/")
async def simple_ask(request: Request, question: str = Form(...)):
    """Simple RAG without UQ - baseline for comparison"""
    try:
        validated_question = question.strip()
        if not validated_question:
            raise HTTPException(status_code=422, detail="Question cannot be empty")

        # Retrieve from Pinecone
        if embedding_model is None:
            raise HTTPException(status_code=503, detail="Embedding model not available")
        
        pc = Pinecone(api_key=settings.pinecone_api_key)
        index = pc.Index(PINECONE_INDEX_NAME)
        embedding_query = embedding_model.embed_query(validated_question)
        response = index.query(
            vector=embedding_query,
            top_k=3,
            include_metadata=True,
        )

        docs = [
            Document(
                page_content=match["metadata"].get("text", ""),
                metadata=match["metadata"],
            )
            for match in response["matches"]
        ]

        # Simple RAG chain without UQ
        retriever = SimpleRetriever(docs)
        llm_chain = get_llm_chain(retriever)
        result = llm_chain.invoke({"query": validated_question})

        sources = [
            doc.metadata.get("source", "Unknown")
            for doc in docs
        ]

        return {
            "response": result.get("result", ""),
            "sources": sources,
            "system": "simple_rag",
            "confidence": None,
            "doubt_certificate": None,
            "safety_check": "skipped",
            "emergency": False,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Simple RAG failed: {str(e)}")
