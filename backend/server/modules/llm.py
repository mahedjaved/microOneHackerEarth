from server.config import settings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_openai import ChatOpenAI


def get_llm_chain(retriever):
    # Try Groq first, fall back to OpenCodeZen if rate limited
    llm = _get_llm_with_fallback()
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
    return chain


def _get_llm_with_fallback():
    """Get LLM instance with fallback support."""
    # Try Groq first
    if settings.groq_api_key_resolved:
        try:
            llm = ChatGroq(
                model="openai/gpt-oss-120b",
                api_key=settings.groq_api_key_resolved,
            )
            # Test the connection
            llm.invoke("test")
            return llm
        except Exception as e:
            print(f"Groq unavailable ({e}), falling back to OpenCodeZen")

    # Fall back to OpenCodeZen
    if settings.opencodezen_api_key:
        return ChatOpenAI(
            model=settings.opencodezen_model,
            api_key=settings.opencodezen_api_key,
            base_url=settings.opencodezen_base_url,
            temperature=0.1,
        )

    # Default to Groq (will fail with rate limit if still exhausted)
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=settings.groq_api_key_resolved,
    )


def get_direct_llm():
    """Get a direct LLM instance for non-RAG use."""
    return _get_llm_with_fallback()

