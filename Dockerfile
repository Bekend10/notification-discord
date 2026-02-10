FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose port (Railway/Render dùng biến $PORT)
EXPOSE 8000

# Run with production settings - support dynamic PORT
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}