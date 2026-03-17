# ClaimJet - EU261 Flight Compensation Assistant

An AI-powered chatbot built with **Google Gemini 2.5 Flash** and **Agent Developer Kit (ADK)** that helps airline passengers determine their eligibility for compensation under EU Regulation 261/2004 (EU261).

🚀 **Live Demo**: [https://claimjet-adk-chatbot-118562953748.us-central1.run.app](https://claimjet-adk-chatbot-118562953748.us-central1.run.app)

## 🧪 Quick Test Examples

Try these queries on the live demo or locally:

**Built-in Test Flights (No API needed):**
```
Check flight TEST001
Check flight TEST002 2026-03-12
```

**Manual Calculations:**
```
My flight was delayed 5 hours and flew 2000km
I flew from Amsterdam to Barcelona, delayed 4 hours
Calculate compensation for 3.5 hour delay on 1800km flight
```

**EU261 Information:**
```
What are the EU261 delay thresholds?
What rights do I have if my flight is delayed?
How much compensation for a 4000km flight?
```

**Real Flight Verification (requires AviationStack API key):**
```
Check flight KL1234 2026-03-15
Check flight LH456 2026-04-20
Check flight BA789
```

## ✨ Features

- ✈️ **Smart Flight Verification**: Automatically verifies real flight data including delays and cancellations
- 💰 **Compensation Calculator**: Calculates EU261 compensation amounts (€250 - €600) based on distance and delay
- 🤖 **AI Agent with Function Calling**: Uses Google Gemini 2.5 Flash with intelligent tool selection
- 📋 **EU261 Knowledge Base**: Complete implementation of EU261/2004 regulation rules
- 🌐 **Web UI**: Beautiful Gradio interface for easy interaction
- ☁️ **Cloud Deployed**: Runs on Google Cloud Run with automatic scaling
- 🧪 **Built-in Test Flights**: No API required for testing - includes TEST001 and TEST002 scenarios

## 🚀 Quick Start

### Option 1: Try Online (No Setup Required)

Visit the live demo: **https://claimjet-adk-chatbot-118562953748.us-central1.run.app**

Test with these examples:
- `Check flight TEST001` - Returns €600 compensation (long-haul delay)
- `Check flight TEST002 2026-03-12` - Returns €250 compensation (short-haul delay)
- `My flight was delayed 5 hours and flew 2000km` - Manual calculation
- `What are the EU261 delay thresholds?` - Get regulation information

### Option 2: Run Locally

**Prerequisites:**
- Python 3.11+
- Google Gemini API key (free tier available)

**Setup in 3 steps:**

1. **Clone and install:**
   ```bash
   git clone https://github.com/yourusername/ClaimJet.git
   cd ClaimJet
   pip install -r requirements.txt
   ```

2. **Get your API key:**
   - Visit: https://aistudio.google.com/apikey
   - Click "Create API Key"
   - Copy your key

3. **Run the chatbot:**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   python chatbot_adk.py
   ```

4. **Open browser:**
   Navigate to `http://localhost:7860`

**One-liner for testing:**
```bash
export GEMINI_API_KEY='your-key' && python chatbot_adk.py
```

## 🏗️ Architecture

The agent uses a modern AI architecture with function calling:

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                            │
│              (Natural language questions)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Gradio Web UI                              │
│                  (chatbot_adk.py)                           │
│         • Chat interface with history                        │
│         • Gradio 6.0 format support                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              ADK Agent (adk_agent.py)                        │
│          FlightCompensationAgent class                       │
│         • Session management                                 │
│         • Tool orchestration                                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Google Gemini 2.5 Flash API                     │
│         • Natural language understanding                     │
│         • Function calling decision                          │
│         • Response generation                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
    ┌─────────────┐ ┌──────────────┐ ┌────────────────┐
    │verify_flight│ │ calculate    │ │  get_eu261    │
    │    _data    │ │compensation  │ │     _info     │
    └──────┬──────┘ └──────┬───────┘ └───────┬───────┘
           │                │                  │
           └────────────────┼──────────────────┘
                            │
                            ▼
           ┌────────────────────────────────┐
           │   EU261 Rules Engine           │
           │   (eu261_rules.py)            │
           │                                │
           │  • Eligibility checking        │
           │  • Compensation calculation    │
           │  • Distance thresholds         │
           │  • Delay thresholds            │
           │  • Extraordinary circumstances │
           └────────────────────────────────┘
                            │
                            ▼
           ┌────────────────────────────────┐
           │   Flight Verifier              │
           │   (flight_verifier.py)        │
           │                                │
           │  • Test flight data            │
           │  • Real flight API (optional)  │
           │  • Date/time validation        │
           └────────────────────────────────┘
```

**Key Components:**

1. **Gradio UI (`chatbot_adk.py`)**: Web interface with chat history
2. **ADK Agent (`adk_agent.py`)**: Manages AI agent lifecycle and tool calling
3. **Gemini 2.5 Flash**: Language model with function calling
4. **Function Tools**: Three specialized tools for different tasks
5. **Rules Engine (`eu261_rules.py`)**: Pure Python EU261 implementation
6. **Flight Verifier (`flight_verifier.py`)**: Flight data verification

## Project Structure

```
ClaimJet/
├── chatbot_adk.py          # Gradio web interface
├── adk_agent.py            # Google ADK agent with function calling
├── eu261_rules.py          # EU261 regulation rules engine
├── flight_verifier.py      # Flight data verification logic
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container configuration
├── .gitignore             # Git ignore rules
├── .dockerignore          # Docker ignore rules
├── README.md              # This file
└── QUICK_START.md         # Quick start guide
```

## 📊 EU261 Compensation Rules

### Compensation Amounts by Distance

| Distance | Delay Threshold | Compensation | Examples |
|----------|----------------|--------------|----------|
| **< 1,500 km** | ≥ 3 hours | **€250** | AMS→BCN, AMS→LHR, PAR→ROM |
| **1,500 - 3,500 km** | ≥ 3 hours | **€400** | AMS→ATH, LON→CAI, MAD→MOW |
| **> 3,500 km** | ≥ 4 hours | **€600** | AMS→JFK, LON→NYC, PAR→DXB |

### Eligibility Requirements

✅ **You ARE eligible if:**
- ✈️ Flight delayed **≥ 3-4 hours** at final destination (depending on distance)
- 📅 Flight cancelled with **< 14 days notice**
- 🚫 Denied boarding due to **overbooking**
- 🇪🇺 Departure from **EU airport** OR arrival to EU with **EU airline**
- 🎫 You had a **confirmed reservation** and checked in on time

❌ **You are NOT eligible if:**
- 🌩️ **Extraordinary circumstances**: Severe weather, ATC strikes, security risks, airport closures
- ⏱️ Delay **below threshold** (< 3-4 hours)
- 📆 Cancellation with **adequate notice** (14+ days before)
- 🛂 **Voluntary** downgrade or missed connection
- ✈️ Non-EU flights with **non-EU carriers**

### Additional Passenger Rights

Beyond compensation, you're entitled to:

| Right | When | What You Get |
|-------|------|--------------|
| **Meals & Drinks** | Delay ≥ 2 hours (short)<br>≥ 3 hours (medium)<br>≥ 4 hours (long) | Food and refreshments |
| **Communication** | Any significant delay | 2 free phone calls or emails |
| **Accommodation** | Overnight delay | Hotel + transport to/from hotel |
| **Reimbursement** | Delay ≥ 5 hours | Full ticket refund option |
| **Re-routing** | Cancellation/long delay | Alternative flight or full refund |

### Test Cases

The agent includes multiple test scenarios:

#### Built-in Test Flights (No API Required)

| Flight | Route | Distance | Delay | Status | Compensation |
|--------|-------|----------|-------|--------|--------------|
| TEST001 | AMS → JFK | 5,850 km | 6h 45m | Delayed | **€600** |
| TEST002 | AMS → BCN | 1,200 km | 4h 15m | Delayed | **€250** |

**Try these:**
- `Check flight TEST001` - Long-haul delay
- `Check flight TEST002 2026-03-12` - Short-haul delay

#### Real Flight API Test (AviationStack API)

The agent can verify real flights using the AviationStack API:

**Example:**
```
Check flight KL1234 2026-03-15
```

This will:
1. Query AviationStack API for real flight data
2. Verify departure/arrival airports
3. Check actual delay time
4. Calculate compensation if eligible

**Note:** Real flight verification requires an AviationStack API key configured in `flight_verifier.py`. Without an API key, the agent will still provide manual calculation assistance.

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export GEMINI_API_KEY="your-api-key"

# Run locally
python chatbot_adk.py
```

### Docker

```bash
# Build image
docker build -t claimjet-adk .

# Run container
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="your-api-key" \
  claimjet-adk
```

### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/claimjet-adk

# Deploy
gcloud run deploy claimjet-adk-chatbot \
  --image gcr.io/PROJECT_ID/claimjet-adk \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets=GEMINI_API_KEY=gemini-api-key:latest
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key from AI Studio |
| `AVIATIONSTACK_API_KEY` | No | AviationStack API key for real flight data verification |
| `GRADIO_SERVER_PORT` | No | Port for Gradio UI (default: 7860) |
| `PORT` | No | Port for Cloud Run (set automatically) |

### Optional: Real Flight API Integration

To enable real-time flight verification with live data:

1. **Get AviationStack API Key:**
   - Sign up at: https://aviationstack.com/
   - Free tier: 100 requests/month
   - Copy your API key

2. **Configure the key:**
   ```bash
   export AVIATIONSTACK_API_KEY="your-aviationstack-key"
   ```

3. **Test with real flights:**
   ```
   Check flight KL1234 2026-03-15
   Check flight LH456 2026-04-20
   Check flight BA789
   ```

The agent will automatically use the API if the key is configured, otherwise it falls back to manual calculation mode.

### Dependencies

- `google-genai>=1.0.0` - Google Gemini API client
- `gradio>=4.0.0` - Web UI framework
- `requests>=2.31.0` - HTTP client for flight API

See `requirements.txt` for complete list.

## Technology Stack

- **AI Model**: Google Gemini 2.5 Flash
- **Agent Framework**: Google ADK (Agent Developer Kit)
- **Web Framework**: Gradio 6.0
- **Deployment**: Google Cloud Run
- **Language**: Python 3.11

## 🔌 API Integration

### Real Flight Data Verification

The agent supports real-time flight verification through aviation APIs:

#### AviationStack API (Recommended)

**Setup:**
```bash
# Get free API key from https://aviationstack.com/
export AVIATIONSTACK_API_KEY="your-key-here"

# Test with real flights
python chatbot_adk.py
```

**Example queries:**
```
Check flight KL1234 2026-03-15
Check flight LH456 2026-04-20  
Check flight BA789
```

**What it verifies:**
- ✈️ Flight number and airline
- 🛫 Departure airport and time
- 🛬 Arrival airport and time
- ⏱️ Actual delay duration
- 📏 Flight distance
- 🗓️ Flight date

**API Tiers:**
| Plan | Requests/Month | Cost | Use Case |
|------|---------------|------|----------|
| Free | 100 | $0 | Testing & demos |
| Basic | 10,000 | $9.99 | Small projects |
| Professional | 100,000 | $49.99 | Production |

#### Fallback Mode (No API Key)

Without an API key, the agent still works but requires manual input:
```
My flight was delayed 5 hours and flew 2000km
I flew from Amsterdam to Barcelona, delayed 4 hours
```

The agent will guide you through providing the necessary details.

#### Other Supported APIs

- **FlightAware API**: Premium real-time data (requires paid subscription)
- **AeroDataBox**: Alternative with similar features
- **Test Flights**: Built-in TEST001 and TEST002 (no API needed)

## Future Enhancements

- [ ] Multi-language support (EN, NL, DE, FR, ES)
- [ ] Claim form PDF generation
- [ ] Email notification system
- [ ] Integration with multiple aviation APIs
- [ ] Support for other EU airlines beyond KLM
- [ ] Mobile-responsive design improvements
- [ ] User authentication and claim history

## Contributing

This is an educational project demonstrating Google ADK capabilities. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This is a demonstration project built for educational purposes.

## Support

- **EU261 Information**: [European Commission Aviation Rights](https://ec.europa.eu/transport/passenger-rights/)
- **Google ADK Documentation**: [Google Agent Developer Kit](https://cloud.google.com/vertex-ai/docs)
- **Issues**: Open an issue on GitHub

## Acknowledgments

- EU Regulation 261/2004 for passenger rights framework
- Google Cloud and Gemini API for AI capabilities
- Gradio team for the web UI framework

---

**Note**: This tool provides information only and does not file actual compensation claims. Always verify eligibility with the airline or relevant authorities.
