from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum, auto
import uuid
from datetime import datetime

from planner import Action, decide_action, execute, IntentExtractor, plan_and_execute


class ConversationState(Enum):
    """conversation states for the agentic bot"""
    INITIAL = "initial"
    PROCESSING = "processing"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"
    COMPLETED = "completed"


@dataclass
class ConversationTurn:
    """represents a single turn in the conversation"""
    user_input: str
    bot_response: str
    timestamp: datetime
    action_taken: str
    intents_detected: List[str]
    missing_slots: List[str]


class AgenticConversationMemory:
    """memory management for agentic conversations"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.turns: List[ConversationTurn] = []
        self.current_state = ConversationState.INITIAL
        self.context: Dict[str, Any] = {}
        self.pending_clarification: Optional[str] = None
    
    def add_turn(self, user_input: str, bot_response: str, action_taken: str, 
                 intents_detected: List[str], missing_slots: List[str]):
        """add a new conversation turn to memory"""
        turn = ConversationTurn(
            user_input=user_input,
            bot_response=bot_response,
            timestamp=datetime.now(),
            action_taken=action_taken,
            intents_detected=intents_detected,
            missing_slots=missing_slots
        )
        self.turns.append(turn)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """get formatted conversation history"""
        return [
            {
                "user": turn.user_input,
                "bot": turn.bot_response,
                "action": turn.action_taken,
                "intents": turn.intents_detected,
                "missing_slots": turn.missing_slots,
                "timestamp": turn.timestamp.isoformat()
            }
            for turn in self.turns
        ]
    
    def update_context(self, key: str, value: Any):
        """update conversation context"""
        self.context[key] = value
    
    def get_context(self) -> Dict[str, Any]:
        """get current conversation context"""
        return self.context.copy()


class AgenticConversationBot:
    """agentic conversation bot with planning and decision making"""
    
    def __init__(self):
        self.memory = AgenticConversationMemory()
        self.intent_extractor = IntentExtractor()
    
    def process_input(self, user_input: str) -> str:
        """main entry point - process user input through planner/controller loop"""
        if not user_input or not user_input.strip():
            return "I didn't catch that—could you re-type your question?"
        
        user_input = user_input.strip()
        
        # Update state based on current situation
        if self.memory.current_state == ConversationState.WAITING_FOR_CLARIFICATION:
            self.memory.current_state = ConversationState.PROCESSING
        elif self.memory.current_state == ConversationState.INITIAL:
            self.memory.current_state = ConversationState.PROCESSING
        
        # Use the planner/controller loop with current state
        ctx = self.memory.get_context()
        ctx["state"] = self.get_state()
        result = plan_and_execute(user_input, ctx)
        
        # Update state based on action taken
        action_taken = result["action_taken"]
        if action_taken == "ASK_FOLLOWUP":
            self.memory.current_state = ConversationState.WAITING_FOR_CLARIFICATION
            self.memory.pending_clarification = result["response"]
        elif action_taken == "FINISH":
            self.memory.current_state = ConversationState.COMPLETED
        else:
            self.memory.current_state = ConversationState.PROCESSING
        
        # Update context with relevant information
        if result["intents_detected"]:
            self.memory.update_context("last_intents", result["intents_detected"])
        if result["missing_slots"]:
            self.memory.update_context("missing_slots", result["missing_slots"])
        
        # Store the conversation turn
        self.memory.add_turn(
            user_input=user_input,
            bot_response=result["response"],
            action_taken=action_taken,
            intents_detected=result["intents_detected"],
            missing_slots=result["missing_slots"]
        )
        
        return result["response"]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """get detailed conversation summary for debugging/analysis"""
        return {
            "session_id": self.memory.session_id,
            "current_state": self.memory.current_state.value,
            "total_turns": len(self.memory.turns),
            "context": self.memory.get_context(),
            "conversation_history": self.memory.get_conversation_history()
        }
    
    def reset_conversation(self):
        """reset the conversation to start fresh"""
        self.memory = AgenticConversationMemory()
    
    def get_state(self) -> str:
        """get current conversation state"""
        return self.memory.current_state.value
    
    def is_conversation_complete(self) -> bool:
        """check if conversation is in completed state"""
        return self.memory.current_state == ConversationState.COMPLETED


# Demonstration functions
def demo_agentic_bot():
    """demonstrate the agentic bot with various types of queries"""
    bot = AgenticConversationBot()
    
    test_inputs = [
        "What is 5 + 3?",  # Calculator
        "Show me your mugs",  # RAG
        "What are the hours for SS 2?",  # Text2SQL
        "Calculate",  # Incomplete - should ask for follow-up
        "What products?",  # Vague product query
        "Store info",  # Incomplete outlet query
        "Thanks, that's all",  # Should finish
    ]
    
    print("=== Agentic Bot Demo ===\n")
    
    for i, user_input in enumerate(test_inputs, 1):
        print(f"Turn {i}:")
        print(f"User: {user_input}")
        response = bot.process_input(user_input)
        print(f"Bot: {response}")
        print(f"Action: {bot.memory.turns[-1].action_taken}")
        print(f"State: {bot.get_state()}")
        print()
    
    print("=== Conversation Summary ===")
    summary = bot.get_conversation_summary()
    print(f"Total turns: {summary['total_turns']}")
    print(f"Final state: {summary['current_state']}")


if __name__ == "__main__":
    demo_agentic_bot() 