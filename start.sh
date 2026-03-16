#!/bin/bash
# Quick start script for KLM Claim Agent

echo "========================================"
echo "KLM Flight Delay Compensation Agent"
echo "========================================"
echo ""

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv .venv
    echo "Installing dependencies..."
    source .venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
else
    source .venv/bin/activate
fi

# Check if service account key exists
if [ ! -f "ai-agent-key.json" ]; then
    echo "Error: ai-agent-key.json not found!"
    echo "Please ensure the service account key is in the project directory."
    exit 1
fi

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/ai-agent-key.json"

echo "Environment ready!"
echo ""
echo "Available commands:"
echo "  1. Test rules engine:  python test_agent.py"
echo "  2. Run demo scenarios: python demo_agent.py"
echo "  3. Interactive mode:   python klm_claim_agent.py"
echo ""

# Run based on argument
if [ "$1" = "test" ]; then
    echo "Running tests..."
    python test_agent.py
elif [ "$1" = "demo" ]; then
    echo "Running demo..."
    python demo_agent.py
elif [ "$1" = "interactive" ]; then
    echo "Starting interactive mode..."
    python klm_claim_agent.py
else
    echo "Usage: ./start.sh [test|demo|interactive]"
    echo ""
    echo "Or manually run:"
    echo "  source .venv/bin/activate"
    echo "  python [script_name].py"
fi
