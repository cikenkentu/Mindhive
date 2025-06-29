from enum import Enum, auto
from typing import Dict, List, Any, Optional
import re
import operator


class Action(Enum):
    """actions the planner can decide to take"""
    ASK_FOLLOWUP = auto()
    CALL_CALCULATOR = auto()
    CALL_RAG = auto()          # drinkware search
    CALL_TEXT2SQL = auto()     # outlet DB
    FINISH = auto()


def decide_action(state: str, intents: List[str], missing_slots: List[str]) -> Action:
    """lightweight planner function that decides next action based on state, intents, and missing information"""
    if missing_slots:
        return Action.ASK_FOLLOWUP
    if "calc_intent" in intents:
        return Action.CALL_CALCULATOR
    if "product_query" in intents:
        return Action.CALL_RAG
    if "outlet_query" in intents:
        return Action.CALL_TEXT2SQL
    return Action.FINISH


def calc_api(expr: str) -> float:
    """simple calculator API that evaluates mathematical expressions safely"""
    # Clean the expression - extract only the math part
    import re
    
    # Extract mathematical expressions from text
    math_pattern = r'(\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?(?:\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)*)|(\(\s*\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?\s*\)(?:\s*[\+\-\*\/]\s*\d+(?:\.\d+)?)*)'
    matches = re.findall(math_pattern, expr)
    
    if matches:
        # Take the first complete match
        math_expr = matches[0][0] if matches[0][0] else matches[0][1]
        math_expr = math_expr.strip()
    else:
        # Try to extract a simple pattern
        simple_pattern = r'\d+(?:\.\d+)?\s*[\+\-\*\/]\s*\d+(?:\.\d+)?'
        match = re.search(simple_pattern, expr)
        if match:
            math_expr = match.group(0)
        else:
            raise ValueError("No valid mathematical expression found")
    
    # Only allow basic math operations for security
    allowed_chars = set('0123456789+-*/.() ')
    if not all(c in allowed_chars for c in math_expr):
        raise ValueError("Invalid characters in expression")
    
    try:
        # Use eval but restrict to safe operations
        allowed_names = {
            "__builtins__": {},
            "__name__": "restricted",
            "__package__": None,
        }
        return eval(math_expr, allowed_names)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


def rag_endpoint(query: str) -> Dict[str, str]:
    """mock RAG endpoint for drinkware product search"""
    # Simple mock database of drinkware products
    products = {
        "mug": "Our ceramic mugs come in various sizes: 8oz, 12oz, and 16oz. Available in white, black, and custom colors.",
        "cup": "We offer coffee cups, tea cups, and travel cups. Materials include ceramic, stainless steel, and glass.",
        "bottle": "Water bottles available in plastic, stainless steel, and glass. Sizes from 12oz to 32oz.",
        "tumbler": "Insulated tumblers keep drinks hot or cold for hours. Available in 16oz and 20oz sizes.",
        "glass": "Drinking glasses in various styles: pint glasses, wine glasses, and cocktail glasses.",
        "flask": "Stainless steel flasks for beverages on the go. Available in 8oz and 16oz sizes."
    }
    
    query_lower = query.lower()
    for product, description in products.items():
        if product in query_lower:
            return {"reply": f"Here's what I found about {product}s: {description}"}
    
    return {"reply": "I couldn't find specific drinkware matching your query. We offer mugs, cups, bottles, tumblers, glasses, and flasks."}


def text2sql_endpoint(query: str) -> Dict[str, str]:
    """mock Text2SQL endpoint for outlet database queries"""
    # Simple mock outlet database
    outlets = [
        {"name": "SS 2", "city": "Petaling Jaya", "hours": "9 AM - 10 PM", "phone": "03-7876-5432"},
        {"name": "PJ Central", "city": "Petaling Jaya", "hours": "10 AM - 9 PM", "phone": "03-7955-1234"},
        {"name": "KLCC", "city": "Kuala Lumpur", "hours": "10 AM - 10 PM", "phone": "03-2166-8888"}
    ]
    
    query_lower = query.lower()
    
    # Handle different query types
    if "hours" in query_lower or "time" in query_lower or "open" in query_lower:
        for outlet in outlets:
            if outlet["name"].lower() in query_lower or outlet["city"].lower() in query_lower:
                return {"reply": f"{outlet['name']} is open {outlet['hours']}."}
        return {"reply": "Please specify which outlet you're asking about."}
    
    elif "phone" in query_lower or "number" in query_lower or "contact" in query_lower:
        for outlet in outlets:
            if outlet["name"].lower() in query_lower or outlet["city"].lower() in query_lower:
                return {"reply": f"{outlet['name']} phone number is {outlet['phone']}."}
        return {"reply": "Please specify which outlet you're asking about."}
    
    elif any(city in query_lower for city in ["petaling jaya", "pj", "kuala lumpur", "kl"]):
        if "petaling jaya" in query_lower or "pj" in query_lower:
            pj_outlets = [o for o in outlets if o["city"] == "Petaling Jaya"]
            outlet_names = ", ".join([o["name"] for o in pj_outlets])
            return {"reply": f"We have {len(pj_outlets)} outlets in Petaling Jaya: {outlet_names}."}
        elif "kuala lumpur" in query_lower or "kl" in query_lower:
            kl_outlets = [o for o in outlets if o["city"] == "Kuala Lumpur"]
            outlet_names = ", ".join([o["name"] for o in kl_outlets])
            return {"reply": f"We have {len(kl_outlets)} outlets in Kuala Lumpur: {outlet_names}."}
    
    # Default response for outlet queries
    all_outlets = ", ".join([f"{o['name']} ({o['city']})" for o in outlets])
    return {"reply": f"We have outlets at: {all_outlets}. What would you like to know about them?"}


def execute(action: Action, **kwargs) -> Dict[str, str]:
    """executor that runs the chosen action with provided parameters"""
    if action is Action.ASK_FOLLOWUP:
        return {"reply": kwargs.get("question", "Could you provide more information?")}
    
    if action is Action.CALL_CALCULATOR:
        try:
            result = calc_api(kwargs["expr"])
            return {"reply": f"The result is: {result}"}
        except Exception as e:
            return {"reply": f"Sorry, I couldn't calculate that: {str(e)}"}
    
    if action is Action.CALL_RAG:
        return rag_endpoint(kwargs["query"])
    
    if action is Action.CALL_TEXT2SQL:
        return text2sql_endpoint(kwargs["query"])
    
    if action is Action.FINISH:
        return {"reply": "Glad I could help!"}
    
    return {"reply": "I'm not sure how to handle that request."}


class IntentExtractor:
    """simple intent extraction for planning decisions"""
    
    def __init__(self):
        self.patterns = {
            "calc_intent": [
                r'\d+\s*[\+\-\*\/]\s*\d+',  # basic math operations
                r'calculate|compute|math|add|subtract|multiply|divide',
                r'what\s+is\s+\d+.*\d+',
                r'\d+\s*[\+\-\*\/]'
            ],
            "product_query": [
                r'mug|cup|bottle|tumbler|glass|flask|drinkware',
                r'what.*products|show.*products|available.*items',
                r'looking\s+for|need\s+a|want\s+to\s+buy'
            ],
            "outlet_query": [
                r'outlet|store|location|branch',
                r'where.*located|address|find.*store',
                r'hours|time.*open|phone|contact',
                r'petaling\s+jaya|kuala\s+lumpur|pj|kl|ss\s*2|klcc|pj\s+central'
            ]
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {
            intent: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for intent, patterns in self.patterns.items()
        }
    
    def extract_intents(self, text: str) -> List[str]:
        """extract intents from user input text"""
        intents = []
        
        for intent, patterns in self.compiled_patterns.items():
            if any(pattern.search(text) for pattern in patterns):
                intents.append(intent)
        
        return intents
    
    def extract_missing_slots(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """determine what information is missing for complete processing"""
        missing = []
        
        # Check for math expressions that are incomplete
        if any(pattern.search(text) for pattern in self.compiled_patterns["calc_intent"]):
            if not re.search(r'\d+\s*[\+\-\*\/]\s*\d+', text):
                missing.append("complete_expression")
        
        # Check for product queries that are too vague
        if any(pattern.search(text) for pattern in self.compiled_patterns["product_query"]):
            if len(text.split()) < 3 and not any(product in text.lower() 
                                               for product in ["mug", "cup", "bottle", "tumbler", "glass", "flask"]):
                missing.append("specific_product")
        
        # Check for outlet queries missing location or specific question
        if any(pattern.search(text) for pattern in self.compiled_patterns["outlet_query"]):
            has_location = any(loc in text.lower() 
                             for loc in ["petaling jaya", "pj", "kuala lumpur", "kl", "ss 2", "klcc", "pj central"])
            has_specific_query = any(q in text.lower() 
                                   for q in ["hours", "time", "phone", "contact", "address"])
            
            if not has_location and not has_specific_query:
                missing.append("location_or_specific_query")
        
        return missing


# Global intent extractor to avoid recreating on every call
_intent_extractor = IntentExtractor()

def plan_and_execute(user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """main planner/controller loop that processes input and executes appropriate action"""
    extractor = _intent_extractor
    
    # Step 1: Parse intent and missing information
    intents = extractor.extract_intents(user_input)
    missing_slots = extractor.extract_missing_slots(user_input, context)
    
    # Step 2: Choose an action
    state = context.get("state", "active") if context else "active"
    action = decide_action(state, intents, missing_slots)
    
    # Step 3: Execute that action and return the result
    kwargs = {"query": user_input, "expr": user_input}
    
    if action == Action.ASK_FOLLOWUP:
        if "complete_expression" in missing_slots:
            kwargs["question"] = "Could you provide a complete mathematical expression? For example: '5 + 3' or '10 * 2'"
        elif "specific_product" in missing_slots:
            kwargs["question"] = "What specific drinkware are you looking for? We have mugs, cups, bottles, tumblers, glasses, and flasks."
        elif "location_or_specific_query" in missing_slots:
            kwargs["question"] = "Which outlet location are you asking about, or what specific information do you need (hours, phone, address)?"
        else:
            kwargs["question"] = "Could you provide more details?"
    
    result = execute(action, **kwargs)
    
    return {
        "action_taken": action.name,
        "intents_detected": intents,
        "missing_slots": missing_slots,
        "response": result["reply"]
    } 