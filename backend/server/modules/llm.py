from server.config import settings
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_openai import ChatOpenAI


def get_llm_chain(retriever):
    llm = _get_llm_with_fallback()
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
    return chain


def _get_llm_with_fallback():
    """Get LLM instance with Kilo as primary, others commented out."""
    # Primary: Kilo
    if settings.kilo_api_key:
        try:
            llm = ChatOpenAI(
                model=settings.kilo_model,
                api_key=settings.kilo_api_key,
                base_url=settings.kilo_base_url,
                temperature=0.1,
            )
            llm.invoke("test")
            return llm
        except Exception as e:
            print(f"Kilo unavailable ({e})")

    # Fallback: Groq
    # if settings.groq_api_key_resolved:
    #     try:
    #         llm = ChatGroq(
    #             model="openai/gpt-oss-120b",
    #             api_key=settings.groq_api_key_resolved,
    #         )
    #         llm.invoke("test")
    #         return llm
    #     except Exception as e:
    #         print(f"Groq unavailable ({e})")

    # Fallback: OpenCodeZen
    # if settings.opencodezen_api_key:
    #     try:
    #         llm = ChatOpenAI(
    #             model=settings.opencodezen_model,
    #             api_key=settings.opencodezen_api_key,
    #             base_url=settings.opencodezen_base_url,
    #             temperature=0.1,
    #         )
    #         llm.invoke("test")
    #         return llm
    #     except Exception as e:
    #         print(f"OpenCodeZen unavailable ({e})")

    raise RuntimeError("No LLM provider available. Configure KILO_API_KEY.")


def get_direct_llm():
    """Get a direct LLM instance for non-RAG use."""
    return _get_llm_with_fallback()

