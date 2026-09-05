import time
import json
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Form, HTTPException, Request, Body

from ..schemas import QuestionRequest, QuestionResponse, ExtendedQuestionResponse

from ..modules.rate_limiter import limiter

from ..modules.llm import get_llm_chain
from ..modules.db_logger import log_query, estimate_tokens_and_cost

from ..modules.load_vectorstore import (
    load_vectorstore,
    embedding_model,
    PINECONE_INDEX_NAME,
)
from ..modules.langsmith_tracing import configure_langsmith_tracing, end_langsmith_run

from ..modules.metrics import (
    request_count,
    token_usage,
    chunk_count,
    errors,
    request_latency,
    query_latency,
    active_requests,
)

from ..modules.pii_detector import detect_and_redact

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from pinecone import Pinecone
from pydantic import Field
from typing import List, Optional

from ..logger import logger
from ..config import settings

router = APIRouter()


@router.post("/ask/", response_model=ExtendedQuestionResponse)
@limiter.limit("10/minute")
async def ask_question(request: Request, question: str = Form(...)):
    try:
        validated = QuestionRequest(question=question)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    if settings.prompt_injection_detection_enabled:
        from ..modules.prompt_injection_detector import validate_query
        validate_query(validated.question)

    # redact PII if enabled
    if settings.pii_detection_enabled:
        original_question = validated.question
        redacted_question = await detect_and_redact(validated.question)
        pii_redacted = original_question != redacted_question
        validated.question = redacted_question
    else:
        pii_redacted = False

    req_start_time = time.time()
    active_requests.labels(method="POST", endpoint="/ask/").inc()

    try:
        logger.info(f"Received question: {validated.question}")

        # RETRIEVAL: existing Pinecone pipeline
        pc = Pinecone(
            api_key=settings.pinecone_api_key,
        )
        index = pc.Index(PINECONE_INDEX_NAME)
        embedding_query = embedding_model.embed_query(validated.question)
        response = index.query(
            vector=embedding_query,
            top_k=2,  # Reduced from 3 to save tokens
            include_metadata=True,
        )
        docs = [
            Document(
                page_content=match["metadata"].get("text", "")[:500],  # Truncate passages to save tokens
                metadata=match["metadata"],
            )
            for match in response["matches"]
        ]

        # Simple retriever class
        class SimpleRetriever(BaseRetriever):
            tags: Optional[List[str]] = Field(
                default_factory=list, description="Optional tags for filtering"
            )
            metadata: Optional[dict] = Field(
                default_factory=dict, description="Optional metadata for filtering"
            )

            def __init__(self, documents: List[Document]):
                super().__init__()
                self._docs = documents

            def _get_relevant_documents(self, query: str) -> List[Document]:
                return self._docs

        retriever = SimpleRetriever(docs)

        # BUILD EVIDENCE PACKET from retrieval results
        from ..modules.corpus.loader import build_evidence_packet
        from ..schemas import Passage

        passages = [
            Passage(
                chunk_id=match["metadata"].get("chunk_id", match["id"]),
                document_id=match["metadata"].get("source", "unknown"),
                document_version=match["metadata"].get("version", "v1"),
                page_location=str(match["metadata"].get("page", "")),
                text=match["metadata"].get("text", "")[:500],  # Truncate to save tokens
                provenance_hash="",
            )
            for match in response["matches"]
        ]

        evidence_packet = build_evidence_packet(
            corpus_id="medical-corpus-v1",
            corpus_hash="",
            retrieval_query=validated.question,
            passages=passages,
            retriever_version="pinecone-v1",
            latency_ms=0,
        )

        # UQ PIPELINE: inserted after retrieval, before RAG chain (Q6)
        # First call RAG chain to generate answer, then pass to UQ pipeline for verification
        llm_chain = get_llm_chain(retriever)
        rag_result = llm_chain.invoke({"query": validated.question})
        llm_answer = rag_result.get("result", "")

        try:
            from ..modules.query_handlers import run_uq_pipeline
            uq_response, run_artifact = run_uq_pipeline(
                question=validated.question,
                evidence_packet=evidence_packet,
                llm_answer=llm_answer,
            )

            # Record run artifact to database
            await log_query(
                query=validated.question,
                answer=uq_response.response or "",
                sources=uq_response.sources,
                estimated_input_tokens=0,
                estimated_output_tokens=0,
                estimated_cost=0.0,
            )

            return ExtendedQuestionResponse(
                response=uq_response.response,
                sources=uq_response.sources,
                disclaimer=uq_response.disclaimer,
                injection_detected=False,
                pii_redacted=pii_redacted,
                doubt_certificate=uq_response.doubt_certificate,
                run_artifact_id=uq_response.run_artifact_id,
                safety_scope=uq_response.safety_scope,
            )

        except Exception as uq_error:
            logger.warning(f"UQ pipeline failed, falling back to baseline RAG: {uq_error}")
            # Fallback: return the RAG result directly since we already called the chain
            sources = [
                doc.metadata.get("source", "Unknown") for doc in docs
            ]

            return ExtendedQuestionResponse(
                response=llm_answer,
                sources=sources,
                disclaimer=settings.medical_disclaimer,
                injection_detected=False,
                pii_redacted=pii_redacted,
                doubt_certificate=None,
                run_artifact_id=None,
                safety_scope="allowed",  # Fallback assumes allowed
            )

    except Exception as e:
        logger.exception(f"Error processing question: {e}")
        errors.labels(method="POST", endpoint="/ask/", status_code=500).inc()
        return JSONResponse(
            content={"error": "Failed to process question"}, status_code=500
        )

    finally:
        active_requests.labels(method="POST", endpoint="/ask/").dec()


# ---------------------------------------------------------------------------
# Test-only endpoint for prompt-injection / safety research
# ---------------------------------------------------------------------------
# This endpoint accepts pre-supplied passages so researchers can feed
# identical poisoned passage sets to UQ-RAG and baselines without
# modifying the production retrieval pipeline.
#
# IMPORTANT: This is a TEST endpoint. It should be disabled in production
# or protected by an admin-only auth layer. For now, it is gated by the
# same settings flag used for other debug features.
# ---------------------------------------------------------------------------

from fastapi import Body

_test_prompt_injection_enabled = False  # Set to True only in test environments


@router.post("/ask_test/", response_model=ExtendedQuestionResponse)
async def ask_question_test(
    request: Request,
    question: str = Form(...),
    custom_passages: str = Form("[]"),  # JSON string of Passage-like dicts
):
    """Test-only endpoint that accepts custom passages instead of running retrieval.

    This enables prompt-injection safety testing by allowing researchers to
    feed poisoned passages to all three systems under identical conditions.

    Args:
        question: The user's question
        custom_passages: JSON string of passage dicts with keys:
            - chunk_id: str
            - document_id: str
            - document_version: str
            - page_location: str
            - text: str
            - provenance_hash: str
    """
    if not _test_prompt_injection_enabled:
        raise HTTPException(
            status_code=403,
            detail="Test endpoint is disabled. Set _test_prompt_injection_enabled = True in ask_question.py to enable.",
        )

    try:
        validated = QuestionRequest(question=question)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Parse custom passages
    try:
        passages_data = json.loads(custom_passages)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid custom_passages JSON: {e}")

    # Build passages and evidence packet from custom data
    from ..schemas import Passage
    from ..modules.corpus.loader import build_evidence_packet

    passages = []
    for p in passages_data:
        passages.append(
            Passage(
                chunk_id=p.get("chunk_id", "unknown"),
                document_id=p.get("document_id", "unknown"),
                document_version=p.get("document_version", "v1"),
                page_location=p.get("page_location", "page-1"),
                text=p.get("text", ""),
                provenance_hash=p.get("provenance_hash", ""),
            )
        )

    evidence_packet = build_evidence_packet(
        corpus_id="test-corpus",
        corpus_hash="test-hash",
        retrieval_query=validated.question,
        passages=passages,
        retriever_version="test-custom",
        latency_ms=0,
    )

    # Skip retrieval, use custom passages directly
    req_start_time = time.time()
    active_requests.labels(method="POST", endpoint="/ask_test/").inc()

    try:
        logger.info(f"[TEST] Received question with {len(passages)} custom passages: {validated.question}")

        # Run UQ pipeline with custom evidence
        from ..modules.query_handlers import run_uq_pipeline
        uq_response, run_artifact = run_uq_pipeline(
            question=validated.question,
            evidence_packet=evidence_packet,
            llm_answer="",  # Will be generated by the pipeline
        )

        return ExtendedQuestionResponse(
            response=uq_response.response,
            sources=uq_response.sources,
            disclaimer=uq_response.disclaimer,
            injection_detected=False,
            pii_redacted=False,
            doubt_certificate=uq_response.doubt_certificate,
            run_artifact_id=uq_response.run_artifact_id,
            safety_scope=uq_response.safety_scope,
        )

    except Exception as e:
        logger.exception(f"[TEST] Error processing question: {e}")
        errors.labels(method="POST", endpoint="/ask_test/", status_code=500).inc()
        return JSONResponse(
            content={"error": "Failed to process question", "detail": str(e)}, status_code=500
        )

    finally:
        active_requests.labels(method="POST", endpoint="/ask_test/").dec()
