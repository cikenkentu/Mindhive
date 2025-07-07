import unittest
from unittest.mock import patch, Mock
import requests
import time
import threading
import subprocess
import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from calculator_tool import call_calculator, call_calculator_with_retry, check_calculator_health
from agentic_bot import CalculatorBot


class TestCalculatorTool(unittest.TestCase):
    """Test the calculator tool HTTP client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_expressions = [
            ("2 + 3", 5.0),
            ("10 - 4", 6.0),
            ("6 * 7", 42.0),
            ("15 / 3", 5.0),
            ("(2 + 3) * 4", 20.0),
            ("100 / 4", 25.0),
            ("2.5 + 1.5", 4.0),
            ("10 * 0", 0.0)
        ]
        
        self.invalid_expressions = [
            "10 / 0",
            "abc + def",
            "",
            "   ",
            "2 + ",
            "* 5",
            "sqrt(16)",
            "2 ** 3"
        ]
    
    @patch('calculator_tool.requests.post')
    @patch('calculator_tool.check_calculator_health')
    def test_successful_calculation(self, mock_health, mock_post):
        """Test successful calculation via HTTP"""
        mock_health.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": 5.0, "expression": "2 + 3"}
        mock_post.return_value = mock_response
        
        result = call_calculator("2 + 3")
        self.assertEqual(result, 5.0)
        mock_post.assert_called_once()
    
    @patch('calculator_tool.requests.post')
    @patch('calculator_tool.check_calculator_health')
    def test_calculation_error(self, mock_health, mock_post):
        """Test calculation error handling"""
        mock_health.return_value = True
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Division by zero is not allowed"}
        mock_post.return_value = mock_response
        
        result = call_calculator("10 / 0")
        self.assertIsInstance(result, str)
        self.assertIn("Division by zero", result)
    
    @patch('calculator_tool.requests.post')
    @patch('calculator_tool.check_calculator_health')
    def test_network_timeout(self, mock_health, mock_post):
        """Test network timeout handling"""
        mock_health.return_value = True
        mock_post.side_effect = requests.exceptions.Timeout()
        
        result = call_calculator("2 + 3")
        self.assertIsInstance(result, str)
        self.assertIn("timed out", result.lower())
    
    @patch('calculator_tool.requests.post')
    @patch('calculator_tool.check_calculator_health')
    def test_connection_error(self, mock_health, mock_post):
        """Test connection error handling"""
        mock_health.return_value = True
        mock_post.side_effect = requests.exceptions.ConnectionError()
        
        result = call_calculator("2 + 3")
        self.assertIsInstance(result, str)
        self.assertIn("connect", result.lower())
    
    @patch('calculator_tool.check_calculator_health')
    def test_service_unavailable(self, mock_health):
        """Test service unavailable handling"""
        mock_health.return_value = False
        
        result = call_calculator("2 + 3")
        self.assertIsInstance(result, str)
        self.assertIn("not available", result.lower())
    
    def test_empty_expression(self):
        """Test empty expression handling"""
        result = call_calculator("")
        self.assertIsInstance(result, str)
        self.assertIn("provide", result.lower())
        
        result = call_calculator("   ")
        self.assertIsInstance(result, str)
        self.assertIn("provide", result.lower())
    
    @patch('calculator_tool.call_calculator')
    def test_retry_logic(self, mock_calc):
        """Test retry logic for transient failures"""
        # First call fails with network error, second succeeds
        mock_calc.side_effect = [
            "Network error calling calculator: Connection failed",
            5.0
        ]
        
        result = call_calculator_with_retry("2 + 3", max_retries=1)
        self.assertEqual(result, 5.0)
        self.assertEqual(mock_calc.call_count, 2)
    
    @patch('calculator_tool.call_calculator')
    def test_no_retry_for_calculation_errors(self, mock_calc):
        """Test that calculation errors don't trigger retries"""
        mock_calc.return_value = "Calculation error: Division by zero is not allowed"
        
        result = call_calculator_with_retry("10 / 0", max_retries=2)
        self.assertIn("Division by zero", result)
        self.assertEqual(mock_calc.call_count, 1)  # No retry


class TestAgenticBot(unittest.TestCase):
    """Test the agentic bot integration with calculator tool"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = CalculatorBot()
    
    def tearDown(self):
        """Clean up after tests"""
        self.bot.reset_conversation()
    
    def test_greeting_handling(self):
        """Test greeting detection and response"""
        response = self.bot.process_input("Hello")
        self.assertIn("Hello", response)
        self.assertIn("calculator", response.lower())
        self.assertEqual(self.bot.get_state(), "completed")
    
    def test_goodbye_handling(self):
        """Test goodbye detection and response"""
        response = self.bot.process_input("Thanks, goodbye!")
        self.assertIn("Goodbye", response)
        self.assertEqual(self.bot.get_state(), "completed")
    
    @patch('agentic_bot.call_calculator_with_retry')
    @patch('agentic_bot.check_calculator_health')
    def test_successful_calculation_flow(self, mock_health, mock_calc):
        """Test successful calculation flow"""
        mock_health.return_value = True
        mock_calc.return_value = 8.0
        
        response = self.bot.process_input("What is 5 + 3?")
        self.assertIn("8", response)
        self.assertIn("result", response.lower())
        
        # Check memory
        summary = self.bot.get_conversation_summary()
        self.assertEqual(summary['calculations_performed'], 1)
        self.assertEqual(summary['calculation_history'][0]['result'], 8.0)
    
    @patch('agentic_bot.call_calculator_with_retry')
    @patch('agentic_bot.check_calculator_health')
    def test_calculation_error_flow(self, mock_health, mock_calc):
        """Test calculation error handling flow"""
        mock_health.return_value = True
        mock_calc.return_value = "Division by zero is not allowed"
        
        response = self.bot.process_input("10 / 0")
        self.assertIn("couldn't calculate", response.lower())
        self.assertIn("division by zero", response.lower())
        
        # Check that no calculation was recorded
        summary = self.bot.get_conversation_summary()
        self.assertEqual(summary['calculations_performed'], 0)
    
    def test_incomplete_request_handling(self):
        """Test handling of incomplete calculation requests"""
        response = self.bot.process_input("Calculate")
        self.assertIn("mathematical expression", response.lower())
        self.assertEqual(self.bot.get_state(), "waiting_for_clarification")
    
    def test_non_calculation_request(self):
        """Test handling of non-calculation requests"""
        response = self.bot.process_input("What's the weather like?")
        self.assertIn("calculator bot", response.lower())
        self.assertEqual(self.bot.get_state(), "waiting_for_clarification")
    
    def test_empty_input_handling(self):
        """Test empty input handling"""
        response = self.bot.process_input("")
        self.assertIn("didn't catch that", response.lower())
        
        response = self.bot.process_input("   ")
        self.assertIn("didn't catch that", response.lower())
    
    @patch('agentic_bot.check_calculator_health')
    def test_service_unavailable_handling(self, mock_health):
        """Test handling when calculator service is unavailable"""
        mock_health.return_value = False
        
        response = self.bot.process_input("What is 5 + 3?")
        self.assertIn("unavailable", response.lower())
        self.assertIn("server", response.lower())
    
    def test_multiple_calculations_memory(self):
        """Test memory tracking across multiple calculations"""
        with patch('agentic_bot.call_calculator_with_retry') as mock_calc, \
             patch('agentic_bot.check_calculator_health', return_value=True):
            
            # First calculation
            mock_calc.return_value = 8.0
            self.bot.process_input("5 + 3")
            
            # Second calculation
            mock_calc.return_value = 20.0
            self.bot.process_input("4 * 5")
            
            # Check memory
            summary = self.bot.get_conversation_summary()
            self.assertEqual(summary['calculations_performed'], 2)
            self.assertEqual(len(summary['calculation_history']), 2)
            
            # Test goodbye with calculation count
            response = self.bot.process_input("Goodbye")
            self.assertIn("2 calculations", response)
    
    def test_intent_extraction(self):
        """Test intent extraction accuracy"""
        extractor = self.bot.intent_extractor
        
        # Test calculation intents
        calc_inputs = [
            "What is 5 + 3?",
            "Calculate 10 * 7",
            "15 divided by 3",
            "Sum of 2 and 8",
            "2 + 3",
            "Compute 100 - 50"
        ]
        
        for input_text in calc_inputs:
            intents = extractor.extract_intents(input_text)
            self.assertIn("calc_intent", intents, f"Failed for: {input_text}")
        
        # Test greeting intents
        greeting_inputs = ["Hello", "Hi there", "Good morning", "Hey"]
        for input_text in greeting_inputs:
            intents = extractor.extract_intents(input_text)
            self.assertIn("greeting", intents, f"Failed for: {input_text}")
        
        # Test goodbye intents
        goodbye_inputs = ["Goodbye", "Thanks, bye", "That's all", "See you later"]
        for input_text in goodbye_inputs:
            intents = extractor.extract_intents(input_text)
            self.assertIn("goodbye", intents, f"Failed for: {input_text}")


class TestIntegration(unittest.TestCase):
    """Integration tests requiring actual server"""
    
    @classmethod
    def setUpClass(cls):
        """Set up for integration tests - check if server is running"""
        cls.server_available = check_calculator_health()
        if not cls.server_available:
            print("\n" + "="*50)
            print("WARNING: Integration tests skipped")
            print("To run integration tests, start the server:")
            print("python server.py")
            print("="*50)
    
    def setUp(self):
        if not self.server_available:
            self.skipTest("Calculator server not available")
    
    def test_end_to_end_calculation(self):
        """Test end-to-end calculation with real server"""
        bot = CalculatorBot()
        
        # Test basic calculation
        response = bot.process_input("What is 15 + 25?")
        self.assertIn("40", response)
        
        # Test another calculation
        response = bot.process_input("Calculate 8 * 7")
        self.assertIn("56", response)
        
        # Test invalid calculation
        response = bot.process_input("10 / 0")
        self.assertIn("couldn't calculate", response.lower())
        
        # Check final state
        summary = bot.get_conversation_summary()
        self.assertEqual(summary['calculations_performed'], 2)
    
    def test_real_calculator_tool(self):
        """Test calculator tool with real HTTP calls"""
        # Test valid calculations
        test_cases = [
            ("2 + 3", 5.0),
            ("10 * 4", 40.0),
            ("100 / 5", 20.0),
            ("15 - 7", 8.0),
            ("(2 + 3) * 4", 20.0)
        ]
        
        for expr, expected in test_cases:
            result = call_calculator(expr)
            self.assertAlmostEqual(result, expected, places=5, 
                                   msg=f"Failed for expression: {expr}")
        
        # Test error cases
        error_cases = ["10 / 0", "abc + def", "sqrt(16)"]
        for expr in error_cases:
            result = call_calculator(expr)
            self.assertIsInstance(result, str, f"Should return error string for: {expr}")


def run_tests():
    """Run all tests with proper output"""
    print("Running Calculator Tool Integration Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add unit tests
    suite.addTest(unittest.makeSuite(TestCalculatorTool))
    suite.addTest(unittest.makeSuite(TestAgenticBot))
    
    # Add integration tests (will be skipped if server not available)
    suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            error_msg = traceback.split('AssertionError: ')[-1].split('\n')[0]
            print(f"- {test}: {error_msg}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            error_msg = traceback.splitlines()[-2]
            print(f"- {test}: {error_msg}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 