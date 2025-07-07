import unittest
import sys
import os
from unittest.mock import patch, Mock
import requests

# Add parent directories to path to import from Question_3
sys.path.append(os.path.join(os.path.dirname(__file__), '../../Question_3'))

from calculator_tool import call_calculator, call_calculator_with_retry, check_calculator_health
from agentic_bot import CalculatorBot


class TestUnhappyCalculator(unittest.TestCase):
    """Test suite for unhappy flows in calculator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = CalculatorBot()
    
    def test_missing_parameter_empty_input(self):
        """Test bot response when user just says 'Calculate' with no expression"""
        response = self.bot.process_input("Calculate")
        self.assertIn("provide a mathematical expression", response.lower())
        self.assertIn("2 + 3", response)  # Should provide examples
    
    def test_missing_parameter_vague_request(self):
        """Test bot response to vague math requests"""
        test_cases = [
            "compute",
            "math",
            "do some calculation",
            "help me with math"
        ]
        
        for test_input in test_cases:
            with self.subTest(input=test_input):
                response = self.bot.process_input(test_input)
                self.assertIn("mathematical expression", response.lower())
    
    def test_empty_expression_direct_call(self):
        """Test direct calculator call with empty expression"""
        result = call_calculator("")
        self.assertIsInstance(result, str)
        self.assertIn("provide a mathematical expression", result.lower())
        
        # Test whitespace-only input
        result = call_calculator("   ")
        self.assertIsInstance(result, str)
        self.assertIn("provide a mathematical expression", result.lower())
    
    @patch('calculator_tool.requests.post')
    @patch('calculator_tool.check_calculator_health')
    def test_api_downtime_500_error(self, mock_health, mock_post):
        """Test handling of HTTP 500 server errors"""
        # Health check passes but API call fails
        mock_health.return_value = True
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Internal Server Error"
        
        result = call_calculator("5 + 3")
        self.assertIsInstance(result, str)
        self.assertIn("service is experiencing issues", result.lower())
    
    @patch('calculator_tool.requests.post')
    @patch('calculator_tool.check_calculator_health')
    def test_api_downtime_503_error(self, mock_health, mock_post):
        """Test handling of HTTP 503 service unavailable"""
        mock_health.return_value = True
        mock_post.return_value.status_code = 503
        mock_post.return_value.text = "Service Unavailable"
        
        result = call_calculator("10 / 2")
        self.assertIsInstance(result, str)
        self.assertIn("service is experiencing issues", result.lower())
    
    @patch('calculator_tool.requests.post')
    def test_connection_error(self, mock_post):
        """Test handling of connection errors"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        result = call_calculator("2 * 4")
        self.assertIsInstance(result, str)
        self.assertIn("connect to calculator service", result.lower())
    
    @patch('calculator_tool.requests.post')
    def test_timeout_error(self, mock_post):
        """Test handling of request timeouts"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = call_calculator("15 - 7")
        self.assertIsInstance(result, str)
        self.assertIn("timed out", result.lower())
    
    @patch('calculator_tool.check_calculator_health')
    def test_service_health_check_failure(self, mock_health):
        """Test when health check fails"""
        mock_health.return_value = False
        
        result = call_calculator("1 + 1")
        self.assertIsInstance(result, str)
        self.assertIn("not available", result.lower())
    
    @patch('calculator_tool.call_calculator')
    def test_retry_mechanism_transient_failures(self, mock_calc):
        """Test retry logic with transient network failures"""
        # First call fails, second succeeds
        mock_calc.side_effect = [
            "Cannot connect to calculator service. Please ensure the server is running on localhost:8000.",
            8.0  # Success on retry
        ]
        
        result = call_calculator_with_retry("2 + 6", max_retries=1)
        self.assertEqual(result, 8.0)
        self.assertEqual(mock_calc.call_count, 2)
    
    @patch('calculator_tool.call_calculator')
    def test_retry_mechanism_permanent_failure(self, mock_calc):
        """Test retry logic when all attempts fail"""
        mock_calc.side_effect = [
            "Connection failed",
            "Connection failed"
        ]
        
        result = call_calculator_with_retry("2 + 2", max_retries=1)
        self.assertIsInstance(result, str)
        self.assertIn("connection failed", result.lower())
        self.assertEqual(mock_calc.call_count, 2)
    
    @patch('calculator_tool.call_calculator')
    def test_retry_no_retry_on_calculation_errors(self, mock_calc):
        """Test that calculation errors don't trigger retries"""
        mock_calc.return_value = "Calculation error: Division by zero"
        
        result = call_calculator_with_retry("5 / 0", max_retries=2)
        self.assertIsInstance(result, str)
        self.assertIn("division by zero", result.lower())
        self.assertEqual(mock_calc.call_count, 1)  # No retry for calc errors
    
    def test_malicious_payload_attempts(self):
        """Test various malicious input attempts"""
        malicious_inputs = [
            "__import__('os').system('rm -rf /')",  # Code injection attempt
            "eval('__import__(\"os\").system(\"ls\")')",  # Eval injection
            "1 + 1; import subprocess; subprocess.call(['ls'])",  # Multi-statement
            "' OR 1=1 --",  # SQL injection pattern
            "../../etc/passwd",  # Path traversal
            "<script>alert('xss')</script>",  # XSS attempt
            "{{7*7}}",  # Template injection
            "A" * 10000,  # Buffer overflow attempt
        ]
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                # These should either be safely handled or return error messages
                result = call_calculator(malicious_input)
                # Should not crash and should return a string error message
                self.assertIsInstance(result, str)
                # Should not execute arbitrary code (no numeric result for malicious input)
                if isinstance(result, str):
                    self.assertTrue(
                        any(keyword in result.lower() for keyword in [
                            "error", "invalid", "calculation", "expression"
                        ]) or "not available" in result.lower()
                    )
    
    def test_bot_conversation_state_recovery(self):
        """Test bot state recovery after errors"""
        # Start with an error
        response1 = self.bot.process_input("calculate")
        self.assertIn("mathematical expression", response1.lower())
        
        # Should still work for valid input after error
        response2 = self.bot.process_input("2 + 2")
        # This might fail if calculator service is down, but bot should handle gracefully
        self.assertIsInstance(response2, str)
        self.assertTrue(len(response2) > 0)
    
    def test_conversation_memory_with_errors(self):
        """Test that conversation memory properly tracks errors"""
        # Generate some conversation with errors
        self.bot.process_input("calculate")
        self.bot.process_input("compute math")
        self.bot.process_input("2 + 2")
        
        summary = self.bot.get_conversation_summary()
        
        # Should have recorded all turns including errors
        self.assertGreaterEqual(len(summary["turns"]), 3)
        self.assertEqual(summary["total_turns"], 3)
        
        # Check that error handling actions were recorded
        history = self.bot.memory.get_conversation_history()
        error_turns = [turn for turn in history if "ASK_FOLLOWUP" in turn["action"]]
        self.assertGreaterEqual(len(error_turns), 2)  # First two were error cases
    
    def tearDown(self):
        """Clean up after each test"""
        self.bot.reset_conversation()


if __name__ == "__main__":
    unittest.main() 