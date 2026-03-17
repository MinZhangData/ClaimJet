# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application structure
COPY app/ ./app/
COPY config/ ./config/
COPY run.py .

# Expose port (Cloud Run will set PORT env variable)
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the application - it will use PORT env variable via GRADIO_SERVER_PORT
CMD ["sh", "-c", "export GRADIO_SERVER_PORT=${PORT:-8080} && python run.py"]
