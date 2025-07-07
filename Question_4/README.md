# ZUS Coffee API - Question 4

FastAPI backend for ZUS Coffee product search and outlet information with RAG and Text2SQL capabilities.

## 🚀 Live Demo

**API Base URL**: `https://your-deployment-url.railway.app`

**Interactive Documentation**: `https://your-deployment-url.railway.app/docs`

## 📋 Features

- **Products Endpoint**: RAG-powered product search using local HuggingFace embeddings
- **Outlets Endpoint**: Text2SQL natural language queries with intelligent fallback
- **Health Monitoring**: Comprehensive health checks for all components
- **OpenAPI Documentation**: Auto-generated API docs at `/docs`

## 🎯 API Endpoints

### Products
- `GET /products?query=<search_term>` - Search ZUS drinkware products
- `GET /products/health` - Products service health check

### Outlets  
- `GET /outlets?query=<natural_language_query>` - Query ZUS outlets
- `GET /outlets/list` - List all outlets
- `GET /outlets/health` - Outlets service health check

### General
- `GET /` - API information
- `GET /health` - Main health check
- `GET /docs` - Interactive API documentation

## 📖 Example Usage

### Test Products Endpoint
```bash
curl "https://your-url.railway.app/products?query=What%20types%20of%20tumblers%20do%20you%20offer?"
```

### Test Outlets Endpoint
```bash
curl "https://your-url.railway.app/outlets?query=Which%20outlets%20are%20in%20Kuala%20Lumpur?"
```

### List All Outlets
```bash
curl "https://your-url.railway.app/outlets/list"
```

## 🔧 Local Development

### Prerequisites
- Python 3.9+
- pip

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database and vector store
python startup.py

# Start server
python -m uvicorn app.main:app --reload
```

Server will be available at: `http://localhost:8000`

## 🏗️ Architecture

### Components
- **FastAPI**: Web framework and API server
- **FAISS**: Vector store for product embeddings
- **SQLite**: Database for outlet information  
- **HuggingFace**: Local embeddings (all-MiniLM-L6-v2)
- **LangChain**: RAG and Text2SQL pipelines

### Data Sources
- **Products**: ZUS Coffee drinkware collection (with fallback mode)
- **Outlets**: 6 real ZUS Coffee outlets in KL/Selangor

## 🚀 Deployment

### Railway (Recommended)
1. Fork this repository
2. Connect to [Railway](https://railway.app)
3. Deploy from GitHub
4. Railway will automatically:
   - Build using Dockerfile
   - Run startup script
   - Start the FastAPI server

### Environment Variables (Optional)
- `OPENAI_API_KEY`: For enhanced LLM features (optional, has good fallbacks)
- `PORT`: Server port (Railway sets this automatically)

## 📊 Testing

Run comprehensive endpoint tests:
```bash
python test_endpoints.py
```

View example transcripts:
```bash
python example_transcripts.py
```

## 🛡️ Error Handling

- **Graceful Degradation**: Falls back to pattern matching when LLM unavailable
- **Input Validation**: FastAPI automatic validation with clear error messages  
- **Health Monitoring**: Real-time status of all components
- **Timeout Handling**: Robust connection and request timeout management

## 📁 Project Structure

```
Question_4/
├── app/
│   ├── main.py           # FastAPI application
│   ├── products.py       # Products endpoint with RAG
│   ├── outlets.py        # Outlets endpoint with Text2SQL
│   ├── embeddings.py     # HuggingFace embeddings manager
│   ├── models.py         # Database models
│   └── db.py            # Database configuration
├── ingestion/
│   ├── ingest_products.py # Vector store ingestion
│   └── ingest_outlets.py  # Database ingestion
├── chatbot_integration.py # Integration examples
├── example_transcripts.py # Success/failure examples
├── test_endpoints.py     # Comprehensive tests
├── startup.py           # Initialization script
├── Dockerfile           # Container configuration
└── requirements.txt     # Dependencies
```

## ✅ Assessment Compliance

### Deliverables Completed:
- ✅ FastAPI repo with OpenAPI spec covering `/products`, `/outlets`
- ✅ Vector-store ingestion scripts and retrieval code for products  
- ✅ Text2SQL prompts/pipeline plus DB schema and executor for outlets
- ✅ Chatbot integration code demonstrating calls to all endpoints
- ✅ Example transcripts for each endpoint showing success and failure modes

### Key Features:
- ✅ **Local/Free**: No mandatory API costs (HuggingFace embeddings)
- ✅ **Production Ready**: Health checks, error handling, fallbacks
- ✅ **Well Documented**: Auto-generated docs, example transcripts  
- ✅ **Robust**: Comprehensive error handling and validation

## 🔗 Links

- **Repository**: [GitHub Link]
- **Live Demo**: [Deployment URL]
- **API Docs**: [Deployment URL]/docs
- **Health Check**: [Deployment URL]/health 