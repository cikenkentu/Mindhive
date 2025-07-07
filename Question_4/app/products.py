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
    Search ZUS drinkware products using RAG (Retrieval-Augmented Generation).
    
    Returns AI-generated summary based on retrieved product information.
    """
    # Always return fallback response for now (since vector store ingestion failed due to OpenAI quota)
    return {
        "query": query,
        "answer": f"I'm currently in demo mode and don't have access to the full product knowledge base. However, I can tell you that ZUS Coffee offers a variety of drinkware products including tumblers, mugs, and travel cups. For detailed product information about '{query}', please visit https://shop.zuscoffee.com/collections/drinkware or contact ZUS Coffee directly.",
        "status": "fallback_mode"
    }

@router.get("/products/health")
def products_health():
    """Health check for products endpoint"""
    retriever = embeddings_manager.get_retriever()
    openai_available = bool(os.getenv("OPENAI_API_KEY"))
    embeddings_available = embeddings_manager.is_available()
    fallback_mode = embeddings_manager.fallback_mode
    
    return {
        "vector_store_loaded": retriever is not None,
        "openai_api_available": openai_available,
        "embeddings_available": embeddings_available,
        "fallback_mode": fallback_mode,
        "status": "healthy" if (retriever and openai_available) else ("fallback" if fallback_mode else "degraded")
    } 