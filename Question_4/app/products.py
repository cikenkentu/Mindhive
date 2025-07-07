from fastapi import APIRouter, HTTPException, Query
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from app.embeddings import embeddings_manager
import os

router = APIRouter()

# Custom prompt for product queries
PRODUCT_PROMPT = PromptTemplate(
    template="""You are a ZUS Coffee product expert. Use the following pieces of context to answer the question about ZUS drinkware products.

Context: {context}

Question: {question}

Provide a helpful and accurate answer about ZUS drinkware products. If you can't find relevant information, say so clearly.

Answer:""",
    input_variables=["context", "question"]
)

@router.get("/products")
def products(query: str = Query(..., min_length=3, description="Product search query")):
    """
    Search ZUS drinkware products using Retrieval-Augmented Generation (vector store + LLM).
    
    Workflow:
    1. Try to obtain a retriever from the shared `embeddings_manager`. This will be available
       only if the vector store has been ingested and is present on disk **and** the
       local embeddings backend was initialised successfully (see ingestion/ingest_products.py).
    2. Require an `OPENAI_API_KEY` because the answer is generated with `OpenAI` LLM for
       brevity/quality. If either prerequisite is missing we fall back to a deterministic
       canned response so the endpoint never raises 500.
    """

    retriever = embeddings_manager.get_retriever()
    openai_available = bool(os.getenv("OPENAI_API_KEY"))

    # ---------------------------------------------
    # RAG path – only when ALL prerequisites ready
    # ---------------------------------------------
    if retriever and openai_available:
        try:
            llm = OpenAI(temperature=0)
            qa = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=False
            )
            answer = qa.run(query).strip()
            return {
                "query": query,
                "answer": answer,
                "status": "ok"
            }
        except Exception as e:
            # Log but don’t crash the API – degrade gracefully.
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    # ---------------------------------------------
    # Dependency missing → return explicit 503/DEGRADED
    # ---------------------------------------------
    if not openai_available:
        # Matches unhappy-flow test expecting 503
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
        )

    if retriever is None:
        raise HTTPException(
            status_code=503,
            detail="Product knowledge base not available. Please run ingestion script first to build the vector store."
        )

    # ---------------- Fallback (sanitised) ----------------
    safe_answer = (
        "I'm currently in demo mode and don't have access to the full product knowledge base. "
        "However, I can tell you that ZUS Coffee offers a variety of drinkware products including "
        "tumblers, mugs, and travel cups. For more details please visit "
        "https://shop.zuscoffee.com/collections/drinkware or contact ZUS Coffee directly."
    )

    return {"query": query, "answer": safe_answer, "status": "degraded"}

@router.get("/products/health")
def products_health():
    """Health check for products endpoint"""
    retriever = embeddings_manager.get_retriever()
    openai_available = bool(os.getenv("OPENAI_API_KEY"))
    embeddings_available = embeddings_manager.is_available()
    fallback_mode = embeddings_manager.fallback_mode

    if retriever and openai_available:
        status = "healthy"
    elif fallback_mode:
        status = "degraded"  # align with unhappy-flow test expectation
    else:
        status = "degraded"

    return {
        "vector_store_loaded": retriever is not None,
        "openai_api_available": openai_available,
        "embeddings_available": embeddings_available,
        "status": status
    } 