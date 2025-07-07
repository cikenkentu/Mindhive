from fastapi import FastAPI
from app.products import router as products_router
from app.outlets import router as outlets_router

app = FastAPI(
    title="ZUS Coffee API",
    description="API for ZUS Coffee product search and outlet information",
    version="1.0.0"
)

app.include_router(products_router)
app.include_router(outlets_router)

@app.get("/")
def root():
    return {
        "message": "ZUS Coffee API",
        "endpoints": {
            "products": "GET /products?query=<search_term>",
            "outlets": "GET /outlets?query=<natural_language_query>",
            "docs": "GET /docs - API documentation"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "zus-coffee-api"}

# Production server setup
if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 