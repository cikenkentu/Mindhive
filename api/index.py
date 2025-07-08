from fastapi import FastAPI, HTTPException, Body, BackgroundTasks, APIRouter
from typing import Dict, Any
import pathlib
import sys
import os

# ---------------------------------------------------------------------------
# Adjust PYTHONPATH so that question modules can be imported as they were in
# individual folders (tests added each folder to sys.path). This keeps their
# internal absolute imports working without any refactor.
# ---------------------------------------------------------------------------
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
for sub in ("Question_1", "Question_2", "Question_3", "Question_4"):
    sys.path.append(str(BASE_DIR / sub))
# Question_4 uses absolute imports like `app.embeddings`, where `app` is the
# sub-directory inside Question_4. Make that directory importable as a top-level
# package by adding its parent to sys.path.
sys.path.append(str(BASE_DIR / "Question_4"))

# ---------------------------------------------------------------------------
# Import required components from each question package
# ---------------------------------------------------------------------------
try:
    # Q1 – sequential conversation bot
    from sequential_conversation import SequentialConversationBot  # type: ignore
except ImportError as e:
    raise ImportError(f"Failed to import SequentialConversationBot (Q1): {e}")

try:
    # Q2 – planner helpers (optional usage)
    from planner import plan_and_execute  # type: ignore
except ImportError:
    # Planner isn’t strictly required for basic demo – continue without it.
    plan_and_execute = None  # type: ignore

try:
    # Q3 – calculator core API
    from server import calc_api  # type: ignore
except ImportError as e:
    raise ImportError(f"Failed to import calc_api from Question_3.server: {e}")

try:
    # Q4 – existing FastAPI routers (products & outlets)
    from app.products import router as products_router  # type: ignore
    from app.outlets import router as outlets_router  # type: ignore
except ImportError as e:
    # Heavy ML deps (scikit-learn, transformers) not installed in lightweight
    # deployment. Provide a disabled stub so routes still exist.
    print(f"[WARN] Products router unavailable ({e}). Using lightweight stub.")
    products_router = APIRouter()

    @products_router.get("/products", tags=["Products RAG"])
    def products_disabled():
        raise HTTPException(
            status_code=503,
            detail="Products endpoint disabled in lightweight deployment."
        )

    @products_router.get("/products/health")
    def products_health_disabled():
        return {
            "vector_store_loaded": False,
            "openai_api_available": False,
            "status": "disabled"
        }

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Mindhive Demo – Questions 1-4",
    description="Unified API exposing sequential chatbot, calculator, RAG products, and outlets Text2SQL.",
    version="1.0.0",
)

# Include Q4 routers without additional prefixes (their paths already begin with
# /products and /outlets respectively).
app.include_router(products_router, tags=["Products RAG"])
app.include_router(outlets_router, tags=["Outlets Text2SQL"])

# ---------------------------------------------------------------------------
# Q3 – Calculator endpoint wrapper
# ---------------------------------------------------------------------------
@app.get("/calculate", tags=["Calculator"])
def calculate(expr: str):
    """Evaluate arithmetic expression via Q3 calc_api."""
    try:
        result = calc_api(expr)
        return {"expression": expr, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------------------------------------------------------------------------
# Q1 (+ optional Q2) – Chatbot endpoint
# ---------------------------------------------------------------------------
_chat_bot = SequentialConversationBot()

@app.post("/chat", tags=["Chatbot"])
def chat(message: str = Body(..., embed=True)) -> Dict[str, str]:
    """Sequential conversation bot (Question 1)."""
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Basic behaviour – use Q1 bot; advanced reasoning via Q2 planner if wanted.
    if plan_and_execute:
        # Attempt to use planner; fall back if planner raises.
        try:
            planned = plan_and_execute(message)
            # planner returns {response: str, ...}
            return {"reply": planned.get("response", planned.get("reply", ""))}
        except Exception:
            pass  # Ignore planner errors and fall back to Q1 bot.

    reply = _chat_bot.process_input(message)
    return {"reply": reply}

# ---------------------------------------------------------------------------
# Root endpoint – helpful landing page
# ---------------------------------------------------------------------------
@app.get("/")
def root() -> Dict[str, Any]:
    """Landing endpoint listing main routes so '/' isn’t 404."""
    return {
        "message": "Mindhive API – Questions 1-4",
        "endpoints": {
            "chat": "POST /chat {message:string}",
            "calculate": "GET /calculate?expr=2+2",
            "products": "GET /products?query=...",
            "products_health": "GET /products/health",
            "outlets": "GET /outlets?query=...",
            "outlets_list": "GET /outlets/list",
            "outlets_health": "GET /outlets/health",
            "docs": "GET /docs",
            "health": "GET /health"
        }
    }

# ---------------------------------------------------------------------------
# Simple health check for monitoring
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy"}

# ---------------------------------------------------------------------------
# Startup initialisation: ensure outlets DB exists and populated
# ---------------------------------------------------------------------------

try:
    from app.db import create_tables, SessionLocal  # type: ignore
    from ingestion.ingest_outlets import populate_outlets_db  # type: ignore
except Exception:
    populate_outlets_db = None  # type: ignore


@app.on_event("startup")
async def init_resources():
    """Initialise SQLite outlets DB if needed."""
    if populate_outlets_db is None:
        print("[INIT] Could not import outlet ingestion tools – skipping DB init.")
        return

    try:
        # Always ensure tables exist
        create_tables()

        # Check if outlets table has rows; if empty, populate
        session = SessionLocal()
        count = 0
        try:
            count = session.execute("SELECT COUNT(*) FROM outlets").scalar()
        except Exception:
            # Table might not exist yet, it will after create_tables()
            pass
        finally:
            session.close()

        if count == 0:
            print(f"[INIT] Populating outlets DB with sample data ...")
            populate_outlets_db()
        else:
            print(f"[INIT] Outlets DB already has {count} rows – skipping population.")
    except Exception as e:
        print(f"[INIT] Error while initialising outlets DB: {e}") 