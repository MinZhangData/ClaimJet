# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY eu261_rules.py .

# Copy agent package
COPY klm_claim_agent/ klm_claim_agent/

# Expose port (Cloud Run will set PORT env variable)
ENV PORT=8080

# Serve the agent via ADK API server
CMD adk api_server --host 0.0.0.0 --port $PORT .
