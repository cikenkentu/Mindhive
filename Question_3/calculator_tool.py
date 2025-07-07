import requests
from typing import Union, Dict, Any
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CALC_URL = "http://localhost:8000/calculate"
HEALTH_URL = "http://localhost:8000/health"
TIMEOUT = 5  # seconds


def check_calculator_health() -> bool:
    """
    Check if the calculator API is running and healthy.
    Returns True if healthy, False otherwise.
    """
    try:
        response = requests.get(HEALTH_URL, timeout=2)
        return response.status_code == 200 and response.json().get("status") == "healthy"
    except Exception:
        return False


def call_calculator(expr: str) -> Union[float, str]:
    """
    Sends expression to the calculator API.
    
    Args:
        expr: Mathematical expression as a string
        
    Returns:
        float: Result of the calculation on success
        str: Error message on failure
    """
    if not expr or not expr.strip():
        return "Please provide a mathematical expression to calculate."
    
    # First check if the API is available
    if not check_calculator_health():
        return "Calculator service is not available. Please ensure the server is running."
    
    try:
        logger.info(f"Calling calculator API with expression: {expr}")
        
        response = requests.post(
            CALC_URL, 
            json={"expression": expr}, 
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        # Handle successful response
        if response.status_code == 200:
            result_data = response.json()
            result = result_data["result"]
            logger.info(f"Calculator API returned: {result}")
            return result
        
        # Handle client errors (4xx)
        elif response.status_code >= 400 and response.status_code < 500:
            try:
                error_detail = response.json().get("detail", "Unknown error")
            except:
                error_detail = response.text or "Bad request"
            logger.warning(f"Calculator API client error: {error_detail}")
            return f"Calculation error: {error_detail}"
        
        # Handle server errors (5xx)
        else:
            logger.error(f"Calculator API server error: {response.status_code}")
            return "Calculator service is experiencing issues. Please try again later."
            
    except requests.exceptions.Timeout:
        logger.error("Calculator API request timed out")
        return "Calculator request timed out. Please try again."
    
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to calculator API")
        return "Cannot connect to calculator service. Please ensure the server is running on localhost:8000."
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Calculator API request failed: {e}")
        return f"Network error calling calculator: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error calling calculator: {e}")
        return f"Unexpected error calling calculator: {str(e)}"


def call_calculator_with_retry(expr: str, max_retries: int = 2) -> Union[float, str]:
    """
    Call calculator with retry logic for transient failures.
    
    Args:
        expr: Mathematical expression
        max_retries: Maximum number of retry attempts
        
    Returns:
        Result or error message
    """
    for attempt in range(max_retries + 1):
        result = call_calculator(expr)
        
        # If we got a number, return it
        if isinstance(result, (int, float)):
            return result
        
        # If it's a non-retryable error, return immediately
        if any(keyword in str(result).lower() for keyword in [
            "calculation error", "expression", "division by zero", "invalid"
        ]):
            return result
        
        # For network/service errors, retry if we have attempts left
        if attempt < max_retries:
            logger.info(f"Retrying calculator call (attempt {attempt + 2}/{max_retries + 1})")
            time.sleep(1)  # Brief delay before retry
        
    return result


# Convenience functions for common operations
def add(a: float, b: float) -> Union[float, str]:
    """Add two numbers"""
    return call_calculator(f"{a} + {b}")


def subtract(a: float, b: float) -> Union[float, str]:
    """Subtract two numbers"""
    return call_calculator(f"{a} - {b}")


def multiply(a: float, b: float) -> Union[float, str]:
    """Multiply two numbers"""
    return call_calculator(f"{a} * {b}")


def divide(a: float, b: float) -> Union[float, str]:
    """Divide two numbers"""
    return call_calculator(f"{a} / {b}")


# For testing and demonstration
if __name__ == "__main__":
    print("Calculator Tool Client Test")
    print("=" * 30)
    
    test_expressions = [
        "2 + 3",
        "10 * 5",
        "100 / 4",
        "15 - 7",
        "(2 + 3) * 4",
        "10 / 0",  # Division by zero
        "abc + def",  # Invalid expression
        "",  # Empty expression
    ]
    
    for expr in test_expressions:
        print(f"Expression: '{expr}'")
        result = call_calculator(expr)
        print(f"Result: {result}")
        print() 