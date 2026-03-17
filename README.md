# ✈️ DelaySlayer - EU261 Flight Compensation Assistant

An intelligent chatbot powered by **Google Gemini 2.5 Flash** to help passengers check flight compensation eligibility under EU261 regulations.

## 🚀 Live Production App

**⭐ DelaySlayer:** https://delayslayer-o2lrnifutq-uc.a.run.app

*Previously known as ClaimJet - now rebranded to DelaySlayer*

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    Gradio Web Chat (Port 7860)                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      Session Management                          │
│              (Gradio State + Memory Bank Sessions)              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                         Memory Bank                              │
│           Google Cloud Firestore (Conversation Storage)          │
│  • Session-based persistence  • Context retrieval (10 msgs)     │
│  • Automatic cleanup          • Graceful degradation            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    ADK Agent (app/core/agent.py)                 │
│              Google Agent Development Kit (ADK)                  │
│  • System Instructions        • Function Calling                │
│  • Tool Selection             • Context Enhancement             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
┌───────────────▼────┐  ┌──────▼──────┐  ┌───▼────────────────┐
│  Flight Verifier   │  │  EU261 Rules │  │  EU261 Info Guide  │
│   (Tool #1)        │  │   (Tool #2)  │  │     (Tool #3)      │
│                    │  │              │  │                    │
│ • Real flight data │  │ • Calculate  │  │ • Regulations      │
│ • API integration  │  │   amounts    │  │ • Thresholds       │
│ • Mock test data   │  │ • Eligibility│  │ • Rights info      │
└────────────────────┘  └──────────────┘  └────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                      Gemini 2.5 Flash                            │
│               (Google GenAI API / Vertex AI)                     │
│  • Temperature: 0.3         • Function calling enabled          │
│  • System instructions      • Streaming responses               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                        Model Armor                               │
│              (Content Safety & Input Validation)                 │
│  • Template-based filtering  • Prompt injection protection      │
│  • PII detection             • Content moderation                │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Core Components

### 1. **Google ADK (Agent Development Kit)**
The foundation of DelaySlayer's intelligence.

**Location:** `app/core/agent.py`

**What it does:**
- Orchestrates agent behavior with system instructions
- Enables **function calling** to automatically select and use tools
- Manages context and conversation flow
- Integrates with Gemini 2.5 Flash for natural language understanding

**Key Features:**
```python
class FlightCompensationAgent:
    - tools = [verify_flight_data, calculate_compensation, get_eu261_info]
    - system_instruction = "You are a flight compensation assistant..."
    - chat(user_message, history, session_id) → response
```

**ADK Benefits:**
- ✅ Automatic tool selection based on user intent
- ✅ Structured function calling (no prompt engineering needed)
- ✅ Built-in error handling and retries
- ✅ Seamless integration with Google AI APIs

**Documentation:** [Google ADK Overview](https://ai.google.dev/adk)

---

### 2. **Memory Bank (Conversation Persistence)**
Enables context-aware conversations across messages.

**Location:** `app/core/memory_bank.py`

**What it does:**
- Stores conversation history in **Google Cloud Firestore**
- Retrieves recent context (last 10 messages by default)
- Enhances prompts with conversation history
- Manages sessions with unique UUIDs

**Architecture:**
```
User Message → Memory Bank.get_history(session_id)
             ↓
      Build context summary
             ↓
      Enhanced prompt = context + current message
             ↓
      Send to Gemini → Get response
             ↓
      Memory Bank.add_message(user + assistant)
```

**Key Features:**
```python
class MemoryBank:
    - create_session(user_id) → session_id
    - add_message(session_id, role, content)
    - get_history(session_id, limit=10) → messages[]
    - get_context_summary(session_id) → formatted_context
    - clear_session(session_id)
    - cleanup_old_sessions(days=7)
```

**Firestore Structure:**
```
conversations/
  └── {session_id}/
      ├── session_id: UUID
      ├── user_id: string
      ├── created_at: timestamp
      ├── last_activity: timestamp
      ├── messages: [
      │     {role, content, timestamp, metadata},
      │     ...
      │   ]
      └── metadata: {}
```

**Benefits:**
- ✅ Conversations persist across page refreshes
- ✅ Context-aware responses (remembers previous messages)
- ✅ Scalable (Firestore handles millions of sessions)
- ✅ Cost-effective (~$0.08 per 10K conversations)
- ✅ Graceful fallback if unavailable

**All setup instructions included in this README.**

---

### 3. **Model Armor (Content Safety)**
Protects against malicious inputs and unsafe content.

**Status:** Configured via Google Cloud Console

**What it does:**
- **Input validation** - Filters prompt injections, jailbreaks
- **PII detection** - Identifies and redacts sensitive data
- **Content moderation** - Blocks harmful/inappropriate content
- **Output filtering** - Ensures safe responses

**Protection Layers:**
```
User Input → Model Armor Template
           ↓
    Validate & Filter
           ↓
    Clean Input → Gemini
           ↓
    Response → Model Armor
           ↓
    Validate & Filter
           ↓
    Safe Output → User
```

**Configuration:**
- Template created via Google Cloud Console
- Template ID stored in `.env` file
- Applied to all Gemini API calls

**Setup instructions via Google Cloud Console (see below).**

---

### 4. **Agent Tools (Function Calling)**
Three specialized tools for flight compensation checks.

#### Tool #1: `verify_flight_data(flight_number, flight_date)`
**Purpose:** Verify flight information using real-time or mock data

**What it does:**
```python
Input:  flight_number="TEST001", flight_date="2026-03-17"
Output: Formatted decision with:
        - Flight details (route, delay, distance)
        - EU261 eligibility status
        - Compensation amount (if eligible)
        - Next steps for filing claims
```

**Location:** `app/services/flight_verifier.py`

**Features:**
- Real flight API integration (when configured)
- Mock test flights (TEST001, TEST002)
- Automatic EU261 eligibility calculation

---

#### Tool #2: `calculate_compensation(delay_hours, distance_km, ...)`
**Purpose:** Manual EU261 compensation calculation

**What it does:**
```python
Input:  delay_hours=5, distance_km=2000, cancellation=False
Output: Eligibility decision + compensation amount
```

**Location:** `app/services/eu261_rules.py`

**EU261 Rules Implemented:**
- Short flights (<1500km): €250 for 3+ hour delays
- Medium flights (1500-3500km): €400 for 3+ hour delays
- Long flights (>3500km): €600 for 4+ hour delays (€300 for 3-4h)
- Cancellation rules (based on advance notice)
- Denied boarding compensation
- Extraordinary circumstances handling

---

#### Tool #3: `get_eu261_info(query)`
**Purpose:** Answer questions about EU261 regulations

**What it does:**
```python
Input:  query="What are the delay thresholds?"
Output: Detailed information about EU261 rules
```

**Topics Covered:**
- Delay thresholds
- Compensation amounts
- Eligibility criteria
- Cancellation rights
- Extraordinary circumstances

---

## 🚀 Deployment Architecture

### Cloud Run Services

```
┌─────────────────────────────────────────────────────────────────┐
│                      Cloud Run (Serverless)                      │
├─────────────────────────────────────────────────────────────────┤
│  🎯 delayslayer (⭐ PRODUCTION)                                 │
│  • DelaySlayer v1.0 - Latest Production Release                │
│  • ADK + Memory Bank + Model Armor                              │
│  • URL: https://delayslayer-o2lrnifutq-uc.a.run.app            │
│  • Image: gcr.io/qwiklabs-asl-03-7e6910d4e317/delayslayer:v1    │
│  • Memory: 1Gi, CPU: 1, Timeout: 300s                           │
│  • Secrets: GEMINI_API_KEY from Secret Manager                  │
├─────────────────────────────────────────────────────────────────┤
│  Legacy Deployments (formerly ClaimJet)                         │
│  • claimjet-final (v3.0)                                        │
│  • claimjet-memory-bank (v2.0)                                  │
│  • Development/testing services                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Infrastructure Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Google Cloud Project                        │
│              qwiklabs-asl-03-7e6910d4e317                       │
├─────────────────────────────────────────────────────────────────┤
│  ✅ Cloud Run (us-central1)                                     │
│  ✅ Firestore (Native Mode, us-central1)                        │
│  ✅ Secret Manager (GEMINI_API_KEY)                             │
│  ✅ Container Registry (GCR)                                    │
│  ✅ Model Armor (Content Safety)                                │
│  ✅ IAM Service Account: ai-agent-sa@...                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
DelaySlayer/
├── app/                        # Application Package
│   ├── __init__.py
│   ├── core/                   # Core Business Logic
│   │   ├── __init__.py
│   │   ├── agent.py           # ADK Agent + Memory Bank Integration
│   │   └── memory_bank.py     # Firestore Conversation Storage
│   ├── services/               # External Services & Rules
│   │   ├── __init__.py
│   │   ├── flight_verifier.py # Flight Data Verification
│   │   └── eu261_rules.py     # EU261 Rules Engine
│   ├── models/                 # Data Models (future)
│   │   └── __init__.py
│   └── utils/                  # Utility Functions (future)
│       └── __init__.py
│
├── config/                     # Configuration Management
│   └── __init__.py            # Application Configuration
│
├── tests/                      # Test Suite
│   ├── __init__.py
│   └── test_memory_bank.py    # Memory Bank Integration Tests
│
├── scripts/                    # Utility Scripts (future)
│
├── run.py                      # Main Application Entry Point
├── requirements.txt            # Python Dependencies
├── Dockerfile                  # Container Build Instructions
├── .env                        # Environment Variables (local only, gitignored)
├── .env.example                # Environment Variables Template
└── README.md                   # Complete Project Documentation
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM** | Gemini 2.5 Flash | Natural language understanding & generation |
| **Agent Framework** | Google ADK | Function calling & tool orchestration |
| **Memory Storage** | Google Cloud Firestore | Conversation persistence |
| **Content Safety** | Google Model Armor | Input/output validation & filtering |
| **UI Framework** | Gradio 6.0 | Web-based chat interface |
| **Container** | Docker + Cloud Run | Serverless deployment |
| **Authentication** | Google Secret Manager | API key management |
| **Monitoring** | Cloud Logging | Error tracking & debugging |

---

## 🚦 Quick Start

### Prerequisites
- Google Cloud Project with billing enabled
- Gemini API key from [AI Studio](https://aistudio.google.com/apikey)
- Python 3.11+ and Docker installed

### 1. Clone Repository
```bash
git clone <repository-url>
cd DelaySlayer
```

### 2. Set Up Environment
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Enable Google Cloud Services
```bash
export PROJECT_ID="your-project-id"

# Enable required APIs
gcloud services enable firestore.googleapis.com --project=$PROJECT_ID
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

# Create Firestore database
gcloud firestore databases create --location=us-central1 --project=$PROJECT_ID
```

### 4. Run Locally
```bash
# Export Gemini API key
export GEMINI_API_KEY="your-api-key"

# Set Google Cloud credentials (for Firestore)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
export GCP_PROJECT="your-project-id"

# Start the chatbot
python run.py
```

Open browser: http://localhost:7860

### 5. Create Secret in Secret Manager
```bash
# Store your Gemini API key securely
echo -n "your-gemini-api-key" | gcloud secrets create gemini-api-key \
  --data-file=- \
  --project=$PROJECT_ID

# Or update existing secret
echo -n "your-gemini-api-key" | gcloud secrets versions add gemini-api-key \
  --data-file=- \
  --project=$PROJECT_ID
```

### 6. Deploy to Cloud Run
```bash
# Build and deploy DelaySlayer (latest)
gcloud builds submit --tag gcr.io/$PROJECT_ID/delayslayer:v1

gcloud run deploy delayslayer \
  --image gcr.io/$PROJECT_ID/delayslayer:v1 \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars GCP_PROJECT=$PROJECT_ID \
  --project=$PROJECT_ID

# Or deploy as claimjet-final (legacy name)
gcloud builds submit --tag gcr.io/$PROJECT_ID/claimjet-final:v3

gcloud run deploy claimjet-final \
  --image gcr.io/$PROJECT_ID/claimjet-final:v3 \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars GCP_PROJECT=$PROJECT_ID \
  --project=$PROJECT_ID
```

**Important:** Use `--set-secrets` to properly mount secrets, not `--set-env-vars` for API keys!

---

## 🧪 Test Flights

DelaySlayer includes mock flight data for testing:

| Flight | Route | Delay | Distance | Compensation |
|--------|-------|-------|----------|--------------|
| **TEST001** | AMS → JFK | 6h 45m | 5,850 km | €600 ✅ |
| **TEST002** | AMS → BCN | 4h 15m | 1,240 km | €250 ✅ |

**Try it:**
```
User: "Check flight TEST001"
Bot: ✅ ELIGIBLE FOR COMPENSATION

Flight: TEST001 (KL) - AMS → JFK
Status: Delayed 6h 45m
Distance: 5,850 km
Compensation: €600 per passenger

The flight qualifies for EU261 compensation.
```

---

## 🎯 User Experience Flow

### Example Conversation

```
┌─────────────────────────────────────────────────────────────────┐
│ User:  "Check flight TEST001"                                    │
├─────────────────────────────────────────────────────────────────┤
│ Bot:   ✅ ELIGIBLE FOR COMPENSATION                             │
│                                                                  │
│        Flight: TEST001 (KL) - AMS → JFK                         │
│        Status: Delayed 6h 45m                                    │
│        Distance: 5,850 km                                        │
│        Compensation: €600 per passenger                          │
│                                                                  │
│        The flight qualifies for EU261 compensation.             │
└─────────────────────────────────────────────────────────────────┘
        ↓ (Memory Bank stores this exchange)
┌─────────────────────────────────────────────────────────────────┐
│ User:  "How do I file a claim?"                                  │
├─────────────────────────────────────────────────────────────────┤
│ Bot:   Based on your TEST001 flight with €600 compensation,     │
│        here's how to file your claim:                            │
│                                                                  │
│        1. Contact KLM customer service                           │
│        2. Reference EU261 regulation                             │
│        3. Provide flight details (TEST001, date, booking)        │
│        4. Expect response within 6 weeks                         │
│                                                                  │
│        💡 Notice how I remembered your previous flight!          │
└─────────────────────────────────────────────────────────────────┘
```

**Key Feature:** The bot remembers "TEST001" from the previous message thanks to Memory Bank!

---

## 🔒 Security & Compliance

### Data Protection
- ✅ **Model Armor** filters sensitive data (PII detection)
- ✅ **Firestore security rules** restrict access
- ✅ **Secret Manager** for API key storage
- ✅ **IAM service accounts** with least privilege

### Content Safety
- ✅ **Input validation** blocks prompt injections
- ✅ **Output filtering** ensures appropriate responses
- ✅ **Rate limiting** prevents abuse
- ✅ **Audit logging** tracks all requests

### Privacy
- ✅ **Anonymous sessions** by default (no user tracking)
- ✅ **Automatic cleanup** (sessions deleted after 7 days)
- ✅ **GDPR compliant** (data deletion on request)
- ✅ **No PII storage** in conversation logs

---

## 📊 Monitoring & Observability

### Cloud Logging
```bash
# View all logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Filter Memory Bank logs
gcloud logging read "textPayload=~'Memory Bank'" --limit 20

# Monitor errors
gcloud logging read "severity>=ERROR" --limit 10
```

### Firestore Metrics
- View in Cloud Console: [Firestore Dashboard](https://console.cloud.google.com/firestore)
- Track: Read/write operations, storage usage, active sessions

### Cloud Run Metrics
- View in Cloud Console: [Cloud Run Dashboard](https://console.cloud.google.com/run)
- Track: Request count, latency, CPU/memory usage, error rate

---

## 💰 Cost Estimation

### Per 10,000 Conversations

| Service | Usage | Cost |
|---------|-------|------|
| **Gemini 2.5 Flash** | 20K input tokens, 5K output | ~$0.20 |
| **Firestore** | 30K writes, 10K reads | ~$0.06 |
| **Cloud Run** | 10K requests (2Gi, 2 CPU) | ~$0.50 |
| **Secret Manager** | 10K accesses | ~$0.03 |
| **Model Armor** | 20K validations | ~$0.10 |
| **Total** | | **~$0.89** |

**Free Tier Includes:**
- Firestore: 50K reads/day, 20K writes/day
- Cloud Run: 2M requests/month
- Secret Manager: 10K accesses/month

**Most workloads fit within free tier!**

---

## 🐛 Troubleshooting

### Memory Bank Not Working
```bash
# Check Firestore API enabled
gcloud services list --enabled | grep firestore

# Verify IAM permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:ai-agent-sa@*"

# Test locally (with virtual environment activated)
source .venv/bin/activate
python tests/test_memory_bank.py
```

### Gemini API Errors
```bash
# Check API key is set locally
echo $GEMINI_API_KEY

# Verify Secret Manager access
gcloud secrets versions access latest --secret=gemini-api-key

# Verify Cloud Run secret configuration
gcloud run services describe claimjet-final \
  --region us-central1 \
  --format="yaml(spec.template.spec.containers[0].env)"

# If secret is not properly mounted, update the service:
gcloud run services update claimjet-final \
  --region us-central1 \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars GCP_PROJECT=qwiklabs-asl-03-7e6910d4e317
```

### Deployment Issues
```bash
# Check Cloud Run logs (for DelaySlayer)
gcloud run services logs read delayslayer --limit 50

# Check Cloud Run logs (for legacy ClaimJet services)
gcloud run services logs read claimjet-final --limit 50

# Describe service
gcloud run services describe delayslayer --region us-central1
```

---

## 🔄 Development Workflow

### Local Development
```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Set environment variables
export GEMINI_API_KEY="your-key"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
export GCP_PROJECT="your-project-id"

# 3. Run chatbot
python run.py

# 4. Test changes
python tests/test_memory_bank.py
```

### Build & Deploy
```bash
# 1. Build Docker image (DelaySlayer - latest)
docker build -t gcr.io/$PROJECT_ID/delayslayer:latest .

# 2. Test locally
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  gcr.io/$PROJECT_ID/delayslayer:latest

# 3. Push to GCR
docker push gcr.io/$PROJECT_ID/delayslayer:latest

# 4. Deploy to Cloud Run
gcloud run deploy delayslayer \
  --image gcr.io/$PROJECT_ID/delayslayer:latest \
  --region us-central1 \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest \
  --set-env-vars GCP_PROJECT=$PROJECT_ID
```

---

## 🤝 Contributing

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function parameters
- Add docstrings for all functions
- Keep functions focused and testable

### Testing
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run Memory Bank tests
python tests/test_memory_bank.py

# Test application locally
python run.py
```

---

## 📝 License

[Add your license here]

---

## 🎯 Roadmap

### Completed ✅
- [x] ADK integration with function calling
- [x] Memory Bank with Firestore persistence
- [x] Model Armor content safety
- [x] Cloud Run deployment with Secret Manager
- [x] Refactored package structure (v3.0)
- [x] Test flight data (TEST001, TEST002)
- [x] EU261 compensation calculator
- [x] Professional Python package layout
- [x] DelaySlayer production deployment (v1.0)

### Planned 🚧
- [ ] User authentication (Google Sign-In)
- [ ] Real flight API integration
- [ ] PDF report generation
- [ ] Email notifications
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Conversation export

---

## 📞 Support

**Project Information:**
- **Project ID:** qwiklabs-asl-03-7e6910d4e317
- **Region:** us-central1
- **Service Account:** ai-agent-sa@qwiklabs-asl-03-7e6910d4e317.iam.gserviceaccount.com

**Live Services:**
- **🎯 DelaySlayer (Production):** https://delayslayer-o2lrnifutq-uc.a.run.app
- **Legacy Services:** ClaimJet deployments available for reference

**Service Configuration:**
- **Latest Image:** gcr.io/qwiklabs-asl-03-7e6910d4e317/delayslayer:v1
- **Resources:** 1Gi RAM, 1 CPU
- **Timeout:** 300 seconds
- **Autoscaling:** 0-3 instances
- **Port:** 8080
- **Authentication:** Public (allow-unauthenticated)
- **Secrets:** GEMINI_API_KEY mounted from Secret Manager

**For Issues:**
1. Check logs: `gcloud logging read "resource.type=cloud_run_revision"`
2. Review documentation in this README
3. Test locally first before deploying

---

## 🎉 Acknowledgments

Built with:
- **Google Gemini 2.5 Flash** - Advanced LLM
- **Google ADK** - Agent Development Kit
- **Google Cloud Firestore** - NoSQL database
- **Google Model Armor** - Content safety
- **Gradio** - Web UI framework

---

**Status:** ✅ Production Ready  
**Last Updated:** March 17, 2026  
**Version:** DelaySlayer v1.0  
**Production URL:** https://delayslayer-o2lrnifutq-uc.a.run.app

---

**Note:** This project was formerly known as ClaimJet. All references have been updated to DelaySlayer, though the codebase folder structure remains unchanged for compatibility.
