"""
Chatbot integration code for ZUS Coffee API endpoints.
Demonstrates how to call /products and /outlets from a conversational agent.
"""

import requests
from typing import Dict, Optional
import time

ZUS_API = "http://localhost:8000"
TIMEOUT = 5

def call_products(query: str) -> str:
    """
    Call the products RAG endpoint.
    
    Args:
        query: User question about ZUS drinkware products
        
    Returns:
        AI-generated product information or error message
    """
    try:
        response = requests.get(
            f"{ZUS_API}/products",
            params={"query": query},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["answer"]
        elif response.status_code == 503:
            return "Product search is currently unavailable. Please try again later."
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return f"Product search error: {error_detail}"
            
    except requests.exceptions.Timeout:
        return "Product search timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "Cannot connect to product service. Please ensure the API server is running."
    except Exception as e:
        return f"Error calling product service: {str(e)}"

def call_outlets(query: str) -> str:
    """
    Call the outlets Text2SQL endpoint.
    
    Args:
        query: Natural language query about ZUS outlets
        
    Returns:
        SQL query results or error message
    """
    try:
        response = requests.get(
            f"{ZUS_API}/outlets",
            params={"query": query},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["result"]
        elif response.status_code == 400:
            return "Sorry, I couldn't understand that outlet query. Please ask about locations, hours, or services."
        elif response.status_code == 503:
            return "Outlet search is currently unavailable. Please try again later."
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return f"Outlet search error: {error_detail}"
            
    except requests.exceptions.Timeout:
        return "Outlet search timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return "Cannot connect to outlet service. Please ensure the API server is running."
    except Exception as e:
        return f"Error calling outlet service: {str(e)}"

def check_api_health() -> Dict[str, bool]:
    """Check if both API endpoints are healthy"""
    health_status = {
        "api_server": False,
        "products": False,
        "outlets": False
    }
    
    try:
        # Check main health endpoint
        response = requests.get(f"{ZUS_API}/health", timeout=2)
        health_status["api_server"] = response.status_code == 200
        
        # Check products health
        response = requests.get(f"{ZUS_API}/products/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            health_status["products"] = data.get("status") == "healthy"
        
        # Check outlets health
        response = requests.get(f"{ZUS_API}/outlets/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            health_status["outlets"] = data.get("status") == "healthy"
            
    except Exception:
        pass  # Health status remains False
    
    return health_status

# Integration with agentic bot (example usage)
class ZUSChatbot:
    """Example chatbot that uses ZUS API endpoints"""
    
    def __init__(self):
        self.api_healthy = False
        self._check_api_status()
    
    def _check_api_status(self):
        """Check API health on initialization"""
        health = check_api_health()
        self.api_healthy = health["api_server"]
        
        if not self.api_healthy:
            print("Warning: ZUS API server is not available")
    
    def process_query(self, user_input: str) -> str:
        """
        Process user query and route to appropriate endpoint.
        
        This would integrate with your existing agentic bot's execute() method:
        
        def execute(action: Action, **kwargs) -> Dict[str, str]:
            if action == Action.CALL_RAG:
                summary = call_products(kwargs["query"])
                return {"reply": summary}
            
            if action == Action.CALL_TEXT2SQL:
                data = call_outlets(kwargs["query"])
                return {"reply": data}
        """
        if not self.api_healthy:
            return "ZUS services are currently unavailable. Please try again later."
        
        # Simple intent detection (you'd use your existing intent extractor)
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['mug', 'tumbler', 'bottle', 'cup', 'drinkware', 'product']):
            return call_products(user_input)
        elif any(word in user_lower for word in ['outlet', 'store', 'location', 'hours', 'address']):
            return call_outlets(user_input)
        else:
            return "I can help you with ZUS drinkware products or outlet information. What would you like to know?"

def demo_api_calls():
    """Demonstrate API calls with example queries"""
    print("ZUS Coffee API Integration Demo")
    print("=" * 40)
    
    # Check API health
    health = check_api_health()
    print(f"API Health: {health}")
    
    if not health["api_server"]:
        print("❌ API server not available. Please start with: uvicorn app.main:app --reload")
        return
    
    # Test products endpoint
    print("\n--- Products Endpoint ---")
    product_queries = [
        "What types of tumblers do you offer?",
        "Do you sell tea infusers?",
        "Show me your mugs"
    ]
    
    for query in product_queries:
        print(f"\nQuery: {query}")
        result = call_products(query)
        print(f"Response: {result}")
        time.sleep(1)
    
    # Test outlets endpoint  
    print("\n--- Outlets Endpoint ---")
    outlet_queries = [
        "Which outlets are in Kuala Lumpur?",
        "What are the hours for SS 2 outlet?",
        "Which outlets have drive-thru service?"
    ]
    
    for query in outlet_queries:
        print(f"\nQuery: {query}")
        result = call_outlets(query)
        print(f"Response: {result}")
        time.sleep(1)

if __name__ == "__main__":
    demo_api_calls() 