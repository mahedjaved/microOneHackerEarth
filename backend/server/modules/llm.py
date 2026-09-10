from server.config import settings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA


def get_llm_chain(retriever):
    """Get LLM chain with Groq as the sole provider."""
    llm = _get_groq_llm()
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
    return chain


def _get_groq_llm():
    """Get Groq LLM instance. No fallback chain."""
    if not settings.groq_api_key_resolved:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. "
            "Set a valid Groq API key in backend/.env or backend/server/.env."
        )
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=settings.groq_api_key_resolved,
    )


def get_direct_llm():
    """Get a direct LLM instance for non-RAG use."""
    return _get_groq_llm()

