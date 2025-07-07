from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from langchain_experimental.sql import SQLDatabaseChain
from langchain_community.utilities import SQLDatabase
from langchain_community.llms import OpenAI
from app.db import get_db, engine
from app.models import Outlet
import os

router = APIRouter()

# Initialize SQL database for LangChain
sql_db = SQLDatabase(engine)

def _fallback_outlet_query(query: str, db: Session):
    """Fallback function for basic outlet queries when LLM is not available"""
    query_lower = query.lower()
    
    try:
        # Basic pattern matching for common queries
        if "kuala lumpur" in query_lower or "kl" in query_lower:
            outlets = db.query(Outlet).filter(Outlet.city.contains("Kuala Lumpur")).all()
        elif "petaling jaya" in query_lower or "pj" in query_lower:
            outlets = db.query(Outlet).filter(Outlet.city.contains("Petaling Jaya")).all()
        elif "putrajaya" in query_lower:
            outlets = db.query(Outlet).filter(Outlet.city.contains("Putrajaya")).all()
        elif "open" in query_lower and ("late" in query_lower or "night" in query_lower or "10" in query_lower or "11" in query_lower):
            # Look for outlets open late
            outlets = db.query(Outlet).filter(Outlet.hours.contains("11:00 PM")).all()
        elif "early" in query_lower or "morning" in query_lower or "8" in query_lower:
            # Look for outlets open early
            outlets = db.query(Outlet).filter(Outlet.hours.contains("8:00 AM")).all()
        else:
            # Default: return all outlets
            outlets = db.query(Outlet).all()
        
        if outlets:
            outlet_info = []
            for outlet in outlets:
                outlet_info.append(f"• {outlet.name} ({outlet.city}) - {outlet.hours}")
            
            result = f"Found {len(outlets)} outlet(s):\n" + "\n".join(outlet_info)
        else:
            result = "No outlets found matching your criteria."
            
        return {
            "query": query,
            "result": result,
            "status": "fallback_mode"
        }
        
    except Exception as e:
        return {
            "query": query,
            "result": f"Sorry, I'm currently in fallback mode and couldn't process your request. Error: {str(e)}",
            "status": "error"
        }

@router.get("/outlets")
def outlets(query: str = Query(..., min_length=3, description="Natural language query about outlets"), 
           db: Session = Depends(get_db)):
    """
    Query ZUS outlets using Text2SQL natural language processing.
    
    Translates natural language to SQL, executes it, and returns results.
    """
    try:
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            raise HTTPException(
                status_code=503,
                detail="OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
            )
        
        # Try to initialize LLM and SQL chain with fallback
        try:
            llm = OpenAI(temperature=0, openai_api_key=os.getenv("OPENAI_API_KEY"))
            sql_chain = SQLDatabaseChain.from_llm(
                llm=llm, 
                db=sql_db, 
                verbose=False,
                return_intermediate_steps=False
            )
            
            # Execute the query
            result = sql_chain.run(query)
        except Exception as llm_error:
            # Fallback to basic SQL queries for common requests
            return _fallback_outlet_query(query, db)
        
        return {
            "query": query,
            "result": result.strip()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Handle SQL errors gracefully
        error_msg = str(e).lower()
        if "sql" in error_msg or "syntax" in error_msg:
            raise HTTPException(
                status_code=400,
                detail="Sorry, I couldn't translate that request into SQL. Please ask about outlet locations, hours, or services."
            )
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/outlets/list")
def list_outlets(db: Session = Depends(get_db)):
    """List all outlets for reference"""
    outlets = db.query(Outlet).all()
    return {
        "outlets": [
            {
                "id": outlet.id,
                "name": outlet.name,
                "city": outlet.city,
                "address": outlet.address,
                "hours": outlet.hours,
                "services": outlet.services
            }
            for outlet in outlets
        ]
    }

@router.get("/outlets/health")
def outlets_health(db: Session = Depends(get_db)):
    """Health check for outlets endpoint"""
    try:
        outlet_count = db.query(Outlet).count()
        openai_available = bool(os.getenv("OPENAI_API_KEY"))
        
        return {
            "database_connected": True,
            "outlet_count": outlet_count,
            "openai_api_available": openai_available,
            "status": "healthy" if openai_available else "degraded"
        }
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "status": "unhealthy"
        } 