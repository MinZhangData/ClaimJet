#!/bin/bash
# Quick run script for KLM Chatbot

echo "🚀 Starting KLM Flight Compensation Chatbot..."
echo ""

# Activate virtual environment
source .venv/bin/activate

# Set authentication
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/ai-agent-key.json"

# Run chatbot
python chatbot.py
