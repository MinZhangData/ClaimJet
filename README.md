# KLM Flight Delay Compensation Agent

An AI-powered agent built with Google Vertex AI that helps KLM passengers determine their eligibility for compensation under EU Regulation 261/2004 (EU261).

## Features

- **EU261 Compliance**: Implements complete EU261/2004 regulation rules
- **Intelligent Conversation**: Powered by Gemini 1.5 Pro for natural interactions
- **Compensation Calculator**: Automatically calculates compensation amounts based on:
  - Flight distance (€250 - €600)
  - Delay duration (3-4 hour thresholds)
  - Flight type (cancellation, delay, denied boarding)
  - Extraordinary circumstances
- **Care & Assistance Rights**: Informs passengers of their rights to meals, accommodation, etc.
- **Multi-passenger Support**: Calculate total compensation for multiple passengers

## Project Structure

```
ClaimJet/
├── .venv/                     # Virtual environment
├── ai-agent-key.json         # Service account credentials
├── eu261_rules.py            # EU261 regulation rules engine
├── klm_claim_agent.py        # Main agent implementation
├── test_agent.py             # Test suite for rules engine
├── demo_agent.py             # Demo script with example scenarios
├── requirements.txt          # Python dependencies
├── start.sh                  # Quick start script
└── README.md                 # This file
```

## Setup

### Prerequisites

- Python 3.11+
- Google Cloud Project with Vertex AI API enabled (optional for rule-based chatbot)
- Service account with necessary permissions (optional for AI features)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd ClaimJet
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Google Cloud authentication (optional):**
   
   If you want to use the AI-powered agent:
   - Copy `ai-agent-key.json.example` to `ai-agent-key.json`
   - Replace with your actual Google Cloud service account credentials
   - **NEVER commit `ai-agent-key.json` to git!**
   
   The rule-based chatbot works without Google Cloud credentials.

## Usage

### 🌐 Web Chatbot (Recommended)

Run the chatbot with a beautiful web interface:

```bash
# Easy way
./run_chatbot.sh

# Or manually
source .venv/bin/activate
python chatbot.py
```

Then open your browser to: **http://localhost:7860**

### Quick Start Scripts

Use the provided start script:

```bash
# Run tests
./start.sh test

# Run demo scenarios
./start.sh demo

# Interactive mode (command line)
./start.sh interactive
```

### Command Line Mode

Run the agent in command line mode:

```bash
source .venv/bin/activate
python klm_claim_agent.py
```

Example conversation:
```
Agent: Hello! I'm your KLM compensation assistant. How can I help you today?

You: My flight KL1234 was delayed by 5 hours
Agent: I'm sorry to hear about your delay. To help determine your eligibility...

You: It was from Amsterdam to Barcelona, about 1200 km
Agent: [Agent calculates and provides compensation details]
```

### Demo Mode

Run predefined scenarios:

```bash
source .venv/bin/activate
python demo_agent.py
```

### Test Mode

Test the EU261 rules engine:

```bash
source .venv/bin/activate
python test_agent.py
```

## EU261 Rules Summary

### Compensation Amounts

| Distance | Compensation |
|----------|-------------|
| < 1,500 km | €250 |
| 1,500 - 3,500 km | €400 |
| > 3,500 km | €600 |

### Eligibility Criteria

✅ **Eligible for compensation:**
- Delay ≥ 3 hours (short/medium flights)
- Delay ≥ 4 hours (long flights)
- Flight cancelled with < 14 days notice
- Denied boarding (overbooking)

❌ **Not eligible:**
- Extraordinary circumstances (severe weather, ATC strikes, etc.)
- Delay below threshold
- Cancellation with adequate notice (14+ days)

### Care & Assistance Rights

Passengers are entitled to:
- **Meals & refreshments**: After 2-4 hours (depending on distance)
- **Hotel accommodation**: If delay extends to next day (5+ hours)
- **Transportation**: To and from hotel
- **Communication**: Two phone calls or emails
- **Reimbursement**: Right to refund if delay ≥ 5 hours

## Technical Details

### Architecture

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  KLM Claim Agent            │
│  (Gemini 1.5 Pro)          │
│                             │
│  - Natural conversation     │
│  - Context understanding    │
│  - Tool calling            │
└────────┬───────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Function Tools             │
├─────────────────────────────┤
│  1. calculate_compensation  │
│  2. get_care_rights        │
└────────┬───────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  EU261 Rules Engine         │
│                             │
│  - Eligibility check        │
│  - Compensation calculation │
│  - Rights determination     │
└─────────────────────────────┘
```

### Key Components

1. **EU261Rules Class** (`eu261_rules.py`)
   - Pure Python implementation of EU261 regulations
   - No external API dependencies
   - Comprehensive rule coverage

2. **KLMClaimAgent Class** (`klm_claim_agent.py`)
   - Vertex AI Gemini model integration
   - Function calling for structured data
   - Conversational interface

3. **Function Tools**
   - `calculate_compensation`: Determines eligibility and amount
   - `get_care_and_assistance_rights`: Provides passenger rights info

## Configuration

### Google Cloud Settings

- **Project ID**: `qwiklabs-asl-03-7e6910d4e317`
- **Location**: `us-central1`
- **Model**: `gemini-1.5-pro`

### Environment Variables

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/ai-agent-key.json"
```

## Example Scenarios

### Scenario 1: Eligible Delay
```
Flight: KL1234 (AMS → BCN)
Distance: 1,200 km
Delay: 4 hours
Result: €250 compensation
```

### Scenario 2: Extraordinary Circumstances
```
Flight: KL897 (AMS → LHR)
Distance: 350 km
Delay: 5 hours
Reason: Severe weather
Result: No compensation (extraordinary circumstances)
```

### Scenario 3: Flight Cancellation
```
Flight: KL643 (AMS → JFK)
Distance: 5,900 km
Notice: 3 days before departure
Passengers: 2
Result: €1,200 total (€600 × 2)
```

## Limitations

- Requires active internet connection for Vertex AI API
- Limited to KLM flights (can be extended to other EU carriers)
- Does not file actual claims (provides eligibility information only)
- Claim time limits vary by country (typically 3 years)

## Future Enhancements

- [ ] Integration with KLM flight database for real-time data
- [ ] Automated claim form generation
- [ ] Multi-language support
- [ ] Mobile app interface
- [ ] Email notification system
- [ ] Integration with payment systems

## Support

For issues or questions about:
- **EU261 regulations**: Contact your local aviation authority
- **KLM claims**: Visit klm.com or contact customer service
- **This agent**: Check the code or consult Google Cloud documentation

## License

This is a demonstration project built for educational purposes as part of a Google Cloud Qwiklabs exercise.

## Acknowledgments

- EU Regulation 261/2004 for passenger rights framework
- Google Cloud Vertex AI for AI capabilities
- KLM Royal Dutch Airlines for inspiration