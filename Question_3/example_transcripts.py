"""
Example Transcripts demonstrating Calculator Tool Integration

This file contains example transcripts showing both successful calculations
and graceful failure handling scenarios.
"""

from agentic_bot import CalculatorBot
import time


def print_transcript(title: str, interactions: list):
    """Print a formatted transcript"""
    print(f"\n{'='*20} {title} {'='*20}")
    
    bot = CalculatorBot()
    
    for i, user_input in enumerate(interactions, 1):
        print(f"\nTurn {i}:")
        print(f"User: {user_input}")
        
        response = bot.process_input(user_input)
        print(f"Bot: {response}")
        
        # Add state and calculation info for debugging
        summary = bot.get_conversation_summary()
        if summary['calculation_history']:
            last_calc = summary['calculation_history'][-1]
            print(f"     [Calculation: {last_calc['expression']} = {last_calc['result']}]")
        
        print(f"     [State: {bot.get_state()}]")
    
    # Print final summary
    summary = bot.get_conversation_summary()
    print(f"\nSummary: {summary['calculations_performed']} calculations performed")
    print(f"Calculator available: {summary['calculator_available']}")


def transcript_1_happy_path():
    """Happy path - successful calculations"""
    interactions = [
        "Hello",
        "What is 7 * 9?",
        "Calculate 15 + 25",
        "(10 - 3) * 2",
        "100 / 4",
        "Thanks, goodbye!"
    ]
    
    print_transcript("Happy Path - Successful Calculations", interactions)


def transcript_2_graceful_failures():
    """Graceful failure handling"""
    interactions = [
        "Hi there",
        "Calculate twenty plus five",  # Invalid expression
        "10 / 0",  # Division by zero
        "What is 5 + ?",  # Incomplete expression
        "2 ** 3",  # Unsupported operation
        "Goodbye"
    ]
    
    print_transcript("Graceful Failure Handling", interactions)


def transcript_3_mixed_scenarios():
    """Mixed successful and failed calculations"""
    interactions = [
        "Hello calculator",
        "What is 5 + 3?",  # Success
        "abc + def",  # Error
        "15 * 2",  # Success
        "Calculate",  # Incomplete request
        "50 / 10",  # Success after clarification
        "sqrt(16)",  # Unsupported
        "That's all, thanks!"
    ]
    
    print_transcript("Mixed Success and Failure Scenarios", interactions)


def transcript_4_timeout_network_errors():
    """Timeout and network error scenarios (simulated)"""
    print(f"\n{'='*20} Network/Timeout Error Scenarios {'='*20}")
    print("\nNote: These scenarios would occur when:")
    print("1. Calculator server is not running")
    print("2. Network connectivity issues")
    print("3. Server timeout/overload")
    print("\nExample responses:")
    
    error_scenarios = [
        {
            "user": "Compute 10 / 2",
            "bot_response": "Sorry, the calculator service is currently unavailable. Please ensure the calculator server is running on localhost:8000.",
            "scenario": "Service unavailable"
        },
        {
            "user": "What is 5 * 8?",
            "bot_response": "Calculator request timed out. Please try again.",
            "scenario": "Request timeout"
        },
        {
            "user": "15 + 30",
            "bot_response": "Cannot connect to calculator service. Please ensure the server is running on localhost:8000.",
            "scenario": "Connection error"
        }
    ]
    
    for i, scenario in enumerate(error_scenarios, 1):
        print(f"\nTurn {i} ({scenario['scenario']}):")
        print(f"User: {scenario['user']}")
        print(f"Bot: {scenario['bot_response']}")


def transcript_5_edge_cases():
    """Edge cases and unusual inputs"""
    interactions = [
        "",  # Empty input
        "   ",  # Whitespace only
        "Calculate something",  # Vague request
        "What's the weather?",  # Non-calculator query
        "2+3",  # No spaces
        "2 + 3 + 4 + 5",  # Multiple operations
        "2.5 * 1.5",  # Decimals
        "0 * 999",  # Zero multiplication
        "Bye"
    ]
    
    print_transcript("Edge Cases and Unusual Inputs", interactions)


def transcript_6_conversation_flow():
    """Natural conversation flow with calculations"""
    interactions = [
        "Hi, I need help with some math",
        "What is 25 * 4?",
        "Great! Now what about 15% of that?",  # Unsupported
        "Ok, what's 100 * 0.15?",  # Alternative approach
        "Perfect! And 100 - 15?",
        "Excellent, thank you so much!"
    ]
    
    print_transcript("Natural Conversation Flow", interactions)


def run_all_transcripts():
    """Run all example transcripts"""
    print("Calculator Tool Integration - Example Transcripts")
    print("=" * 60)
    print("These transcripts demonstrate the calculator bot's capabilities")
    print("and error handling in various scenarios.")
    
    transcript_1_happy_path()
    transcript_2_graceful_failures()
    transcript_3_mixed_scenarios()
    transcript_4_timeout_network_errors()
    transcript_5_edge_cases()
    transcript_6_conversation_flow()
    
    print(f"\n{'='*60}")
    print("Transcript Examples Complete")
    print("\nTo test with a real server:")
    print("1. Start the server: python server.py")
    print("2. Run the bot: python agentic_bot.py")
    print("3. Or run tests: python test_calculator_integration.py")


if __name__ == "__main__":
    run_all_transcripts() 