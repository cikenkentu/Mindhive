from fastapi import FastAPI
from app.products import router as products_router
from app.outlets import router as outlets_router
import os
import subprocess
import sys

app = FastAPI(
    title="ZUS Coffee API",
    description="API for ZUS Coffee product search and outlet information",
    version="1.0.0"
)

app.include_router(products_router)
app.include_router(outlets_router)

@app.on_event("startup")
async def startup_event():
    """Initialize database and vector store on app startup"""
    try:
        print("🚀 Initializing ZUS Coffee API...")
        
        # Check if already initialized
        if not (os.path.exists("zus_outlets.db") and os.path.exists("faiss_drinkware_index")):
            print("Running startup initialization...")
            # Run startup script
            result = subprocess.run([sys.executable, "startup.py"], 
                                  capture_output=True, text=True, cwd=os.getcwd())
            if result.returncode == 0:
                print("✅ Startup initialization completed successfully")
            else:
                print(f"⚠️ Startup initialization warning: {result.stderr}")
        else:
            print("✅ Already initialized - skipping startup")
            
    except Exception as e:
        print(f"⚠️ Startup initialization error: {e}")
        print("🔄 API will continue with fallback mode")

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