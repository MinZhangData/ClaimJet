# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY chatbot.py .
COPY eu261_rules.py .
COPY flight_verifier.py .

# Expose port (Cloud Run will set PORT env variable)
ENV PORT=8080

# Update chatbot.py to use environment PORT variable
# Run the application
CMD python -c "import os; import chatbot; chatbot.demo.launch(server_name='0.0.0.0', server_port=int(os.environ.get('PORT', 8080)), share=False, show_error=True)"
