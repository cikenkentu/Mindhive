FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p faiss_drinkware_index

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run startup script then start server
CMD ["sh", "-c", "python startup.py && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"] 