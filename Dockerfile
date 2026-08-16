# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY setup_database.py .

# Expose port (Cloud Run sets PORT env variable)
ENV PORT=8080
EXPOSE 8080

# Run the application - use PORT from environment
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port $PORT"]
