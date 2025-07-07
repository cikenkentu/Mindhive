# Mindhive AI Chatbot Engineer Assessment

## Setup & Run Instructions

### Prerequisites
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-openai-api-key"  # Mac/Linux
# set OPENAI_API_KEY=your-openai-api-key    # Windows
```

### Quick Start

**Part 1: Sequential Conversation**
```bash
cd Question_1
python sequential_conversation.py
python test_sequential_conversation.py
```

**Part 2: Agentic Planning**
```bash
cd Question_2
python agentic_bot.py
python -m pytest test_planner.py -v
```

**Part 3: Tool Integration**
```bash
cd Question_3
# Terminal 1: Start calculator server
python server.py

# Terminal 2: Run bot
python agentic_bot.py
python test_calculator_integration.py
```

**Part 4: Custom API & RAG**
```bash
cd Question_4
# Initialize data
python ingestion/ingest_products.py
python ingestion/ingest_outlets.py

# Start API server
uvicorn app.main:app --reload

# Test integration
python chatbot_integration.py
```

**Part 5: Unhappy Flows**
```bash
cd Question_5
python run_tests.py
```

## Architecture Overview

### Core Components

**State Management (Part 1)**
- LangChain conversation memory
- Entity extraction and context tracking
- Multi-turn conversation flow

**Agentic Planning (Part 2)**
- Intent classification and action selection
- Decision tree for follow-up questions
- Dynamic conversation control

**Tool Integration (Part 3)**
- Calculator API with HTTP client
- Retry logic and error handling
- Service health monitoring

**RAG & Text2SQL (Part 4)**
- FAISS vector store for product search
- SQLite database for outlet queries
- FastAPI with OpenAPI documentation

**Security & Robustness (Part 5)**
- Input validation and sanitization
- SQL injection and XSS protection
- Graceful error handling

### Key Trade-offs

**Memory vs Performance**
- Conversation history stored in memory for simplicity
- Trade-off: Limited scalability for production use

**Hardcoded Data vs Web Scraping**
- Using static data for reliable testing
- Trade-off: Not real-time but more stable for demos

**Simple Architecture vs Microservices**
- Monolithic FastAPI app for easier deployment
- Trade-off: Less scalable but simpler to maintain

**Local Vector Store vs Cloud**
- FAISS local storage for cost efficiency
- Trade-off: No distributed scaling but zero hosting costs

## Project Structure
```
├── Question_1/          # Sequential conversation with memory
├── Question_2/          # Agentic planning and decision logic
├── Question_3/          # Calculator tool integration
├── Question_4/          # FastAPI with RAG and Text2SQL
├── Question_5/          # Security and unhappy flows testing
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Deployment

See `Question_4/` for production deployment with Railway
