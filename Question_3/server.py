from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
import re
import uvicorn
from typing import Union


class CalcRequest(BaseModel):
    expression: str
    
    @field_validator('expression')
    @classmethod
    def validate_expression(cls, v):
        if not v or not v.strip():
            raise ValueError('Expression cannot be empty')
        if len(v) > 100:
            raise ValueError('Expression too long')
        return v.strip()


class CalcResponse(BaseModel):
    result: float
    expression: str


app = FastAPI(title="Calculator API", description="Simple arithmetic calculator service")


def calc_api(expr: str) -> float:
    """
    Safely evaluates mathematical expressions.
    Supports basic arithmetic: +, -, *, /, (), decimals
    """
    # Clean the expression - extract only the math part
    math_pattern = r'(\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?(?:\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)*)|(\(\s*\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?\s*\)(?:\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)*)'
    matches = re.findall(math_pattern, expr)
    
    if matches:
        # Take the first complete match
        math_expr = matches[0][0] if matches[0][0] else matches[0][1]
        math_expr = math_expr.strip()
        # Reject if the original input contains extra characters beyond the math expr
        # (e.g. "1+1; import os")
        cleaned_original = expr.strip()
        if cleaned_original != math_expr:
            raise ValueError("Invalid characters in expression")
    else:
        # Try to extract a simple pattern
        simple_pattern = r'\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?'
        match = re.search(simple_pattern, expr)
        if match:
            math_expr = match.group(0)
        else:
            raise ValueError("No valid mathematical expression found")
    
    # Only allow basic math operations for security
    allowed_chars = set('0123456789+-*/.() ')
    if not all(c in allowed_chars for c in math_expr):
        raise ValueError("Invalid characters in expression")
    
    # Check for division by zero before evaluation
    if '/0' in math_expr.replace(' ', '') or '/ 0' in math_expr:
        raise ValueError("Division by zero is not allowed")
    
    try:
        # Use eval but restrict to safe operations
        allowed_names = {
            "__builtins__": {},
            "__name__": "restricted",
            "__package__": None,
        }
        result = eval(math_expr, allowed_names)
        
        # Ensure result is a number
        if not isinstance(result, (int, float)):
            raise ValueError("Result is not a number")
            
        return float(result)
    except ZeroDivisionError:
        raise ValueError("Division by zero is not allowed")
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


@app.post("/calculate", response_model=CalcResponse)
def calculate(req: CalcRequest):
    """
    Calculate arithmetic expressions.
    
    Supports:
    - Basic operations: +, -, *, /
    - Parentheses for grouping
    - Decimal numbers
    - Multiple operations in sequence
    
    Examples:
    - "2 + 3" → 5
    - "10 * (5 - 2)" → 30
    - "15.5 / 2" → 7.75
    """
    try:
        result = calc_api(req.expression)
        return CalcResponse(result=result, expression=req.expression)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "calculator-api"}


@app.get("/")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Calculator API",
        "endpoints": {
            "calculate": "POST /calculate - Calculate arithmetic expressions",
            "health": "GET /health - Health check",
            "docs": "GET /docs - API documentation"
        }
    }


if __name__ == "__main__":
    print("Starting Calculator API server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 