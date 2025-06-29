import unittest
import json
import os
from sequential_conversation import (
    SequentialConversationBot, 
    ConversationState, 
    EntityExtractor
)
from data import OutletInfo


class TestSequentialConversation(unittest.TestCase):
    """
    test cases for the sequential conversation system
    """
    
    def setUp(self):
        """
        set up test fixtures before each test method
        """
        self.bot = SequentialConversationBot()
    
    def tearDown(self):
        """
        clean up after each test method
        """
        # clean up any exported files
        for file in os.listdir('.'):
            if file.startswith('conversation_') and file.endswith('.json'):
                try:
                    os.remove(file)
                except:
                    pass


class TestHappyPath(TestSequentialConversation):
    """
    test cases for successful conversation flows
    """
    
    def test_complete_outlet_inquiry_flow(self):
        """
        test the complete happy path: location inquiry -> outlet selection -> info request
        """
        
        # turn 1: initial outlet inquiry with location
        response1 = self.bot.process_input("Is there an outlet in Petaling Jaya?")
        self.assertIn("Yes! We have outlets in Petaling Jaya", response1)
        self.assertIn("Which outlet are you referring to", response1)
        self.assertEqual(self.bot.memory.current_state, ConversationState.OUTLET_SELECTION)
        self.assertEqual(self.bot.memory.get_context("inquiry_location"), "petaling_jaya")
        
        # turn 2: outlet selection
        response2 = self.bot.process_input("SS 2, what's the opening time?")
        self.assertIn("SS 2", response2)
        self.assertIn("9:00 AM", response2)
        self.assertEqual(self.bot.memory.current_state, ConversationState.INFORMATION_REQUEST)
        
        # turn 3: end conversation
        response3 = self.bot.process_input("Thanks!")
        self.assertEqual(self.bot.memory.current_state, ConversationState.COMPLETED)
        
        # verify conversation memory
        self.assertEqual(len(self.bot.memory.turns), 3)
        self.assertIsNotNone(self.bot.memory.get_context("selected_outlet"))
    
    def test_kuala_lumpur_outlet_inquiry(self):
        """
        test inquiry for kuala lumpur outlets
        """
        
        response1 = self.bot.process_input("Do you have any outlets in Kuala Lumpur?")
        self.assertIn("Kuala Lumpur", response1)
        self.assertIn("KLCC Outlet", response1)
        self.assertEqual(self.bot.memory.current_state, ConversationState.INFORMATION_REQUEST)
        
        response2 = self.bot.process_input("What are the opening hours?")
        self.assertIn("KLCC Outlet", response2)
        self.assertIn("10:00 AM", response2)
        self.assertEqual(self.bot.memory.current_state, ConversationState.INFORMATION_REQUEST)
    
    def test_step_by_step_inquiry(self):
        """
        test step-by-step inquiry without initial location
        """
        
        # turn 1: general outlet inquiry
        response1 = self.bot.process_input("Do you have any outlets?")
        self.assertIn("several locations", response1)
        self.assertEqual(self.bot.memory.current_state, ConversationState.LOCATION_INQUIRY)
        
        # turn 2: specify location
        response2 = self.bot.process_input("Petaling Jaya")
        self.assertIn("Petaling Jaya", response2)
        self.assertIn("Which outlet", response2)
        self.assertEqual(self.bot.memory.current_state, ConversationState.OUTLET_SELECTION)
        
        # turn 3: select outlet and ask for info
        response3 = self.bot.process_input("PJ Central, what's the phone number?")
        self.assertIn("PJ Central", response3)
        self.assertIn("+603-2345-6789", response3)
        self.assertEqual(self.bot.memory.current_state, ConversationState.INFORMATION_REQUEST)
    
    def test_address_inquiry(self):
        """
        test asking for outlet address
        """
        
        response1 = self.bot.process_input("Where is your outlet in Petaling Jaya?")
        response2 = self.bot.process_input("SS 2, where exactly is it located?")
        
        self.assertIn("address", response2.lower())
        self.assertIn("SS 2/4", response2)
    
    def test_phone_inquiry(self):
        """
        test asking for outlet phone number
        """
        
        response1 = self.bot.process_input("Is there an outlet in Petaling Jaya?")
        response2 = self.bot.process_input("SS 2, what's the contact number?")
        
        self.assertIn("+603-1234-5678", response2)
    
    def test_direct_outlet_query(self):
        """
        test direct outlet name queries without location setup
        """
        
        # test direct SS2 query
        response1 = self.bot.process_input("SS 2 opening hours?")
        self.assertIn("SS 2", response1)
        self.assertIn("9:00 AM", response1)
        self.assertEqual(self.bot.memory.current_state, ConversationState.INFORMATION_REQUEST)
        self.assertEqual(self.bot.memory.get_context("inquiry_location"), "petaling_jaya")
        
        # test follow-up question
        response2 = self.bot.process_input("What's the phone number?")
        self.assertIn("+603-1234-5678", response2)
        self.assertEqual(self.bot.memory.current_state, ConversationState.INFORMATION_REQUEST)
        
        # test conversation ending
        response3 = self.bot.process_input("Thank you!")
        self.assertEqual(self.bot.memory.current_state, ConversationState.COMPLETED)


class TestInterruptedPaths(TestSequentialConversation):
    """
    test cases for interrupted or unusual conversation flows
    """
    
    def test_conversation_reset_mid_flow(self):
        """
        test resetting conversation in the middle of a flow
        """
        
        # start a conversation
        self.bot.process_input("Is there an outlet in Petaling Jaya?")
        self.assertEqual(self.bot.memory.current_state, ConversationState.OUTLET_SELECTION)
        
        # reset conversation
        self.bot.reset_conversation()
        self.assertEqual(self.bot.memory.current_state, ConversationState.INITIAL)
        self.assertEqual(len(self.bot.memory.turns), 0)
        self.assertEqual(len(self.bot.memory.context_variables), 0)
        
        # start new conversation
        response = self.bot.process_input("Hello")
        self.assertIn("help", response.lower())
    
    def test_invalid_location_inquiry(self):
        """
        test inquiry for non-existent location
        """
        
        response = self.bot.process_input("Do you have outlets in Johor Bahru?")
        self.assertIn("don't have any outlets", response)
        self.assertIn("Johor Bahru", response)
    
    def test_ambiguous_outlet_selection(self):
        """
        test handling of ambiguous outlet selection
        """
        
        self.bot.process_input("Is there an outlet in Petaling Jaya?")
        response = self.bot.process_input("The one near the mall")
        
        self.assertIn("don't have that outlet", response)
        self.assertIn("Our Petaling Jaya outlets are", response)
    
    def test_context_loss_recovery(self):
        """
        test recovery when context is lost or unclear
        """
        
        # start conversation but skip to information request without proper setup
        self.bot.memory.set_state(ConversationState.INFORMATION_REQUEST)
        response = self.bot.process_input("What time do you open?")
        
        self.assertIn("need to know which outlet", response)
    
    def test_unexpected_input_in_different_states(self):
        """
        test handling of unexpected input in various conversation states
        """
        
        # test unexpected input in initial state
        response1 = self.bot.process_input("What's the weather like?")
        self.assertIn("help", response1.lower())
        
        # test unexpected input in outlet selection state
        self.bot.process_input("Is there an outlet in Petaling Jaya?")
        response2 = self.bot.process_input("I like pizza")
        self.assertIn("don't have that outlet", response2)
    
    def test_empty_or_invalid_input(self):
        """
        test handling of empty or invalid input
        """
        
        # test empty input
        response1 = self.bot.process_input("")
        self.assertIn("didn't catch that", response1.lower())
        
        # test whitespace only
        response2 = self.bot.process_input("   ")
        self.assertIn("didn't catch that", response2.lower())
    
    def test_state_transition_edge_cases(self):
        """
        test edge cases in state transitions
        """
        
        # test direct jump to completed state
        self.bot.memory.set_state(ConversationState.COMPLETED)
        response = self.bot.process_input("Hello")
        self.assertIn("help", response)
        
        # test invalid state handling
        response = self.bot._generate_response("test", {"intents": [], "locations": []})
        self.assertIn("help", response)


class TestEntityExtraction(TestSequentialConversation):
    """
    test cases for entity extraction functionality
    """
    
    def test_location_extraction(self):
        """
        test extraction of location entities
        """
        
        extractor = EntityExtractor()
        
        # test petaling jaya variations
        entities1 = extractor.extract("Is there an outlet in Petaling Jaya?")
        self.assertIn("petaling_jaya", entities1["locations"])
        
        entities2 = extractor.extract("Do you have stores in PJ?")
        self.assertIn("petaling_jaya", entities2["locations"])
        
        entities3 = extractor.extract("SS 2 outlet please")
        self.assertIn("petaling_jaya", entities3["locations"])
        self.assertIn("ss2", entities3["locations"])
        
        # test kuala lumpur variations
        entities4 = extractor.extract("Any outlets in Kuala Lumpur?")
        self.assertIn("kuala_lumpur", entities4["locations"])
        
        entities5 = extractor.extract("KLCC branch")
        self.assertIn("kuala_lumpur", entities5["locations"])
        self.assertIn("klcc", entities5["locations"])
    
    def test_intent_extraction(self):
        """
        test extraction of intent entities
        """
        
        extractor = EntityExtractor()
        
        # test outlet inquiry intent
        entities1 = extractor.extract("Is there an outlet nearby?")
        self.assertIn("outlet_inquiry", entities1["intents"])
        
        entities2 = extractor.extract("Do you have any stores?")
        self.assertIn("outlet_inquiry", entities2["intents"])
        
        # test opening time intent
        entities3 = extractor.extract("What time do you open?")
        self.assertIn("opening_time", entities3["intents"])
        
        entities4 = extractor.extract("What are your opening hours?")
        self.assertIn("opening_time", entities4["intents"])
        
        # test location intent
        entities5 = extractor.extract("Where is your store located?")
        self.assertIn("location", entities5["intents"])
        
        # test phone intent
        entities6 = extractor.extract("What's your phone number?")
        self.assertIn("phone", entities6["intents"])


class TestConversationMemory(TestSequentialConversation):
    """
    test cases for conversation memory functionality
    """
    
    def test_turn_tracking(self):
        """
        test proper tracking of conversation turns
        """
        
        self.bot.process_input("Hello")
        self.bot.process_input("Is there an outlet in PJ?")
        self.bot.process_input("SS 2 please")
        
        self.assertEqual(len(self.bot.memory.turns), 3)
        
        # check turn details
        first_turn = self.bot.memory.turns[0]
        self.assertEqual(first_turn.turn_id, 1)
        self.assertEqual(first_turn.user_input, "Hello")
        self.assertIsNotNone(first_turn.timestamp)
    
    def test_context_management(self):
        """
        test context variable management
        """
        
        # test setting and getting context
        self.bot.memory.update_context("test_key", "test_value")
        self.assertEqual(self.bot.memory.get_context("test_key"), "test_value")
        
        # test default value
        self.assertEqual(self.bot.memory.get_context("nonexistent", "default"), "default")
        
        # test context persistence across turns
        self.bot.process_input("Is there an outlet in Petaling Jaya?")
        location = self.bot.memory.get_context("inquiry_location")
        self.assertEqual(location, "petaling_jaya")
    
    def test_conversation_export(self):
        """
        test conversation export functionality
        """
        
        # conduct a short conversation
        self.bot.process_input("Hello")
        self.bot.process_input("Is there an outlet in PJ?")
        
        # export conversation
        filename = self.bot.export_conversation("test_export.json")
        self.assertTrue(os.path.exists(filename))
        
        # verify export content
        with open(filename, 'r') as f:
            exported_data = json.load(f)
        
        self.assertIn("session_id", exported_data)
        self.assertIn("turns", exported_data)
        self.assertEqual(len(exported_data["turns"]), 2)
        
        # clean up
        os.remove(filename)
    
    def test_conversation_summary(self):
        """
        test conversation summary generation
        """
        
        self.bot.process_input("Hello")
        self.bot.process_input("Is there an outlet in PJ?")
        
        summary = self.bot.get_conversation_summary()
        
        self.assertIn("session_id", summary)
        self.assertIn("total_turns", summary)
        self.assertIn("current_state", summary)
        self.assertIn("context_variables", summary)
        
        self.assertEqual(summary["total_turns"], 2)


class TestIntegration(TestSequentialConversation):
    """
    integration tests for the complete system
    """
    
    def test_multiple_conversation_sessions(self):
        """
        test handling of multiple conversation sessions
        """
        
        # first session
        bot1 = SequentialConversationBot()
        bot1.process_input("Is there an outlet in PJ?")
        session1_id = bot1.memory.session_id
        
        # second session
        bot2 = SequentialConversationBot()
        bot2.process_input("Is there an outlet in KL?")
        session2_id = bot2.memory.session_id
        
        # verify sessions are independent
        self.assertNotEqual(session1_id, session2_id)
        self.assertEqual(bot1.memory.get_context("inquiry_location"), "petaling_jaya")
        self.assertEqual(bot2.memory.get_context("inquiry_location"), "kuala_lumpur")
    
    def test_complex_conversation_flow(self):
        """
        test a complex conversation with multiple back-and-forth exchanges
        """
        
        responses = []
        
        # complex conversation flow
        inputs = [
            "Hi there",
            "Do you have any stores?",
            "Petaling Jaya",
            "Actually, what about Kuala Lumpur?",
            "KLCC, what's the address?",
            "Thank you"
        ]
        
        for user_input in inputs:
            response = self.bot.process_input(user_input)
            responses.append(response)
        
        # verify the conversation progressed appropriately
        self.assertEqual(len(self.bot.memory.turns), 6)
        self.assertIn("KLCC", responses[-2])


def run_tests():
    """
    run all tests and generate a report
    """
    
    # create test suite
    test_suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    
    # run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # generate summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            newline = '\n'
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split(newline)[0]}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            newline = '\n'
            print(f"- {test}: {traceback.split(newline)[-2]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1) 