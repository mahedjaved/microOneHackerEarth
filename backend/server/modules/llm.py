from server.config import settings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain_core.language_models.fake_chat_models import FakeListChatModel

print("DEBUG: llm.py loaded from:", __file__)


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
        try:
            llm = ChatOpenAI(
                model=settings.opencodezen_model,
                api_key=settings.opencodezen_api_key,
                base_url=settings.opencodezen_base_url,
                temperature=0.1,
            )
            # Test the connection
            llm.invoke("test")
            return llm
        except Exception as e:
            print(f"OpenCodeZen unavailable ({e}), using mock LLM")

    # If all providers fail, return a fake LLM for testing
    print("WARNING: No LLM provider available. Using mock LLM for testing.")
    return FakeListChatModel(responses=["This is a test response from the medical assistant. Based on the provided context, the answer is for testing purposes only."])


def get_direct_llm():
    """Get a direct LLM instance for non-RAG use."""
    return _get_llm_with_fallback()

