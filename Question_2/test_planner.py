import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, List

from planner import (
    Action, decide_action, execute, calc_api, rag_endpoint, text2sql_endpoint,
    IntentExtractor, plan_and_execute
)


class TestPlannerActions(unittest.TestCase):
    """test the Action enum and decide_action function"""
    
    def test_action_enum_values(self):
        """test that all required actions exist"""
        self.assertTrue(hasattr(Action, 'ASK_FOLLOWUP'))
        self.assertTrue(hasattr(Action, 'CALL_CALCULATOR'))
        self.assertTrue(hasattr(Action, 'CALL_RAG'))
        self.assertTrue(hasattr(Action, 'CALL_TEXT2SQL'))
        self.assertTrue(hasattr(Action, 'FINISH'))
    
    def test_decide_action_with_missing_slots(self):
        """test that missing slots always trigger ASK_FOLLOWUP"""
        result = decide_action("active", ["calc_intent"], ["missing_number"])
        self.assertEqual(result, Action.ASK_FOLLOWUP)
        
        result = decide_action("active", ["product_query"], ["specific_product"])
        self.assertEqual(result, Action.ASK_FOLLOWUP)
    
    def test_decide_action_calc_intent(self):
        """test calculator action selection"""
        result = decide_action("active", ["calc_intent"], [])
        self.assertEqual(result, Action.CALL_CALCULATOR)
    
    def test_decide_action_product_query(self):
        """test RAG action selection"""
        result = decide_action("active", ["product_query"], [])
        self.assertEqual(result, Action.CALL_RAG)
    
    def test_decide_action_outlet_query(self):
        """test Text2SQL action selection"""
        result = decide_action("active", ["outlet_query"], [])
        self.assertEqual(result, Action.CALL_TEXT2SQL)
    
    def test_decide_action_default_finish(self):
        """test default FINISH action"""
        result = decide_action("active", [], [])
        self.assertEqual(result, Action.FINISH)
        
        result = decide_action("active", ["unknown_intent"], [])
        self.assertEqual(result, Action.FINISH)
    
    def test_decide_action_priority(self):
        """test that missing slots take priority over intents"""
        result = decide_action("active", ["calc_intent", "product_query"], ["missing_info"])
        self.assertEqual(result, Action.ASK_FOLLOWUP)


class TestCalculatorAPI(unittest.TestCase):
    """test the calculator API functionality"""
    
    def test_basic_math_operations(self):
        """test basic arithmetic operations"""
        self.assertEqual(calc_api("5 + 3"), 8)
        self.assertEqual(calc_api("10 - 4"), 6)
        self.assertEqual(calc_api("6 * 7"), 42)
        self.assertEqual(calc_api("15 / 3"), 5)
    
    def test_complex_expressions(self):
        """test more complex mathematical expressions"""
        self.assertEqual(calc_api("(5 + 3) * 2"), 16)
        self.assertEqual(calc_api("10 + 5 * 2"), 20)
        self.assertEqual(calc_api("(20 - 5) / 3"), 5)
    
    def test_invalid_characters(self):
        """test security - invalid characters should raise error"""
        with self.assertRaises(ValueError):
            calc_api("import os")
        
        with self.assertRaises(ValueError):
            calc_api("__import__('os')")
        
        with self.assertRaises(ValueError):
            calc_api("__import__('os')")
    
    def test_invalid_expressions(self):
        """test handling of invalid mathematical expressions"""
        with self.assertRaises(ValueError):
            calc_api("hello world")
        
        with self.assertRaises(ValueError):
            calc_api("")
        
        # Division by zero should raise an error during eval
        with self.assertRaises(ValueError):
            calc_api("5 / 0")


class TestRAGEndpoint(unittest.TestCase):
    """test the RAG endpoint for drinkware queries"""
    
    def test_specific_product_queries(self):
        """test queries for specific products"""
        result = rag_endpoint("Tell me about mugs")
        self.assertIn("mug", result["reply"].lower())
        self.assertIn("ceramic", result["reply"])
        
        result = rag_endpoint("I need a bottle")
        self.assertIn("bottle", result["reply"].lower())
        self.assertIn("Water bottles", result["reply"])
    
    def test_product_variations(self):
        """test different product name variations"""
        products = ["mug", "cup", "bottle", "tumbler", "glass", "flask"]
        
        for product in products:
            result = rag_endpoint(f"What {product}s do you have?")
            self.assertIn("reply", result)
            self.assertIn(product, result["reply"].lower())
    
    def test_unknown_product_query(self):
        """test handling of unknown product queries"""
        result = rag_endpoint("Do you have spoons?")
        self.assertIn("couldn't find", result["reply"])
        self.assertIn("mugs, cups, bottles", result["reply"])
    
    def test_empty_query(self):
        """test handling of empty or vague queries"""
        result = rag_endpoint("")
        self.assertIn("couldn't find", result["reply"])
        
        result = rag_endpoint("products")
        self.assertIn("mugs, cups, bottles", result["reply"])


class TestText2SQLEndpoint(unittest.TestCase):
    """test the Text2SQL endpoint for outlet queries"""
    
    def test_hours_queries(self):
        """test queries about opening hours"""
        result = text2sql_endpoint("What time does SS 2 open?")
        self.assertIn("SS 2", result["reply"])
        self.assertIn("9 AM - 10 PM", result["reply"])
        
        result = text2sql_endpoint("KLCC hours")
        self.assertIn("KLCC", result["reply"])
        self.assertIn("10 AM - 10 PM", result["reply"])
    
    def test_phone_queries(self):
        """test queries about phone numbers"""
        result = text2sql_endpoint("PJ Central phone number")
        self.assertIn("PJ Central", result["reply"])
        self.assertIn("03-7955-1234", result["reply"])
        
        result = text2sql_endpoint("Contact info for SS 2")
        self.assertIn("SS 2", result["reply"])
        self.assertIn("03-7876-5432", result["reply"])
    
    def test_city_queries(self):
        """test queries about outlets in specific cities"""
        result = text2sql_endpoint("Outlets in Petaling Jaya")
        self.assertIn("Petaling Jaya", result["reply"])
        self.assertIn("SS 2", result["reply"])
        self.assertIn("PJ Central", result["reply"])
        
        result = text2sql_endpoint("KL outlets")
        self.assertIn("Kuala Lumpur", result["reply"])
        self.assertIn("KLCC", result["reply"])
    
    def test_vague_outlet_queries(self):
        """test handling of vague outlet queries"""
        result = text2sql_endpoint("Tell me about stores")
        self.assertIn("outlets at:", result["reply"])
        self.assertIn("SS 2 (Petaling Jaya)", result["reply"])
        self.assertIn("KLCC (Kuala Lumpur)", result["reply"])
    
    def test_missing_location_queries(self):
        """test queries missing specific location"""
        result = text2sql_endpoint("What are the hours?")
        self.assertIn("specify which outlet", result["reply"])
        
        result = text2sql_endpoint("Phone number please")
        self.assertIn("specify which outlet", result["reply"])


class TestExecuteFunction(unittest.TestCase):
    """test the main execute function that routes to different actions"""
    
    def test_execute_ask_followup(self):
        """test ASK_FOLLOWUP execution"""
        result = execute(Action.ASK_FOLLOWUP, question="What do you need?")
        self.assertEqual(result["reply"], "What do you need?")
        
        result = execute(Action.ASK_FOLLOWUP)
        self.assertEqual(result["reply"], "Could you provide more information?")
    
    def test_execute_calculator(self):
        """test CALL_CALCULATOR execution"""
        result = execute(Action.CALL_CALCULATOR, expr="5 + 3")
        self.assertIn("8", result["reply"])
        
        # Test error handling
        result = execute(Action.CALL_CALCULATOR, expr="invalid")
        self.assertIn("couldn't calculate", result["reply"])
    
    def test_execute_rag(self):
        """test CALL_RAG execution"""
        result = execute(Action.CALL_RAG, query="mug information")
        self.assertIn("mug", result["reply"].lower())
    
    def test_execute_text2sql(self):
        """test CALL_TEXT2SQL execution"""
        result = execute(Action.CALL_TEXT2SQL, query="SS 2 hours")
        self.assertIn("SS 2", result["reply"])
    
    def test_execute_finish(self):
        """test FINISH execution"""
        result = execute(Action.FINISH)
        self.assertEqual(result["reply"], "Glad I could help!")
    
    def test_execute_unknown_action(self):
        """test handling of unknown actions"""
        # Create a mock action that's not in the enum
        mock_action = MagicMock()
        mock_action.name = "UNKNOWN_ACTION"
        
        result = execute(mock_action)
        self.assertIn("not sure how to handle", result["reply"])


class TestIntentExtractor(unittest.TestCase):
    """test the IntentExtractor class functionality"""
    
    def setUp(self):
        self.extractor = IntentExtractor()
    
    def test_calc_intent_detection(self):
        """test calculation intent detection"""
        test_cases = [
            "What is 5 + 3?",
            "Calculate 10 * 2",
            "Can you compute 15 - 7?",
            "5 + 3 equals what?",
            "Math problem: 20 / 4"
        ]
        
        for test_case in test_cases:
            intents = self.extractor.extract_intents(test_case)
            self.assertIn("calc_intent", intents, f"Failed for: {test_case}")
    
    def test_product_query_detection(self):
        """test product query intent detection"""
        test_cases = [
            "Show me your mugs",
            "What bottles do you have?",
            "I'm looking for a tumbler",
            "Need a flask for hiking",
            "What products are available?"
        ]
        
        for test_case in test_cases:
            intents = self.extractor.extract_intents(test_case)
            self.assertIn("product_query", intents, f"Failed for: {test_case}")
    
    def test_outlet_query_detection(self):
        """test outlet query intent detection"""
        test_cases = [
            "Where is your SS 2 outlet?",
            "KLCC store hours",
            "Phone number for PJ Central",
            "Outlets in Kuala Lumpur",
            "Store locations"
        ]
        
        for test_case in test_cases:
            intents = self.extractor.extract_intents(test_case)
            self.assertIn("outlet_query", intents, f"Failed for: {test_case}")
    
    def test_multiple_intent_detection(self):
        """test detection of multiple intents in one query"""
        query = "Calculate 5 + 3 and show me mugs in SS 2 store"
        intents = self.extractor.extract_intents(query)
        
        self.assertIn("calc_intent", intents)
        self.assertIn("product_query", intents)
        self.assertIn("outlet_query", intents)
    
    def test_missing_slots_detection(self):
        """test missing slot detection"""
        # Incomplete math expression
        missing = self.extractor.extract_missing_slots("Calculate something")
        self.assertIn("complete_expression", missing)
        
        # Vague product query
        missing = self.extractor.extract_missing_slots("Show products")
        self.assertIn("specific_product", missing)
        
        # Outlet query without location or specific question
        missing = self.extractor.extract_missing_slots("Store info")
        self.assertIn("location_or_specific_query", missing)
    
    def test_complete_queries_no_missing_slots(self):
        """test that complete queries don't have missing slots"""
        complete_queries = [
            "What is 5 + 3?",
            "Show me your mugs",
            "SS 2 store hours"
        ]
        
        for query in complete_queries:
            missing = self.extractor.extract_missing_slots(query)
            # These should not have the specific missing slots for their intent
            if "calc_intent" in self.extractor.extract_intents(query):
                self.assertNotIn("complete_expression", missing)
            if "product_query" in self.extractor.extract_intents(query):
                self.assertNotIn("specific_product", missing)
            if "outlet_query" in self.extractor.extract_intents(query):
                self.assertNotIn("location_or_specific_query", missing)


class TestPlanAndExecute(unittest.TestCase):
    """test the main plan_and_execute function integration"""
    
    def test_calculator_workflow(self):
        """test complete calculator workflow"""
        result = plan_and_execute("What is 10 + 5?")
        
        self.assertEqual(result["action_taken"], "CALL_CALCULATOR")
        self.assertIn("calc_intent", result["intents_detected"])
        self.assertIn("15", result["response"])
    
    def test_product_query_workflow(self):
        """test complete product query workflow"""
        result = plan_and_execute("Tell me about your mugs")
        
        self.assertEqual(result["action_taken"], "CALL_RAG")
        self.assertIn("product_query", result["intents_detected"])
        self.assertIn("mug", result["response"].lower())
    
    def test_outlet_query_workflow(self):
        """test complete outlet query workflow"""
        result = plan_and_execute("What are the hours for SS 2?")
        
        self.assertEqual(result["action_taken"], "CALL_TEXT2SQL")
        self.assertIn("outlet_query", result["intents_detected"])
        self.assertIn("SS 2", result["response"])
        self.assertIn("9 AM - 10 PM", result["response"])
    
    def test_incomplete_query_workflow(self):
        """test workflow for incomplete queries"""
        result = plan_and_execute("Calculate")
        
        self.assertEqual(result["action_taken"], "ASK_FOLLOWUP")
        self.assertIn("calc_intent", result["intents_detected"])
        self.assertIn("complete_expression", result["missing_slots"])
        self.assertIn("mathematical expression", result["response"])
    
    def test_vague_product_query_workflow(self):
        """test workflow for vague product queries"""
        result = plan_and_execute("What products?")
        
        self.assertEqual(result["action_taken"], "ASK_FOLLOWUP")
        self.assertIn("product_query", result["intents_detected"])
        self.assertIn("specific_product", result["missing_slots"])
        self.assertIn("specific drinkware", result["response"])
    
    def test_finish_workflow(self):
        """test workflow that leads to FINISH"""
        result = plan_and_execute("Thanks, goodbye!")
        
        self.assertEqual(result["action_taken"], "FINISH")
        self.assertEqual(result["response"], "Glad I could help!")
    
    def test_context_handling(self):
        """test that context is properly handled"""
        context = {"state": "active", "previous_intent": "calc_intent"}
        result = plan_and_execute("What is 5 + 3?", context)
        
        self.assertEqual(result["action_taken"], "CALL_CALCULATOR")
        self.assertIn("8", result["response"])


# Integration test for the complete system
class TestPlannerIntegration(unittest.TestCase):
    """test complete integration of planner components"""
    
    def test_decision_flow_sequence(self):
        """test a sequence of decisions flowing correctly"""
        # Start with incomplete query
        result1 = plan_and_execute("I need help with math")
        self.assertEqual(result1["action_taken"], "ASK_FOLLOWUP")
        
        # Follow up with complete query
        result2 = plan_and_execute("What is 25 * 4?")
        self.assertEqual(result2["action_taken"], "CALL_CALCULATOR")
        self.assertIn("100", result2["response"])
    
    def test_error_handling_throughout_pipeline(self):
        """test error handling at different stages"""
        # Invalid calculation - should ask for followup since no valid math found
        result = plan_and_execute("Calculate abc + def")
        self.assertEqual(result["action_taken"], "ASK_FOLLOWUP")
        self.assertIn("mathematical expression", result["response"])
        
        # Unknown product - should still trigger RAG action
        result = plan_and_execute("Show me drinkware spoons")
        self.assertEqual(result["action_taken"], "CALL_RAG")
        self.assertIn("couldn't find", result["response"])


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2) 