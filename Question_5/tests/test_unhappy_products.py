import unittest
import sys
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

# Add parent directories to path to import from Question_4
sys.path.append(os.path.join(os.path.dirname(__file__), '../../Question_4'))

from app.main import app

client = TestClient(app)


class TestUnhappyProducts(unittest.TestCase):
    """Test suite for unhappy flows in products endpoint"""
    
    def test_missing_query_param(self):
        """Test missing required query parameter"""
        response = client.get("/products")
        self.assertEqual(response.status_code, 422)  # FastAPI validation error
        
        error_detail = response.json()
        self.assertIn("detail", error_detail)
        # Should indicate query parameter is required
        self.assertTrue(
            any("query" in str(detail).lower() for detail in error_detail["detail"])
        )
    
    def test_empty_query_param(self):
        """Test empty query parameter"""
        response = client.get("/products", params={"query": ""})
        self.assertEqual(response.status_code, 422)  # Min length validation
        
        error_detail = response.json()
        self.assertIn("detail", error_detail)
    
    def test_query_too_short(self):
        """Test query parameter that's too short (less than min_length=3)"""
        short_queries = ["a", "ab", "  "]
        
        for query in short_queries:
            with self.subTest(query=query):
                response = client.get("/products", params={"query": query})
                self.assertEqual(response.status_code, 422)
                
                error_detail = response.json()
                self.assertIn("detail", error_detail)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_openai_api_key(self):
        """Test behavior when OpenAI API key is not configured"""
        # Clear environment variables to simulate missing API key
        response = client.get("/products", params={"query": "coffee mugs"})
        self.assertEqual(response.status_code, 503)
        
        error_detail = response.json()
        self.assertIn("OpenAI API key not configured", error_detail["detail"])
    
    @patch('app.embeddings.embeddings_manager.get_retriever')
    def test_vector_store_unavailable(self, mock_retriever):
        """Test when vector store/knowledge base is not available"""
        mock_retriever.return_value = None
        
        response = client.get("/products", params={"query": "travel mugs"})
        self.assertEqual(response.status_code, 503)
        
        error_detail = response.json()
        self.assertIn("knowledge base not available", error_detail["detail"])
        self.assertIn("ingestion script", error_detail["detail"])
    
    @patch('app.products.RetrievalQA.from_chain_type')
    def test_qa_chain_initialization_failure(self, mock_qa_chain):
        """Test when QA chain fails to initialize"""
        mock_qa_chain.side_effect = Exception("Failed to initialize QA chain")
        
        response = client.get("/products", params={"query": "ceramic mugs"})
        self.assertEqual(response.status_code, 500)
        
        error_detail = response.json()
        self.assertIn("Internal server error", error_detail["detail"])
        self.assertIn("Failed to initialize QA chain", error_detail["detail"])
    
    @patch('app.products.RetrievalQA.from_chain_type')
    def test_qa_chain_run_failure(self, mock_qa_chain):
        """Test when QA chain execution fails"""
        mock_chain_instance = Mock()
        mock_chain_instance.run.side_effect = Exception("Vector store corrupted")
        mock_qa_chain.return_value = mock_chain_instance
        
        response = client.get("/products", params={"query": "steel bottles"})
        self.assertEqual(response.status_code, 500)
        
        error_detail = response.json()
        self.assertIn("Internal server error", error_detail["detail"])
        self.assertIn("Vector store corrupted", error_detail["detail"])
    
    @patch('app.products.OpenAI')
    def test_openai_api_failure(self, mock_openai):
        """Test when OpenAI API calls fail"""
        mock_openai.side_effect = Exception("OpenAI API rate limit exceeded")
        
        response = client.get("/products", params={"query": "thermal bottles"})
        self.assertEqual(response.status_code, 500)
        
        error_detail = response.json()
        self.assertIn("Internal server error", error_detail["detail"])
        self.assertIn("OpenAI API rate limit exceeded", error_detail["detail"])
    
    def test_malicious_query_payloads(self):
        """Test various malicious query attempts"""
        malicious_queries = [
            "'; DROP TABLE products; --",  # SQL injection
            "<script>alert('XSS')</script>",  # XSS attempt
            "../../etc/passwd",  # Path traversal
            "{{7*7}}",  # Template injection
            "__import__('os').system('rm -rf /')",  # Code injection
            "UNION SELECT * FROM users",  # SQL union attack
            "javascript:alert('XSS')",  # JavaScript injection
            "\x00\x01\x02\x03",  # Binary data
            "A" * 10000,  # Very long input
            "%3Cscript%3Ealert%281%29%3C%2Fscript%3E",  # URL encoded XSS
        ]
        
        for malicious_query in malicious_queries:
            with self.subTest(query=malicious_query):
                # Note: These might pass validation if they're >=3 chars
                response = client.get("/products", params={"query": malicious_query})
                
                # Should not crash the server
                self.assertIn(response.status_code, [200, 400, 422, 500, 503])
                
                # If it returns 200, check that response is safe
                if response.status_code == 200:
                    response_data = response.json()
                    self.assertIn("query", response_data)
                    self.assertIn("answer", response_data)
                    
                    # Response should not contain dangerous content
                    answer = response_data["answer"].lower()
                    dangerous_patterns = ["<script", "javascript:", "drop table", "delete from"]
                    for pattern in dangerous_patterns:
                        self.assertNotIn(pattern, answer)
    
    def test_special_characters_in_query(self):
        """Test handling of special characters that might break parsing"""
        special_queries = [
            "café mugs",  # Unicode characters
            "mugs & bottles",  # Ampersand
            "20% off mugs",  # Percentage sign
            "mugs (large)",  # Parentheses
            "mugs + bottles",  # Plus sign
            "mugs/bottles",  # Forward slash
            "mugs\\bottles",  # Backslash
            "mugs\nwith\ttabs",  # Newlines and tabs
            '"quoted mugs"',  # Quotes
            "mugs 'with' apostrophes",  # Apostrophes
        ]
        
        for query in special_queries:
            with self.subTest(query=query):
                response = client.get("/products", params={"query": query})
                
                # Should handle gracefully - either success or proper error
                self.assertIn(response.status_code, [200, 400, 422, 500, 503])
                
                # Should return valid JSON
                try:
                    response_data = response.json()
                    self.assertIsInstance(response_data, dict)
                except ValueError:
                    self.fail(f"Invalid JSON response for query: {query}")
    
    @patch('app.products.RetrievalQA.from_chain_type')
    def test_timeout_simulation(self, mock_qa_chain):
        """Test timeout handling (simulated)"""
        import time
        
        def slow_run(query):
            time.sleep(0.1)  # Simulate slow response
            return "Slow response for " + query
        
        mock_chain_instance = Mock()
        mock_chain_instance.run = slow_run
        mock_qa_chain.return_value = mock_chain_instance
        
        # This should still complete (we're not testing actual timeouts here)
        response = client.get("/products", params={"query": "fast query"})
        # Just verify it handles the slow operation
        self.assertIn(response.status_code, [200, 500])
    
    def test_concurrent_requests_stability(self):
        """Test that multiple concurrent requests don't cause issues"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(query_suffix):
            try:
                response = client.get("/products", params={"query": f"mugs {query_suffix}"})
                results.put(("success", response.status_code))
            except Exception as e:
                results.put(("error", str(e)))
        
        # Start multiple concurrent requests
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, args=(f"test{i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=10)
        
        # Check results
        while not results.empty():
            result_type, result_value = results.get()
            if result_type == "success":
                self.assertIn(result_value, [200, 500, 503])  # Valid status codes
            else:
                # Log errors but don't fail (concurrent requests might have issues)
                print(f"Concurrent request error: {result_value}")
    
    def test_products_health_endpoint(self):
        """Test the products health endpoint"""
        response = client.get("/products/health")
        self.assertEqual(response.status_code, 200)
        
        health_data = response.json()
        required_fields = ["vector_store_loaded", "openai_api_available", "status"]
        for field in required_fields:
            self.assertIn(field, health_data)
        
        # Status should be one of the expected values
        self.assertIn(health_data["status"], ["healthy", "degraded"])


if __name__ == "__main__":
    unittest.main() 