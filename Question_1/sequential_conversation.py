import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from data import OUTLETS_DB, OutletInfo


class ConversationState(Enum):
    """
    conversation state enumeration
    """
    INITIAL = "initial"
    LOCATION_INQUIRY = "location_inquiry"
    OUTLET_SELECTION = "outlet_selection"
    INFORMATION_REQUEST = "information_request"
    COMPLETED = "completed"


@dataclass
class ConversationTurn:
    """
    single conversation turn data
    """
    turn_id: int
    timestamp: str
    user_input: str
    bot_response: str
    state: str
    extracted_entities: Dict[str, Any]
    context_variables: Dict[str, Any]


class ConversationMemory:
    """
    manages conversation memory and state
    """
    
    def __init__(self):
        self.turns = []
        self.current_state = ConversationState.INITIAL
        self.context_variables = {}
        self.session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        self.outlets_db = OUTLETS_DB
    
    def add_turn(self, user_input, bot_response, extracted_entities=None):
        """
        add new conversation turn
        """
        if extracted_entities is None:
            extracted_entities = {}
            
        turn = ConversationTurn(
            turn_id=len(self.turns) + 1,
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            bot_response=bot_response,
            state=self.current_state.value,
            extracted_entities=extracted_entities,
            context_variables=self.context_variables.copy()
        )
        self.turns.append(turn)
    
    def update_context(self, key, value):
        """
        update context variable
        """
        self.context_variables[key] = value
    
    def get_context(self, key, default=None):
        """
        get context variable
        """
        return self.context_variables.get(key, default)
    
    def set_state(self, new_state):
        """
        update conversation state
        """
        self.current_state = new_state
    
    def get_debug_summary(self):
        """
        get detailed summary for debugging
        """
        return {
            "session_id": self.session_id,
            "total_turns": len(self.turns),
            "current_state": self.current_state.value,
            "last_user_input": self.turns[-1].user_input if self.turns else None,
            "last_bot_response": self.turns[-1].bot_response if self.turns else None,
            "context_variables": self.context_variables,
            "conversation_flow": [turn.state for turn in self.turns]
        }


class EntityExtractor:
    """
    extracts entities from user input
    """
    
    def __init__(self):
        # compile regex patterns once for efficiency
        raw_location_patterns = {
            "petaling_jaya": r"(petaling\s+jaya|pj|ss\s*\d+)",
            "kuala_lumpur": r"(kuala\s+lumpur|kl|klcc)",
            "ss2": r"ss\s*2",
            "pj_central": r"pj\s+central",
            "klcc": r"klcc"
        }
        
        raw_intent_patterns = {
            "outlet_inquiry": r"(outlets?|stores?|shops?|branch(es)?)",
            "opening_time": r"(opening|open|time|hours|when|closing)",
            "location": r"(where|location|address|located|exactly)",
            "phone": r"(phone|number|contact|call)"
        }
        
        self.location_patterns = {k: re.compile(v, re.I) for k, v in raw_location_patterns.items()}
        self.intent_patterns = {k: re.compile(v, re.I) for k, v in raw_intent_patterns.items()}
    
    def extract(self, text):
        """
        extract entities and intents from text
        """
        entities = {
            "locations": [],
            "intents": [],
            "raw_text": text
        }
        
        # extract locations using pre-compiled patterns
        for location, pattern in self.location_patterns.items():
            if pattern.search(text):
                entities["locations"].append(location)
        
        # extract intents using pre-compiled patterns
        for intent, pattern in self.intent_patterns.items():
            if pattern.search(text):
                entities["intents"].append(intent)
        
        return entities


class SequentialConversationBot:
    """
    main conversation bot with sequential memory
    """
    
    def __init__(self):
        self.memory = ConversationMemory()
        self.extractor = EntityExtractor()
    
    def process_input(self, user_input):
        """
        process user input and generate response
        """
        # handle empty input
        if not user_input or not user_input.strip():
            return "I didn't catch that—could you re-type your question?"
        
        entities = self.extractor.extract(user_input)
        response = self._generate_response(user_input, entities)
        self.memory.add_turn(user_input, response, entities)
        
        return response
    
    def _generate_response(self, user_input, entities):
        """
        generate response based on conversation state and entities
        """
        # detect location switch mid-conversation
        if ("actually" in user_input.lower() or "what about" in user_input.lower()):
            known_locs = {"petaling_jaya", "kuala_lumpur"}
            locs = [loc for loc in entities["locations"] if loc in known_locs]
            if locs and self.memory.current_state != ConversationState.INITIAL:
                self.memory.set_state(ConversationState.OUTLET_SELECTION)
                region = locs[-1]
                self.memory.update_context("inquiry_location", region)
                outlet_names = [o.name for o in self.memory.outlets_db[region]]
                return (f"Switching to {region.replace('_',' ').title()}. "
                        f"Which outlet are you referring to? We have: {', '.join(outlet_names)}")

        current_state = self.memory.current_state
        
        if current_state == ConversationState.INITIAL:
            return self._handle_initial_state(user_input, entities)
        elif current_state == ConversationState.LOCATION_INQUIRY:
            return self._handle_location_inquiry(user_input, entities)
        elif current_state == ConversationState.OUTLET_SELECTION:
            return self._handle_outlet_selection(user_input, entities)
        elif current_state == ConversationState.INFORMATION_REQUEST:
            return self._handle_information_request(user_input, entities)
        else:
            return "How can I help you today?"
    
    def _handle_initial_state(self, user_input, entities):
        """
        handle initial conversation state
        """
        # check for direct outlet queries
        if "ss2" in entities["locations"] or "ss 2" in user_input.lower():
            self.memory.update_context("inquiry_location", "petaling_jaya")
            outlets = self.memory.outlets_db["petaling_jaya"]
            selected_outlet = next((outlet for outlet in outlets if "SS 2" in outlet.name), None)
            if selected_outlet:
                self.memory.update_context("selected_outlet", selected_outlet)
                self.memory.set_state(ConversationState.INFORMATION_REQUEST)
                # check for immediate info request
                if any(intent in entities["intents"] for intent in ("opening_time", "phone", "location")):
                    return self._handle_information_request(user_input, entities)
                return f"Great! You're asking about the {selected_outlet.name}. What would you like to know about it?"
        
        elif "klcc" in entities["locations"] or "klcc" in user_input.lower():
            self.memory.update_context("inquiry_location", "kuala_lumpur")
            outlets = self.memory.outlets_db["kuala_lumpur"]
            selected_outlet = next((outlet for outlet in outlets if "KLCC" in outlet.name), None)
            if selected_outlet:
                self.memory.update_context("selected_outlet", selected_outlet)
                self.memory.set_state(ConversationState.INFORMATION_REQUEST)
                # check for immediate info request
                if any(intent in entities["intents"] for intent in ("opening_time", "phone", "location")):
                    return self._handle_information_request(user_input, entities)
                return f"Perfect! You're asking about the {selected_outlet.name}. What would you like to know about it?"
        
        if "outlet_inquiry" in entities["intents"]:
            if "petaling_jaya" in entities["locations"]:
                self.memory.update_context("inquiry_location", "petaling_jaya")
                outlets = self.memory.outlets_db["petaling_jaya"]
                
                if len(outlets) > 1:
                    self.memory.set_state(ConversationState.OUTLET_SELECTION)
                    outlet_names = [outlet.name for outlet in outlets]
                    return f"Yes! We have outlets in Petaling Jaya. Which outlet are you referring to? We have: {', '.join(outlet_names)}"
                else:
                    self.memory.set_state(ConversationState.INFORMATION_REQUEST)
                    self.memory.update_context("selected_outlet", outlets[0])
                    return f"Yes! We have the {outlets[0].name} in {outlets[0].location}. What would you like to know about it?"
            
            elif entities["locations"]:
                location = entities["locations"][0]
                self.memory.update_context("inquiry_location", location)
                if location in self.memory.outlets_db:
                    outlets = self.memory.outlets_db[location]
                    if len(outlets) > 1:
                        outlet_names = [outlet.name for outlet in outlets]
                        self.memory.set_state(ConversationState.OUTLET_SELECTION)
                        return f"Yes! We have outlets in {location.replace('_', ' ').title()}. Which outlet are you referring to? We have: {', '.join(outlet_names)}"
                    else:
                        self.memory.set_state(ConversationState.INFORMATION_REQUEST)
                        self.memory.update_context("selected_outlet", outlets[0])
                        return f"Yes! We have the {outlets[0].name} in {outlets[0].location}. What would you like to know about it?"
                else:
                    return f"I'm sorry, we don't have any outlets in {location.replace('_', ' ').title()} at the moment."
            else:
                # check for unrecognized location
                m = re.search(r"outlet[s]?\s+in\s+([A-Za-z\s]+)\??", user_input, re.I)
                if m and not entities["locations"]:
                    unknown = m.group(1).strip().title()
                    return f"I'm sorry, we don't have any outlets in {unknown} at the moment."
                
                self.memory.set_state(ConversationState.LOCATION_INQUIRY)
                return "Yes, we have outlets in several locations! Which area are you interested in?"
        
        return "Hello! How can I help you with our outlet information today?"
    
    def _handle_location_inquiry(self, user_input, entities):
        """
        handle location inquiry state
        """
        if entities["locations"]:
            location = entities["locations"][0]
            self.memory.update_context("inquiry_location", location)
            
            if location in self.memory.outlets_db:
                outlets = self.memory.outlets_db[location]
                if len(outlets) > 1:
                    self.memory.set_state(ConversationState.OUTLET_SELECTION)
                    outlet_names = [outlet.name for outlet in outlets]
                    return f"Great! We have outlets in {location.replace('_', ' ').title()}. Which outlet are you referring to? We have: {', '.join(outlet_names)}"
                else:
                    self.memory.set_state(ConversationState.INFORMATION_REQUEST)
                    self.memory.update_context("selected_outlet", outlets[0])
                    return f"Perfect! We have the {outlets[0].name} in {outlets[0].location}. What would you like to know about it?"
            else:
                return f"I'm sorry, we don't have any outlets in {location.replace('_', ' ').title()} at the moment. We have outlets in Petaling Jaya and Kuala Lumpur."
        
        return "Which location are you interested in? We have outlets in Petaling Jaya and Kuala Lumpur."
    
    def _handle_outlet_selection(self, user_input, entities):
        """
        handle outlet selection state
        """
        inquiry_location = self.memory.get_context("inquiry_location")
        if inquiry_location and inquiry_location in self.memory.outlets_db:
            outlets = self.memory.outlets_db[inquiry_location]
            selected_outlet = None
            
            user_lower = user_input.lower().strip()
            
            # outlet pattern matching
            outlet_patterns = {
                "SS 2 Outlet": [r'\bss\s*2\b', r'\bss2\b'],
                "PJ Central Outlet": [r'\bpj\s+central\b', r'\bpj\s*central\b', r'\bcentral\b'],
                "KLCC Outlet": [r'\bklcc\b']
            }
            
            for outlet in outlets:
                outlet_name = outlet.name
                if outlet_name in outlet_patterns:
                    patterns = outlet_patterns[outlet_name]
                    if any(re.search(pattern, user_lower) for pattern in patterns):
                        # special validation for SS 2 to prevent false matches
                        if "SS 2 Outlet" in outlet_name:
                            if re.search(r'\bss\s*2\b', user_lower) and not re.search(r'\bss\s*(?!2\b)\d+', user_lower):
                                selected_outlet = outlet
                                break
                        else:
                            selected_outlet = outlet
                            break
            
            if selected_outlet:
                self.memory.update_context("selected_outlet", selected_outlet)
                # check for immediate info request
                if any(intent in entities["intents"] for intent in ("opening_time", "phone", "location")):
                    self.memory.set_state(ConversationState.INFORMATION_REQUEST)
                    return self._handle_information_request(user_input, entities)
                
                self.memory.set_state(ConversationState.INFORMATION_REQUEST)
                return f"Perfect! You're asking about the {selected_outlet.name}. What would you like to know about it?"
        
        # provide helpful suggestions for unmatched outlets
        if inquiry_location and inquiry_location in self.memory.outlets_db:
            outlets = self.memory.outlets_db[inquiry_location]
            outlet_names = [outlet.name for outlet in outlets]
            location_name = inquiry_location.replace('_', ' ').title()
            return f"We don't have that outlet in {location_name}. Our {location_name} outlets are: {', '.join(outlet_names)}."
        
        return "I'm not sure which outlet you're referring to. Could you please specify which outlet you're interested in?"
    
    def _handle_information_request(self, user_input, entities):
        """
        handle information request state
        """
        selected_outlet = self.memory.get_context("selected_outlet")
        if not selected_outlet:
            return "I'm sorry, I need to know which outlet you're asking about first."
        
        # check for conversation ending
        if any(word in user_input.lower() for word in ["thanks", "thank you", "bye", "goodbye"]):
            self.memory.set_state(ConversationState.COMPLETED)
            return "You're welcome! Feel free to ask if you need any other information about our outlets."
        
        if "opening_time" in entities["intents"]:
            return f"Ah yes, the {selected_outlet.name} opens at {selected_outlet.opening_time} and closes at {selected_outlet.closing_time}. Is there anything else you'd like to know?"
        
        elif "location" in entities["intents"]:
            return f"The {selected_outlet.name} address is {selected_outlet.address}. What else would you like to know?"
        
        elif "phone" in entities["intents"]:
            return f"You can contact the {selected_outlet.name} at {selected_outlet.phone}. Any other questions?"
        
        else:
            # provide general information
            return (f"Here's the information for {selected_outlet.name}:\n"
                   f"Location: {selected_outlet.address}\n"
                   f"Hours: {selected_outlet.opening_time} - {selected_outlet.closing_time}\n"
                   f"Phone: {selected_outlet.phone}\n"
                   f"Is there anything specific you'd like to know?")
    
    def reset_conversation(self):
        """
        reset conversation to start fresh
        """
        self.memory = ConversationMemory()
    
    def get_conversation_summary(self):
        """
        get summary of current conversation
        """
        return {
            "session_id": self.memory.session_id,
            "total_turns": len(self.memory.turns),
            "current_state": self.memory.current_state.value,
            "context_variables": self.memory.context_variables
        }
    
    def get_debug_info(self):
        """
        get detailed debug information for logging
        """
        return self.memory.get_debug_summary()
    
    def export_conversation(self, filename=None):
        """
        export conversation to json file
        """
        if filename is None:
            filename = f"conversation_{self.memory.session_id}.json"
        
        export_data = {
            "session_id": self.memory.session_id,
            "turns": [asdict(turn) for turn in self.memory.turns],
            "final_state": self.memory.current_state.value,
            "context_variables": self.memory.context_variables
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filename


def main():
    """
    demonstrate the conversation system
    """
    bot = SequentialConversationBot()
    
    print("=== Sequential Conversation Bot Demo ===")
    print("Type 'quit' to exit, 'reset' to start over, 'summary' to see conversation summary")
    print("Example: Try asking 'Is there an outlet in Petaling Jaya?'")
    print()
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'reset':
            bot.reset_conversation()
            print("Bot: Conversation reset. How can I help you today?")
            continue
        elif user_input.lower() == 'summary':
            summary = bot.get_conversation_summary()
            print(f"Bot: Conversation Summary:")
            print(f"  Session ID: {summary['session_id']}")
            print(f"  Total Turns: {summary['total_turns']}")
            print(f"  Current State: {summary['current_state']}")
            print(f"  Context: {summary['context_variables']}")
            continue
        elif user_input.lower() == 'debug':
            debug_info = bot.get_debug_info()
            print(f"Bot: Debug Info:")
            for key, value in debug_info.items():
                print(f"  {key}: {value}")
            continue
        
        if user_input:
            response = bot.process_input(user_input)
            print(f"Bot: {response}")
    
    # export conversation
    export_file = bot.export_conversation()
    print(f"\nConversation exported to: {export_file}")


if __name__ == "__main__":
    main() 