# DelaySlayer Technical Design
**AI-powered flight delay complaint handling built on EU 261/2004**  
**Products:** DelaySlayer for Airlines (KLM internal moderation assistant), DelaySlayer for Passengers (Schiphol-facing eligibility app)

---

## 1. Purpose

DelaySlayer is a shared AI + rules engine that evaluates flight delay complaints and passenger eligibility guidance under EU 261/2004. The same reasoning core powers:

- an **airline-facing moderation workflow** for KLM support/claims teams
- a **passenger-facing self-service workflow** for Schiphol travelers

EU 261/2004 establishes common EU rules on compensation and assistance for denied boarding, cancellation, and long delay of flights. Public EU passenger-rights guidance states that passengers may be entitled to compensation when they reach their final destination with a delay of **3 hours or more**, unless the delay was caused by extraordinary circumstances. KLM’s public policy describes similar criteria for delayed-flight compensation. 

---

## 2. Goals

### 2.1 Business goals

- reduce manual complaint triage workload
- provide faster and more consistent first-pass decisions
- make passenger rights easier to understand
- standardize reasoning and evidence collection
- create auditable decision records

### 2.2 Technical goals

- use a single shared eligibility engine across two products
- keep the architecture hackathon-feasible but production-oriented
- separate **LLM understanding** from **deterministic legal/rule evaluation**
- support explainable outputs for staff and passengers
- avoid direct payment or refund execution in MVP

### 2.3 Non-goals

- actual payment processing
- direct refund settlement
- baggage claims
- denied boarding and cancellation handling in MVP
- full appeals workflow
- full legal adjudication of complex edge cases

---

## 3. Core design principle

## **LLM for understanding, rules for entitlement, templates for action**

The system should use:
- an LLM to parse unstructured complaints and generate explanations
- deterministic business rules for EU 261 screening
- workflow state and evidence logs for operational control

This is required because eligibility decisions should remain grounded in explicit legal and policy checks, not free-form model judgment.  [oai_citation:1‡EUR-Lex](https://eur-lex.europa.eu/eli/reg/2004/261/oj/eng?utm_source=chatgpt.com)

---

## 4. System context

### 4.1 Two products, one engine

- **DelaySlayer for Airlines**  
  Internal complaint moderation assistant for KLM support teams

- **DelaySlayer for Passengers**  
  Passenger eligibility guidance app linked from Schiphol channels

### 4.2 Shared reasoning engine with divergent workflows

Both products reuse the same flight verification and eligibility evaluation logic, but diverge at the decision point:

**Airlines workflow:**
1. User fills complaint form
2. Flight verification and delay calculation
3. EU261 eligibility evaluation with confidence scoring
4. Decision routing: high confidence → automated email; low confidence → human moderation

**Passengers workflow:**
1. User talks with chatbot
2. Flight verification and delay calculation
3. EU261 eligibility evaluation
4. Decision routing: eligible → redirect to airline page; ineligible → return conclusion

---

## 5. High-level architecture and workflow

### 5.1 System component diagram

```text
+-----------------------------+       +-----------------------------+
| DelaySlayer for Airlines    |       | DelaySlayer for Passengers  |
| KLM internal UI / CRM plug  |       | Schiphol chatbot interface  |
+-------------+---------------+       +-------------+---------------+
              |                                     |
              +------------------+  +---------------+
                                 |  |
                                 v  v
                    +-------------------------------+
                    | API Gateway / App Backend     |
                    | Auth, rate limit, request ID  |
                    +---------------+---------------+
                                    |
                                    v
                    +-------------------------------+
                    | Claims Orchestrator Service   |
                    | state machine + routing       |
                    +---------------+---------------+
                                    |
                    +-------------------+-------------------+
                    |                                       |
                    v                                       v
        +------------------------+            +------------------------+
        | Airlines Workflow       |            | Passengers Workflow     |
        | (Complaint moderation)  |            | (Eligibility guidance)  |
        +------------------------+            +------------------------+
                    |                                       |
                    +-------------------+-------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Agent: flight_verify          |
                    | Flight data + delay calc      |
                    +---------------+---------------+
                                    |
                                    v
                    +-------------------------------+
                    | Rule Engine: EU261 Eligibility|
                    | Evaluate eligibility & score  |
                    +---------------+---------------+
                                    |
                    +-------------------+-------------------+
                    |                                       |
                    v                                       v
        +------------------------+            +------------------------+
        | Agent: refund_decision  |            | Eligibility Result      |
        | (Airlines: email/review)|            | (Passengers: redirect)  |
        +------------------------+            +------------------------+
                    |                                       |
                    v                                       v
        +------------------------+            +------------------------+
        | Email Service /         |            | Redirect to Airline     |
        | Manual Review Queue     |            | Official Page           |
        +------------------------+            +------------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Data Layer                    |
                    | case DB, audit log, evidence  |
                    +-------------------------------+
```

### 5.2 Agent workflow flowchart

```flowchart
graph TD
    A([Start]) --> B{User type}

    %% Airlines branch
    B -->|Airlines| C[User fills in complaint form]
    C --> D[Agent `flight_verify` calls API with `flight_number` and `flight_date`]
    D --> E[Calculate delay time if flight is delayed]
    E --> F[Evaluate refund eligibility and return confidence score]
    F --> G{Confidence score > 80?}
    G -->|Yes| H[Agent `refund_decision` sends email to user]
    G -->|No| I[Agent `refund_decision` invokes human moderation]

    %% Passengers branch
    B -->|Passengers| J[User talks with chatbot]
    J --> K[Agent `flight_verify` calls API with `flight_number` and `flight_date`]
    K --> L[Calculate delay time if flight is delayed]
    L --> M[Evaluate refund eligibility and return result]
    M --> N{Meets refund conditions?}
    N -->|Yes| O[Redirect user to corresponding airline official complaint page]
    N -->|No| P[Return conclusion to user]
```

---

## 6. Component specifications

### 6.1 Claims Orchestrator Service

**Responsibility:** Coordinate the end-to-end case lifecycle and route requests to the appropriate workflow (Airlines vs Passengers).

**Key flows:**
- **Airlines:** Intake → Flight Verification → Eligibility Evaluation → Refund Decision (email or escalation)
- **Passengers:** Chatbot query → Flight Verification → Eligibility Evaluation → Redirect or conclusion
- Event logging for each state transition
- Conditional routing based on user type and eligibility score

**State machine:**
```
INTAKE → FLIGHT_VERIFICATION → ELIGIBILITY_EVAL → 
  → REFUND_DECISION → COMPLETE / ESCALATED / REDIRECTED
```

---

### 6.2 Agent: flight_verify

**Responsibility:** Validate flight facts, calculate delay, and evaluate EU261 eligibility. Returns both the verified data and eligibility score.

**Inputs:** 
- flight identifier (IATA code, date, route)
- claimant country (for EU jurisdiction check)

**Outputs:** 
```json
{
  "verified_flight_data": {
    "actual_departure": "ISO8601",
    "scheduled_departure": "ISO8601",
    "delay_hours": "number",
    "reported_cause": "string"
  },
  "eligibility_result": {
    "meets_3h_threshold": "boolean",
    "extraordinary_circumstances": "boolean",
    "compensation_eur": "number",
    "confidence_score": "number (0-1)"
  }
}
```

**Process:**
1. Call Aviationstack API with flight number, date, and route
2. Extract `scheduled_departure`, `actual_departure`, and `status`
3. Calculate delay in hours
4. Apply EU261 rule matrix to determine eligibility
5. Generate confidence score based on data completeness and matching certainty
6. Flag unverifiable cases (missing flight records, API errors) for escalation

**Integration:** Aviationstack API (enterprise plan)
- Cache flight records for 1 hour to minimize API calls (quota: 100k/month)
- Fallback to scheduled times if actual times unavailable; adjust confidence accordingly

---

### 6.3 Agent: refund_decision

**Responsibility:** Route the eligibility decision to appropriate next steps based on user type and confidence level.

**Inputs:**
- user_type: "AIRLINE" | "PASSENGER"
- eligibility_result from `flight_verify`
- claimant contact info (for email dispatch)

**Outputs (depends on user_type):**

**For Airlines (confidence > 80%):**
- Send automated email to claimant with compensation offer and EU261 justification
- Log decision to audit trail

**For Airlines (confidence ≤ 80%):**
- Create manual review ticket
- Route to KLM claims queue with evidence summary
- Notify claims team via dashboard

**For Passengers (eligible):**
- Generate eligibility confirmation
- Provide redirect URL to KLM official complaint page with pre-filled flight details
- Log consent and redirect event

**For Passengers (ineligible):**
- Generate plain-language explanation (e.g., "Your flight was delayed by 2 hours; EU261 requires 3+ hours for compensation")
- Provide additional help resources or appeal instructions

---

### 6.4 Rule Engine / Policy Service

**Responsibility:** Centralized, versionable repository of EU261 rules and KLM policy thresholds.

**Stored rules:**
- delay thresholds and compensation tables
- extraordinary circumstance codes and descriptions
- confidence score thresholds for automated vs escalated decisions
- escalation rules (e.g., missing evidence, API failures)

**Eligibility rule matrix:**
| Delay (hours) | EU261 eligible | Extraordinary | Compensation |
|---|---|---|---|
| < 3 | NO | — | €0 |
| 3–≤4 | YES | if not | €250 |
| > 4 | YES | if not | €400–€600 (by distance) |

**Interface:** RESTful rule lookup service; audit trail on all rule changes.

---

### 6.7 Data Layer

**Entities:**
- `cases`: primary claim records with state, timestamps, resolved decision
- `case_evidence`: attachments, screenshots, flight records
- `audit_log`: all state transitions, rule evaluations, manual interventions
- `rule_versions`: historical rule snapshots for decision reproducibility

**Retention:** cases indefinitely (EU legal hold); audit logs 7+ years.

---

## 7. Data model sketch

```json
{
  "case": {
    "id": "uuid",
    "created_at": "ISO8601",
    "user_type": "AIRLINE | PASSENGER",
    "state": "INTAKE | FLIGHT_VERIFICATION | ELIGIBILITY_EVAL | REFUND_DECISION | COMPLETE | ESCALATED | REDIRECTED",
    "claimant": {
      "name": "string",
      "email": "string",
      "country": "ISO3166"
    },
    "flight": {
      "iata_code": "string",
      "scheduled_departure": "ISO8601",
      "actual_departure": "ISO8601",
      "route": "IATA-IATA"
    },
    "flight_verification": {
      "delay_hours": "number",
      "actual_departure": "ISO8601",
      "scheduled_departure": "ISO8601",
      "reported_cause": "string"
    },
    "eligibility": {
      "meets_3h_threshold": "boolean",
      "extraordinary_circumstances": "boolean",
      "compensation_eur": "number",
      "confidence_score": "number (0-1)"
    },
    "decision": {
      "type": "APPROVED | DENIED | ESCALATED | REDIRECTED",
      "reason_code": "string",
      "narrative": "string",
      "user_type_action": {
        "AIRLINE": "EMAIL | MANUAL_REVIEW",
        "PASSENGER": "REDIRECT | CONCLUSION"
      }
    }
  }
}
```

---

## 8. Agent implementation strategy

### 8.1 Agent: flight_verify

**Implementation approach:**
- Deterministic flight data retrieval from Aviationstack API
- Rule-engine-based EU261 eligibility evaluation (no LLM)
- Confidence scoring based on:
  - Data completeness (actual vs. estimated times)
  - Flight record match certainty
  - API response quality

**Process:**
1. Validate flight identifiers and date format
2. Query Aviationstack `/flights` endpoint
3. Parse response: extract `scheduled_departure`, `actual_departure`, `status`
4. Calculate `delay_hours = (actual_departure - scheduled_departure) / 60 minutes`
5. Apply rule matrix:
   - If delay_hours >= 3 AND no extraordinary circumstances → ELIGIBLE
   - If delay_hours < 3 → INELIGIBLE
   - Extraordinary circumstances detected → FLAG for review
6. Generate confidence score (0-1 scale):
   - 1.0 = confirmed actual times
   - 0.8 = using estimated times
   - 0.5 = partial data, API errors
7. Return structured result

### 8.2 Agent: refund_decision

**Implementation approach:**
- Stateless decision dispatcher
- Template-based action generation
- User-type-aware routing

**For Airlines (internal moderation):**
- If confidence_score > 0.8 AND eligible: send automated email with compensation offer
- If confidence_score ≤ 0.8 OR edge cases: create manual review ticket and notify claims team
- Always log decision and send confirmation email to claimant

**For Passengers (public-facing guidance):**
- If eligible: generate eligibility confirmation and redirect URL to KLM complaints page
- If ineligible: generate plain-language explanation with reason code
- Log interaction for compliance audit

---

## 9. API contracts

### 9.1 Airlines workflow: Create complaint claim
```
POST /v1/airlines/claims
{
  "complaint_text": "string",
  "claimant": { "name", "email", "country" },
  "flight_number": "string",
  "flight_date": "ISO8601",
  "attachments": ["url"]
}
→ 202 { "case_id": "uuid", "status_url": "/claims/{id}" }
```

### 9.2 Passengers workflow: Chat query
```
POST /v1/passengers/eligibility-check
{
  "flight_number": "string",
  "flight_date": "ISO8601",
  "claimant": { "email": "string", "country": "ISO3166" }
}
→ 200 {
  "eligible": "boolean",
  "compensation_eur": "number",
  "redirect_url": "string | null",
  "explanation": "string"
}
```

### 9.3 Get case status (Airlines)
```
GET /v1/airlines/claims/{id}
→ 200 {
  "state": "string",
  "eligibility": { ... },
  "decision_action": "EMAIL | MANUAL_REVIEW",
  "next_steps": "string"
}
```

### 9.4 (KLM internal) Escalate to manual review
```
POST /v1/airlines/claims/{id}/escalate
{ "reason": "string", "priority": "HIGH | NORMAL" }
→ 200 { "escalated_to": "queue_id" }
```

---

## 10. Security & compliance

- **Authentication:** OAuth 2.0 + SAML for KLM staff; JWT for passenger sessions
- **Data protection:** GDPR compliance; PII encryption at rest; audit logging of all access
- **Rate limiting:** 10 req/sec per IP; burst capacity 50 req/min
- **Validation:** all inputs sanitized; SQL/prompt injection guards
- **Legal hold:** immutable audit trail; read-only access to completed cases

---

## 11. Deployment & operations

**Platform:** Google Cloud Run (serverless, auto-scaling containers)

**Tech stack:**
- Backend: Node.js / Python + async workers (Cloud Run services)
- Database: Cloud SQL PostgreSQL (cases, audit) + Memorystore Redis (cache)
- LLM: Claude API via inference service
- Message queue: Cloud Tasks or Pub/Sub for async workflows
- External APIs: Aviationstack (flight data), Claude API

**Cloud Run configuration:**
- API Gateway on Cloud Run (autoscale 0–100 instances, CPU: 2, memory: 2GB)
- Claims Orchestrator on Cloud Run (autoscale 1–50 instances, CPU: 2, memory: 4GB)
- Agents (flight-verify, refund-decision) on Cloud Run (autoscale 1–20 instances per agent, CPU: 2, memory: 2GB)
- Cloud SQL connection pooling via Cloud SQL Auth proxy
- Logging to Cloud Logging; structured JSON logs for audit trail

**Scaling & resilience:**
- Cloud Run auto-scales on CPU and request latency
- Cloud SQL high-availability with automated failover
- Redis cluster mode for cache failover

**Monitoring:**
- Cloud Monitoring dashboards: request latency, error rate, agent execution time
- Case decision latency SLA: p95 < 2 seconds for flight_verify + refund_decision
- Manual escalation rate: target < 5% of cases (Airlines workflow)
- Redirect rate: target > 80% of passenger queries
- Audit log completeness: 100% (enforced at DB layer)
- Alerting on Aviationstack API quota usage, API errors

---

## 12. Codebase structure

```
claimjet/
├── docker-compose.yml                # Local dev environment
├── README.md                          # Project overview
├── package.json / requirements.txt    # Dependencies
├── .env.example                       # Environment template
│
├── src/
│   ├── main.ts                        # Application entry point
│   ├── config/
│   │   ├── env.ts                     # Environment validation
│   │   ├── constants.ts               # Shared constants
│   │   └── cloud-run.ts               # Cloud Run config
│   │
│   ├── controllers/
│   │   ├── airlines.controller.ts      # POST /airlines/claims, POST /airlines/claims/{id}/escalate
│   │   ├── passengers.controller.ts    # POST /passengers/eligibility-check
│   │   └── health.controller.ts        # Health checks
│   │
│   ├── services/
│   │   ├── claims-orchestrator.service.ts  # Routes to airline/passenger workflows
│   │   ├── airline-workflow.service.ts     # Complaint moderation flow
│   │   ├── passenger-workflow.service.ts   # Eligibility guidance flow
│   │   └── external/
│   │       ├── aviationstack.service.ts    # Flight verification API client
│   │       ├── email.service.ts            # Email dispatch
│   │       └── cache.service.ts            # Redis operations
│   │
│   ├── agents/
│   │   ├── flight-verify/
│   │   │   ├── flight-verify.agent.ts      # Flight API + eligibility evaluation
│   │   │   ├── aviationstack.adapter.ts    # Aviationstack API client
│   │   │   ├── rules.engine.ts             # EU261 rule matrix evaluation
│   │   │   ├── confidence.calculator.ts    # Confidence scoring logic
│   │   │   └── flight-verify.test.ts
│   │   └── refund-decision/
│   │       ├── refund-decision.agent.ts    # Decision routing by user type
│   │       ├── email.dispatcher.ts         # Email service for airlines
│   │       ├── redirect.generator.ts       # Redirect URL generation for passengers
│   │       ├── templates/
│   │       │   ├── eligible-email.hbs
│   │       │   ├── ineligible-conclusion.hbs
│   │       │   └── escalation-notice.hbs
│   │       └── refund-decision.test.ts
│   │
│   ├── models/
│   │   ├── case.model.ts              # Case entity + schema
│   │   ├── evidence.model.ts          # Evidence attachments
│   │   └── audit-log.model.ts         # Audit trail
│   │
│   ├── repositories/
│   │   ├── case.repository.ts         # DB operations: cases, evidence
│   │   ├── audit.repository.ts        # Audit log operations
│   │   └── rule.repository.ts         # Rule versioning
│   │
│   ├── middleware/
│   │   ├── auth.middleware.ts         # OAuth/SAML + JWT verify
│   │   ├── logger.middleware.ts       # Request/response logging
│   │   ├── error-handler.middleware.ts
│   │   └── rate-limit.middleware.ts
│   │
│   ├── utils/
│   │   ├── validators.ts              # Input sanitization
│   │   ├── error-codes.ts             # Standardized error codes
│   │   └── delay-calculator.ts        # Delay hour calculations
│   │
│   └── types/
│       ├── case.types.ts              # TypeScript interfaces
│       ├── agents.types.ts
│       └── api.types.ts
│
├── infra/
│   ├── terraform/
│   │   ├── main.tf                    # Cloud Run, Cloud SQL, Memorystore
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── modules/
│   │       ├── cloud-run/
│   │       ├── cloud-sql/
│   │       └── redis/
│   ├── cloudbuild.yaml                # CI/CD pipeline
│   └── docker/
│       ├── Dockerfile                 # Multi-stage build
│       └── .dockerignore
│
├── migrations/
│   ├── 001_init_cases_table.sql
│   ├── 002_init_evidence_table.sql
│   ├── 003_init_audit_log_table.sql
│   └── 004_init_rules_table.sql
│
├── tests/
│   ├── unit/
│   │   ├── agents/
│   │   ├── services/
│   │   └── utils/
│   ├── integration/
│   │   ├── claims-flow.test.ts
│   │   ├── agent-chain.test.ts
│   │   └── db.fixtures.ts
│   ├── e2e/
│   │   ├── api.e2e.test.ts
│   │   └── cloud-run.test.ts
│   └── fixtures/
│       ├── sample-complaints.json
│       ├── mock-flight-data.json
│       └── mock-rules.json
│
├── docs/
│   ├── ARCHITECTURE.md                # High-level design (links to design doc)
│   ├── API.md                         # API endpoint documentation
│   ├── SETUP.md                       # Local dev environment
│   ├── DEPLOYMENT.md                  # Cloud Run deployment guide
│   ├── AGENTS.md                      # Agent implementation guide
│   └── RULES.md                       # EU261 rules reference
│
└── scripts/
    ├── bootstrap.sh                   # Set up local dev DB
    ├── seed-rules.sh                  # Load rule fixtures
    └── test-flight-api.sh             # Debug Aviationstack API
```

**Key principles:**

1. **Separation of concerns:** Controllers → Services → Agents/Rules → Repositories
2. **Modular agents:** Each agent is self-contained (logic, tests, schemas)
3. **No business logic in controllers:** Controllers delegate to services
4. **Immutable audit trail:** All decisions logged; audit repo is read-only after commit
5. **Type safety:** TypeScript interfaces enforce contracts between layers
6. **External service isolation:** Adapters (Aviationstack, Claude) are swappable
7. **Configuration as code:** All env/secrets via Cloud Run, passed at runtime
8. **Infrastructure as code:** Terraform modules for reproducible deployment
9. **Test coverage by layer:** Unit (agents, rules), integration (flows), E2E (API)
10. **Documentation co-located:** `docs/` folder parallels src structure

**Dependency flow (acyclic):**
```
API Requests
    ↓
Controllers (request validation)
    ↓
Services (business logic + orchestration)
    ↓
Agents (LLM/rule evaluation)
    ↓
Repositories (data access)
    ↓
PostgreSQL / Redis
```

**Technology recommendations:**
- **Language:** TypeScript (strong types, Node.js async/await)
- **Framework:** Express / Fastify (lightweight, Cloud Run optimized)
- **ORM:** Prisma or SQLAlchemy (type-safe, migration-friendly)
- **Testing:** Jest (unit), Supertest (integration), Playwright (E2E)
- **Linting:** ESLint + Prettier (code consistency)
- **Git:** conventional commits, branch protection on main

---

## 13. Testing strategy

### 13.1 Unit tests
- **flight_verify agent:** Flight API integration with mock data; rule matrix coverage (all delay thresholds); confidence scoring logic
- **refund_decision agent:** Decision routing by user type (airline vs passenger); email template rendering; redirect URL generation
- Rule engine: all EU261 eligibility combinations (delay, extraordinary circumstances)

### 13.2 Integration tests
- **Airline workflow:** complaint intake → flight_verify → eligibility → refund_decision (email path)
- **Airline workflow (escalation):** low confidence score → refund_decision (manual review path)
- **Passenger workflow:** eligibility check query → flight_verify → eligibility → refund_decision (redirect path)
- Flight verification with mock Aviationstack responses
- Email dispatch and redirect URL generation

### 13.3 Compliance tests
- GDPR data retention and deletion policies
- Audit logging completeness: all decisions logged with reasoning
- Decision explainability: KLM staff can trace every rule applied
- Confidence score accuracy and calibration

---

## 14. Risks & mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| Aviationstack API quota exceeded or service outage | MEDIUM | Cache flight data; graceful fallback to escalation; quota monitoring |
| Rule changes break historical decision reproducibility | MEDIUM | Immutable rule versioning; audit trail; test suite before deployment |
| High manual escalation rate (airlines) blocks workflow | MEDIUM | Confidence threshold tuning; SLA monitoring; escalation queue management |
| Passenger confusion on eligibility (low confidence redirect) | MEDIUM | Clear explanation templates; help resources; appeal channel |
| Data loss or audit log corruption | HIGH | Encrypted backups; read-only audit table; point-in-time recovery testing |
| False negatives (system denies eligible passengers) | CRITICAL | Conservative thresholds; regular decision audits; passenger appeal process |

---

## 15. Success metrics

### Airlines workflow
- **Automation rate:** > 85% of cases resolved without manual intervention (confidence > 80%)
- **Manual escalation rate:** < 15% of cases
- **Decision consistency:** inter-rater agreement > 95% on sample audits
- **Case decision latency:** p95 < 2 seconds (flight_verify + refund_decision)
- **Email delivery success:** > 99% of automated emails delivered

### Passengers workflow
- **Eligibility guidance accuracy:** > 95% match with manual review
- **Redirect successful:** > 80% of eligible passengers successfully redirected
- **User satisfaction:** NPS > 50 on eligibility guidance
- **Query response latency:** < 1 second average

### Overall
- **Operational efficiency:** average case decision time < 2 minutes (airlines)
- **Compliance:** zero audit findings on decision traceability
- **Aviationstack API uptime:** > 99.5%

---

## 16. Future roadmap

- **Phase 2:** cancellation and denied-boarding workflows (same architecture)
- **Phase 3:** multi-language support and regional policy variants
- **Phase 4:** passenger appeal workflow with structured evidence collection
- **Phase 5:** regulatory reporting dashboards (EU transparency requirements)

