from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum, auto
import uuid
from datetime import datetime
import re

from calculator_tool import call_calculator_with_retry, check_calculator_health


class ConversationState(Enum):
    """Conversation states for the agentic bot"""
    INITIAL = "initial"
    PROCESSING = "processing"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    COMPLETED = "completed"


class Action(Enum):
    """Actions the planner can decide to take"""
    ASK_FOLLOWUP = auto()
    CALL_CALCULATOR = auto()
    CALL_RAG = auto()          # For future extension
    CALL_TEXT2SQL = auto()     # For future extension
    FINISH = auto()


@dataclass
class ConversationTurn:
    """Represents a single turn in the conversation"""
    user_input: str
    bot_response: str
    timestamp: datetime
    action_taken: str
    intents_detected: List[str]
    missing_slots: List[str]
    calculation_result: Optional[float] = None


class AgenticConversationMemory:
    """Memory management for agentic conversations"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.turns: List[ConversationTurn] = []
        self.current_state = ConversationState.INITIAL
        self.context: Dict[str, Any] = {}
        self.pending_clarification: Optional[str] = None
        self.calculation_history: List[Dict[str, Any]] = []
    
    def add_turn(self, user_input: str, bot_response: str, action_taken: str, 
                 intents_detected: List[str], missing_slots: List[str], 
                 calculation_result: Optional[float] = None):
        """Add a new conversation turn to memory"""
        turn = ConversationTurn(
            user_input=user_input,
            bot_response=bot_response,
            timestamp=datetime.now(),
            action_taken=action_taken,
            intents_detected=intents_detected,
            missing_slots=missing_slots,
            calculation_result=calculation_result
        )
        self.turns.append(turn)
        
        # Track calculations separately
        if calculation_result is not None:
            self.calculation_history.append({
                "expression": user_input,
                "result": calculation_result,
                "timestamp": turn.timestamp.isoformat()
            })
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get formatted conversation history"""
        return [
            {
                "user": turn.user_input,
                "bot": turn.bot_response,
                "action": turn.action_taken,
                "intents": turn.intents_detected,
                "missing_slots": turn.missing_slots,
                "calculation_result": turn.calculation_result,
                "timestamp": turn.timestamp.isoformat()
            }
            for turn in self.turns
        ]
    
    def update_context(self, key: str, value: Any):
        """Update conversation context"""
        self.context[key] = value
    
    def get_context(self) -> Dict[str, Any]:
        """Get current conversation context"""
        return self.context.copy()


class IntentExtractor:
    """Enhanced intent extraction for calculation and other requests"""
    
    def __init__(self):
        self.patterns = {
            "calc_intent": [
                r'\d+\s*[\+\-\*\/]\s*\d+',  # Basic math operations
                r'calculate|compute|math|add|subtract|multiply|divide',
                r'what\s+is\s+\d+.*\d+',
                r'\d+\s*[\+\-\*\/]',
                r'plus|minus|times|divided\s+by',
                r'sum\s+of|product\s+of|difference\s+of|quotient\s+of'
            ],
            "greeting": [
                r'^(hi|hello|hey|good\s+(morning|afternoon|evening))',
                r'^(what\'s\s+up|how\s+are\s+you|how\s+do\s+you\s+do)'
            ],
            "goodbye": [
                r'(bye|goodbye|see\s+you|farewell|thanks?\s*,?\s*(bye|goodbye)?)',
                r'(that\'s\s+all|i\'m\s+done|thank\s+you\s+very\s+much)'
            ]
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {
            intent: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for intent, patterns in self.patterns.items()
        }
    
    def extract_intents(self, text: str) -> List[str]:
        """Extract intents from user input text"""
        intents = []
        
        for intent, patterns in self.compiled_patterns.items():
            if any(pattern.search(text) for pattern in patterns):
                intents.append(intent)
        
        return intents
    
    def extract_missing_slots(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """Determine what information is missing for complete processing"""
        missing = []
        
        # Check for math expressions that are incomplete
        calc_patterns = self.compiled_patterns["calc_intent"]
        if any(pattern.search(text) for pattern in calc_patterns):
            # If it's just "calculate" or "compute" without an expression
            if not re.search(r'\d+\s*[\+\-\*\/]\s*\d+', text):
                if any(word in text.lower() for word in ['calculate', 'compute', 'math']):
                    missing.append("mathematical_expression")
        
        return missing


class CalculatorBot:
    """Enhanced agentic bot with HTTP calculator tool integration"""
    
    def __init__(self):
        self.memory = AgenticConversationMemory()
        self.intent_extractor = IntentExtractor()
        self.calculator_available = False
        self._check_calculator_status()
    
    def _check_calculator_status(self):
        """Check if calculator service is available"""
        self.calculator_available = check_calculator_health()
        if not self.calculator_available:
            print("Warning: Calculator service is not available. Start the server with: python server.py")
    
    def _decide_action(self, intents: List[str], missing_slots: List[str]) -> Action:
        """Decide what action to take based on intents and missing information"""
        if missing_slots:
            return Action.ASK_FOLLOWUP
        
        if "goodbye" in intents:
            return Action.FINISH
        
        if "calc_intent" in intents:
            return Action.CALL_CALCULATOR
        
        if "greeting" in intents:
            return Action.FINISH  # Simple greeting response
        
        return Action.ASK_FOLLOWUP  # Default to asking for clarification
    
    def _execute_action(self, action: Action, user_input: str, intents: List[str]) -> Dict[str, Any]:
        """Execute the chosen action"""
        if action == Action.ASK_FOLLOWUP:
            if "mathematical_expression" in self.intent_extractor.extract_missing_slots(user_input):
                return {
                    "response": "I can help you with calculations! Please provide a mathematical expression, like '2 + 3' or '10 * 5'.",
                    "calculation_result": None
                }
            else:
                return {
                    "response": "I'm a calculator bot. Ask me to calculate mathematical expressions like '15 + 25' or 'What is 10 * 8?'",
                    "calculation_result": None
                }
        
        elif action == Action.CALL_CALCULATOR:
            if not self.calculator_available:
                self._check_calculator_status()  # Re-check status
                
            if not self.calculator_available:
                return {
                    "response": "Sorry, the calculator service is currently unavailable. Please ensure the calculator server is running on localhost:8000.",
                    "calculation_result": None
                }
            
            # Call the HTTP calculator service
            result = call_calculator_with_retry(user_input)
            
            if isinstance(result, (int, float)):
                return {
                    "response": f"The result is: {result}",
                    "calculation_result": result
                }
            else:
                # result is an error message string
                return {
                    "response": f"Sorry, I couldn't calculate that: {result}",
                    "calculation_result": None
                }
        
        elif action == Action.FINISH:
            if "greeting" in intents:
                return {
                    "response": "Hello! I'm a calculator bot. I can help you with mathematical calculations. Try asking me something like 'What is 5 + 3?'",
                    "calculation_result": None
                }
            else:  # goodbye
                calc_count = len(self.memory.calculation_history)
                if calc_count > 0:
                    return {
                        "response": f"Goodbye! I helped you with {calc_count} calculation{'s' if calc_count != 1 else ''} today. Have a great day!",
                        "calculation_result": None
                    }
                else:
                    return {
                        "response": "Goodbye! Feel free to come back anytime for calculations.",
                        "calculation_result": None
                    }
        
        return {
            "response": "I'm not sure how to handle that request. Try asking me to calculate something!",
            "calculation_result": None
        }
    
    def process_input(self, user_input: str) -> str:
        """Main entry point - process user input and return response"""
        if not user_input or not user_input.strip():
            return "I didn't catch that—could you re-type your question?"
        
        user_input = user_input.strip()
        
        # Update state
        if self.memory.current_state == ConversationState.WAITING_FOR_CLARIFICATION:
            self.memory.current_state = ConversationState.PROCESSING
        elif self.memory.current_state == ConversationState.INITIAL:
            self.memory.current_state = ConversationState.PROCESSING
        
        # Extract intents and missing slots
        intents = self.intent_extractor.extract_intents(user_input)
        missing_slots = self.intent_extractor.extract_missing_slots(user_input)
        
        # Decide action and execute
        action = self._decide_action(intents, missing_slots)
        result = self._execute_action(action, user_input, intents)
        
        # Update state based on action
        if action == Action.ASK_FOLLOWUP:
            self.memory.current_state = ConversationState.WAITING_FOR_CLARIFICATION
        elif action == Action.FINISH:
            self.memory.current_state = ConversationState.COMPLETED
        else:
            self.memory.current_state = ConversationState.PROCESSING
        
        # Store the conversation turn
        self.memory.add_turn(
            user_input=user_input,
            bot_response=result["response"],
            action_taken=action.name,
            intents_detected=intents,
            missing_slots=missing_slots,
            calculation_result=result["calculation_result"]
        )
        
        return result["response"]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get detailed conversation summary"""
        return {
            "session_id": self.memory.session_id,
            "current_state": self.memory.current_state.value,
            "total_turns": len(self.memory.turns),
            "calculations_performed": len(self.memory.calculation_history),
            "calculator_available": self.calculator_available,
            "calculation_history": self.memory.calculation_history,
            "context": self.memory.get_context(),
            # expose raw turns list for deep inspection in unhappy-flow tests
            "turns": [
                {
                    "user_input": t.user_input,
                    "bot_response": t.bot_response,
                    "action_taken": t.action_taken,
                    "timestamp": t.timestamp.isoformat()
                } for t in self.memory.turns
            ],
            "conversation_history": self.memory.get_conversation_history()
        }
    
    def reset_conversation(self):
        """Reset the conversation to start fresh"""
        self.memory = AgenticConversationMemory()
        self._check_calculator_status()
    
    def get_state(self) -> str:
        """Get current conversation state"""
        return self.memory.current_state.value
    
    def is_conversation_complete(self) -> bool:
        """Check if conversation is in completed state"""
        return self.memory.current_state == ConversationState.COMPLETED


# Demo function
def demo_calculator_bot():
    """Demonstrate the calculator bot with various types of queries"""
    bot = CalculatorBot()
    
    test_inputs = [
        "Hello",
        "What is 5 + 3?",
        "Calculate 10 * 7",
        "15 / 3",
        "(2 + 3) * 4",
        "Calculate",  # Incomplete
        "100 / 0",  # Division by zero
        "abc + def",  # Invalid expression
        "What is the square root of 16?",  # Unsupported operation
        "Thanks, goodbye!"
    ]
    
    print("=== Calculator Bot Demo ===\n")
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"Turn {i}:")
        print(f"User: {user_input}")
        response = bot.process_input(user_input)
        print(f"Bot: {response}")
        print(f"State: {bot.get_state()}")
        print()
    
    print("=== Conversation Summary ===")
    summary = bot.get_conversation_summary()
    print(f"Total turns: {summary['total_turns']}")
    print(f"Calculations performed: {summary['calculations_performed']}")
    print(f"Calculator available: {summary['calculator_available']}")
    
    if summary['calculation_history']:
        print("\nCalculation History:")
        for calc in summary['calculation_history']:
            print(f"  {calc['expression']} = {calc['result']}")


if __name__ == "__main__":
    demo_calculator_bot() 