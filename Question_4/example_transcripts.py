"""
Example transcripts demonstrating ZUS Coffee API endpoints
Shows success and failure modes for /products and /outlets endpoints
"""

# =============================================================================
# PRODUCTS ENDPOINT (/products) - RAG with Vector Store
# =============================================================================

PRODUCTS_SUCCESS_EXAMPLES = """
--- Products Endpoint Success Examples ---

Example 1: Tumbler Query
User: "What types of tumblers do you offer?"
API: GET /products?query=What%20types%20of%20tumblers%20do%20you%20offer%3F
Response: {
  "query": "What types of tumblers do you offer?",
  "answer": "I'm currently in demo mode and don't have access to the full product knowledge base. However, I can tell you that ZUS Coffee offers a variety of drinkware products including tumblers, mugs, and travel cups. For detailed product information about 'What types of tumblers do you offer?', please visit https://shop.zuscoffee.com/collections/drinkware or contact ZUS Coffee directly.",
  "status": "fallback_mode"
}

Example 2: Mug Query
User: "Do you have ceramic mugs?"
API: GET /products?query=Do%20you%20have%20ceramic%20mugs%3F
Response: {
  "query": "Do you have ceramic mugs?",
  "answer": "I'm currently in demo mode and don't have access to the full product knowledge base. However, I can tell you that ZUS Coffee offers a variety of drinkware products including tumblers, mugs, and travel cups. For detailed product information about 'Do you have ceramic mugs?', please visit https://shop.zuscoffee.com/collections/drinkware or contact ZUS Coffee directly.",
  "status": "fallback_mode"
}

Example 3: Travel Cup Query
User: "Show me travel cups with lids"
API: GET /products?query=Show%20me%20travel%20cups%20with%20lids
Response: {
  "query": "Show me travel cups with lids",
  "answer": "I'm currently in demo mode and don't have access to the full product knowledge base. However, I can tell you that ZUS Coffee offers a variety of drinkware products including tumblers, mugs, and travel cups. For detailed product information about 'Show me travel cups with lids', please visit https://shop.zuscoffee.com/collections/drinkware or contact ZUS Coffee directly.",
  "status": "fallback_mode"
}
"""

PRODUCTS_FAILURE_EXAMPLES = """
--- Products Endpoint Failure Examples ---

Example 1: Query Too Short
User: "mu"
API: GET /products?query=mu
Response: {
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["query", "query"],
      "msg": "String should have at least 3 characters",
      "input": "mu"
    }
  ]
}
Status: 422 Unprocessable Entity

Example 2: Missing Query Parameter
User: (no query provided)
API: GET /products
Response: {
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "query"],
      "msg": "Field required",
      "input": null
    }
  ]
}
Status: 422 Unprocessable Entity

Example 3: Vector Store Unavailable
User: "What drinkware do you have?"
API: GET /products?query=What%20drinkware%20do%20you%20have%3F
Response: {
  "query": "What drinkware do you have?",
  "answer": "I'm currently in demo mode and don't have access to the full product knowledge base. However, I can tell you that ZUS Coffee offers a variety of drinkware products including tumblers, mugs, and travel cups. For detailed product information about 'What drinkware do you have?', please visit https://shop.zuscoffee.com/collections/drinkware or contact ZUS Coffee directly.",
  "status": "fallback_mode"
}
"""

# =============================================================================
# OUTLETS ENDPOINT (/outlets) - Text2SQL
# =============================================================================

OUTLETS_SUCCESS_EXAMPLES = """
--- Outlets Endpoint Success Examples ---

Example 1: Location Query (Fallback Mode)
User: "Which outlets are in Kuala Lumpur?"
API: GET /outlets?query=Which%20outlets%20are%20in%20Kuala%20Lumpur%3F
Response: {
  "query": "Which outlets are in Kuala Lumpur?",
  "result": "Found 4 outlet(s):\n• KLCC Outlet (Kuala Lumpur) - 10:00 AM - 10:00 PM\n• Mid Valley Outlet (Kuala Lumpur) - 10:00 AM - 10:00 PM\n• Bangsar Village Outlet (Kuala Lumpur) - 8:00 AM - 11:00 PM",
  "status": "fallback_mode"
}

Example 2: Hours Query (Fallback Mode)
User: "Which outlets open late at night?"
API: GET /outlets?query=Which%20outlets%20open%20late%20at%20night%3F
Response: {
  "query": "Which outlets open late at night?",
  "result": "Found 1 outlet(s):\n• Bangsar Village Outlet (Kuala Lumpur) - 8:00 AM - 11:00 PM",
  "status": "fallback_mode"
}

Example 3: City-specific Query (Fallback Mode)
User: "outlets in Petaling Jaya"
API: GET /outlets?query=outlets%20in%20Petaling%20Jaya
Response: {
  "query": "outlets in Petaling Jaya",
  "result": "Found 2 outlet(s):\n• SS 2 Outlet (Petaling Jaya) - 9:00 AM - 10:00 PM\n• PJ Central Outlet (Petaling Jaya) - 10:00 AM - 9:00 PM",
  "status": "fallback_mode"
}

Example 4: Early Opening Query (Fallback Mode)
User: "Which outlets open early in the morning?"
API: GET /outlets?query=Which%20outlets%20open%20early%20in%20the%20morning%3F
Response: {
  "query": "Which outlets open early in the morning?",
  "result": "Found 1 outlet(s):\n• Bangsar Village Outlet (Kuala Lumpur) - 8:00 AM - 11:00 PM",
  "status": "fallback_mode"
}

Example 5: List All Outlets
User: (Direct endpoint call)
API: GET /outlets/list
Response: {
  "outlets": [
    {
      "id": 1,
      "name": "SS 2 Outlet",
      "city": "Petaling Jaya",
      "address": "123 SS 2/75, Petaling Jaya, Selangor",
      "hours": "9:00 AM - 10:00 PM",
      "services": "Dine-in, Takeaway, Delivery"
    },
    {
      "id": 2,
      "name": "PJ Central Outlet",
      "city": "Petaling Jaya", 
      "address": "PJ Central Mall, Petaling Jaya, Selangor",
      "hours": "10:00 AM - 9:00 PM",
      "services": "Dine-in, Takeaway"
    },
    // ... (additional outlets)
  ]
}
"""

OUTLETS_FAILURE_EXAMPLES = """
--- Outlets Endpoint Failure Examples ---

Example 1: Query Too Short
User: "KL"
API: GET /outlets?query=KL
Response: {
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["query", "query"],
      "msg": "String should have at least 3 characters", 
      "input": "KL"
    }
  ]
}
Status: 422 Unprocessable Entity

Example 2: Missing Query Parameter
User: (no query provided)
API: GET /outlets
Response: {
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "query"],
      "msg": "Field required",
      "input": null
    }
  ]
}
Status: 422 Unprocessable Entity

Example 3: OpenAI API Key Not Available (if using LLM mode)
User: "Find outlets with drive-thru service"
API: GET /outlets?query=Find%20outlets%20with%20drive-thru%20service
Response: {
  "detail": "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
}
Status: 503 Service Unavailable

Example 4: Database Connection Error
User: "Show me all outlets"
API: GET /outlets?query=Show%20me%20all%20outlets
Response: {
  "detail": "Internal server error: database connection failed"
}
Status: 500 Internal Server Error

Example 5: Complex Query in Fallback Mode
User: "Find outlets with specific WiFi requirements and parking"
API: GET /outlets?query=Find%20outlets%20with%20specific%20WiFi%20requirements%20and%20parking
Response: {
  "query": "Find outlets with specific WiFi requirements and parking",
  "result": "Found 6 outlet(s):\n• SS 2 Outlet (Petaling Jaya) - 9:00 AM - 10:00 PM\n• PJ Central Outlet (Petaling Jaya) - 10:00 AM - 9:00 PM\n• KLCC Outlet (Kuala Lumpur) - 10:00 AM - 10:00 PM\n• Mid Valley Outlet (Kuala Lumpur) - 10:00 AM - 10:00 PM\n• IOI City Mall Outlet (Putrajaya) - 10:00 AM - 10:00 PM\n• Bangsar Village Outlet (Kuala Lumpur) - 8:00 AM - 11:00 PM",
  "status": "fallback_mode"
}
"""

# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

HEALTH_CHECK_EXAMPLES = """
--- Health Check Examples ---

Products Health Check:
API: GET /products/health
Response: {
  "vector_store_loaded": false,
  "openai_api_available": false,
  "embeddings_available": true,
  "fallback_mode": false,
  "status": "fallback"
}

Outlets Health Check:
API: GET /outlets/health  
Response: {
  "database_connected": true,
  "outlet_count": 6,
  "openai_api_available": false,
  "status": "degraded"
}

Main API Health Check:
API: GET /health
Response: {
  "status": "healthy",
  "service": "zus-coffee-api"
}
"""

# =============================================================================
# CHATBOT INTEGRATION EXAMPLES
# =============================================================================

CHATBOT_INTEGRATION_EXAMPLES = """
--- Chatbot Integration Examples ---

Example 1: Product Query Integration
User: "What mugs do you have?"
Chatbot Intent: PRODUCT_SEARCH
Chatbot calls: call_products("What mugs do you have?")
API Response: Fallback mode response with general drinkware info
Chatbot Reply: "I'm currently in demo mode and don't have access to the full product knowledge base. However, I can tell you that ZUS Coffee offers a variety of drinkware products including tumblers, mugs, and travel cups. For detailed product information about 'What mugs do you have?', please visit https://shop.zuscoffee.com/collections/drinkware or contact ZUS Coffee directly."

Example 2: Outlet Query Integration  
User: "Where are your KL outlets?"
Chatbot Intent: OUTLET_SEARCH
Chatbot calls: call_outlets("Where are your KL outlets?")
API Response: List of Kuala Lumpur outlets
Chatbot Reply: "Found 3 outlet(s):\n• KLCC Outlet (Kuala Lumpur) - 10:00 AM - 10:00 PM\n• Mid Valley Outlet (Kuala Lumpur) - 10:00 AM - 10:00 PM\n• Bangsar Village Outlet (Kuala Lumpur) - 8:00 AM - 11:00 PM"

Example 3: API Unavailable Scenario
User: "Show me tumblers"
Chatbot Intent: PRODUCT_SEARCH
Chatbot calls: call_products("Show me tumblers") 
API Response: Connection error (server down)
Chatbot Reply: "Cannot connect to product service. Please ensure the API server is running."

Example 4: Mixed Query Handling
User: "I want a tumbler from your Bangsar outlet"
Chatbot Intent: MIXED (products + outlets)
Chatbot calls: 
  1. call_products("tumbler") 
  2. call_outlets("Bangsar outlet")
Combined Response: Product info + outlet details for Bangsar Village
"""

def main():
    """Print all example transcripts"""
    print("ZUS Coffee API - Example Transcripts")
    print("=" * 50)
    
    print(PRODUCTS_SUCCESS_EXAMPLES)
    print(PRODUCTS_FAILURE_EXAMPLES)
    print(OUTLETS_SUCCESS_EXAMPLES)
    print(OUTLETS_FAILURE_EXAMPLES)
    print(HEALTH_CHECK_EXAMPLES)
    print(CHATBOT_INTEGRATION_EXAMPLES)

if __name__ == "__main__":
    main() 