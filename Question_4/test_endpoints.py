#!/usr/bin/env python3
"""
Test script for all ZUS Coffee API endpoints
Contains curl commands and Python requests for testing all examples from transcripts
"""

import requests
import json
from urllib.parse import quote

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_curl_command(description, curl_cmd, url, expected_status=200):
    """Test an endpoint and show both curl command and result"""
    print(f"\n--- {description} ---")
    print(f"Curl: {curl_cmd}")
    print(f"URL:  {url}")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == expected_status
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run all endpoint tests"""
    
    print("🧪 ZUS Coffee API Endpoint Tests")
    print("Make sure your server is running: python -m app.main")
    print("Server should be at: http://localhost:8000")
    
    # =================================================================
    # HEALTH CHECKS FIRST
    # =================================================================
    print_section("HEALTH CHECKS")
    
    test_curl_command(
        "Main API Health Check",
        "curl http://localhost:8000/health",
        f"{BASE_URL}/health"
    )
    
    test_curl_command(
        "Products Health Check", 
        "curl http://localhost:8000/products/health",
        f"{BASE_URL}/products/health"
    )
    
    test_curl_command(
        "Outlets Health Check",
        "curl http://localhost:8000/outlets/health", 
        f"{BASE_URL}/outlets/health"
    )
    
    # =================================================================
    # PRODUCTS ENDPOINT - SUCCESS EXAMPLES
    # =================================================================
    print_section("PRODUCTS ENDPOINT - SUCCESS EXAMPLES")
    
    test_curl_command(
        "Example 1: Tumbler Query",
        'curl "http://localhost:8000/products?query=What%20types%20of%20tumblers%20do%20you%20offer%3F"',
        f"{BASE_URL}/products?query=What%20types%20of%20tumblers%20do%20you%20offer%3F"
    )
    
    test_curl_command(
        "Example 2: Mug Query", 
        'curl "http://localhost:8000/products?query=Do%20you%20have%20ceramic%20mugs%3F"',
        f"{BASE_URL}/products?query=Do%20you%20have%20ceramic%20mugs%3F"
    )
    
    test_curl_command(
        "Example 3: Travel Cup Query",
        'curl "http://localhost:8000/products?query=Show%20me%20travel%20cups%20with%20lids"',
        f"{BASE_URL}/products?query=Show%20me%20travel%20cups%20with%20lids"
    )
    
    # =================================================================
    # PRODUCTS ENDPOINT - FAILURE EXAMPLES  
    # =================================================================
    print_section("PRODUCTS ENDPOINT - FAILURE EXAMPLES")
    
    test_curl_command(
        "Example 1: Query Too Short",
        'curl "http://localhost:8000/products?query=mu"',
        f"{BASE_URL}/products?query=mu",
        expected_status=422
    )
    
    test_curl_command(
        "Example 2: Missing Query Parameter",
        'curl "http://localhost:8000/products"',
        f"{BASE_URL}/products",
        expected_status=422
    )
    
    # =================================================================
    # OUTLETS ENDPOINT - SUCCESS EXAMPLES
    # =================================================================
    print_section("OUTLETS ENDPOINT - SUCCESS EXAMPLES")
    
    test_curl_command(
        "Example 1: Location Query (KL)",
        'curl "http://localhost:8000/outlets?query=Which%20outlets%20are%20in%20Kuala%20Lumpur%3F"',
        f"{BASE_URL}/outlets?query=Which%20outlets%20are%20in%20Kuala%20Lumpur%3F"
    )
    
    test_curl_command(
        "Example 2: Hours Query (Late Night)",
        'curl "http://localhost:8000/outlets?query=Which%20outlets%20open%20late%20at%20night%3F"',
        f"{BASE_URL}/outlets?query=Which%20outlets%20open%20late%20at%20night%3F"
    )
    
    test_curl_command(
        "Example 3: City-specific Query (PJ)",
        'curl "http://localhost:8000/outlets?query=outlets%20in%20Petaling%20Jaya"',
        f"{BASE_URL}/outlets?query=outlets%20in%20Petaling%20Jaya"
    )
    
    test_curl_command(
        "Example 4: Early Opening Query", 
        'curl "http://localhost:8000/outlets?query=Which%20outlets%20open%20early%20in%20the%20morning%3F"',
        f"{BASE_URL}/outlets?query=Which%20outlets%20open%20early%20in%20the%20morning%3F"
    )
    
    test_curl_command(
        "Example 5: List All Outlets",
        'curl "http://localhost:8000/outlets/list"',
        f"{BASE_URL}/outlets/list"
    )
    
    # =================================================================
    # OUTLETS ENDPOINT - FAILURE EXAMPLES
    # =================================================================
    print_section("OUTLETS ENDPOINT - FAILURE EXAMPLES")
    
    test_curl_command(
        "Example 1: Query Too Short", 
        'curl "http://localhost:8000/outlets?query=KL"',
        f"{BASE_URL}/outlets?query=KL",
        expected_status=422
    )
    
    test_curl_command(
        "Example 2: Missing Query Parameter",
        'curl "http://localhost:8000/outlets"',
        f"{BASE_URL}/outlets", 
        expected_status=422
    )
    
    # =================================================================
    # ADDITIONAL USEFUL ENDPOINTS
    # =================================================================
    print_section("ADDITIONAL ENDPOINTS")
    
    test_curl_command(
        "Root Endpoint",
        'curl "http://localhost:8000/"',
        f"{BASE_URL}/"
    )
    
    test_curl_command(
        "API Documentation (OpenAPI)",
        'curl "http://localhost:8000/openapi.json"',
        f"{BASE_URL}/openapi.json"
    )

if __name__ == "__main__":
    main() 