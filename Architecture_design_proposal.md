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

### 4.2 Shared reasoning engine

Both products reuse the same backend logic:

1. intake and structure case
2. verify flight facts
3. evaluate EU261 eligibility
4. generate resolution and explanation

---

## 5. High-level architecture

```text
+-----------------------------+       +-----------------------------+
| DelaySlayer for Airlines    |       | DelaySlayer for Passengers  |
| KLM internal UI / CRM plug  |       | Schiphol web/app interface  |
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
                    | state machine + workflow      |
                    +---------------+---------------+
                                    |
              -------------------------------------------------------
              |                         |                          |
              v                         v                          v
+-------------------------+  +-------------------------+  +-------------------------+
| Agent 1                 |  | Agent 2                 |  | Agent 3                 |
| Intake & Structuring    |  | Flight Verification     |  | EU261 Eligibility       |
+-------------------------+  +-------------------------+  +-------------------------+
                                    |
                                    v
                         +-------------------------+
                         | Agent 4                 |
                         | Resolution & Explanation|
                         +-------------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Rule Engine / Policy Service  |
                    | eligibility tables, thresholds|
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Data Layer                    |
                    | case DB, audit log, evidence  |
                    +-------------------------------+
                                    |
                                    v
                    +-------------------------------+
                    | Manual Review Queue           |
                    | human escalation only         |
                    +-------------------------------+
```

---

## 6. Component specifications

### 6.1 Claims Orchestrator Service

**Responsibility:** Coordinate the end-to-end case lifecycle and state transitions.

**Key flows:**
- Intake → Structuring → Verification → Eligibility check → Resolution
- Conditional routing to manual review based on eligibility score or rule violations
- Event logging for each state transition

**State machine:**
```
INTAKE → STRUCTURING → FLIGHT_VERIFICATION → ELIGIBILITY_EVAL → 
  → RESOLUTION → COMPLETE / ESCALATED
```

---

### 6.2 Agent 1: Intake & Structuring

**Responsibility:** Parse unstructured complaint text and extract structured facts.

**Inputs:** complaint text, claimant info, flight details
**Outputs:** structured case JSON with:
- claimant identity and contact
- flight identifier (IATA code, date, route)
- claimed delay (hours)
- delay reason (if stated)
- evidence attachments

**Implementation:** LLM-driven extraction with confidence scoring. Fallback to manual review if confidence < 70%.

---

### 6.3 Agent 2: Flight Verification

**Responsibility:** Validate flight facts against authoritative data sources and detect extraordinary circumstances.

**Inputs:** structured case with flight identifiers
**Outputs:** verified flight data with:
- actual departure/arrival times
- scheduled times
- delay duration (calculated)
- reported cause (technical, weather, ATC, etc.)
- extraordinary circumstance flag

**Integration:** Query external flight database (IATA, airline ops) or rules DB. Flag unverifiable cases for escalation.

---

### 6.4 Agent 3: EU261 Eligibility

**Responsibility:** Apply deterministic rules to establish compensation entitlement.

**Inputs:** verified flight facts, claimant location
**Outputs:** eligibility decision with:
- delay >= 3 hours: YES/NO
- extraordinary circumstances exclusion: YES/NO
- passenger location (EU / non-EU)
- compensation amount (EUR)
- applicable exemptions

**Rule matrix:**
| Delay (hours) | EU261 eligible | Extraordinary | Compensation |
|---|---|---|---|
| < 3 | NO | — | €0 |
| 3–≤4 | YES | if not | €250 |
| > 4 | YES | if not | €400–€600 (by distance) |

---

### 6.5 Agent 4: Resolution & Explanation

**Responsibility:** Generate clear, user-appropriate decision narrative and next-action recommendations.

**Outputs by audience:**
- **For KLM staff:** decision summary, evidence chain, escalation triggers, compliance notes
- **For passengers:** plain-language eligibility statement, compensation estimate, next steps

**Templates:**
- eligible + simple: "You are entitled to €250 compensation. KLM will contact you within 14 days."
- ineligible + reason: "Your flight delay was caused by extraordinary circumstances (severe weather). EU261 does not apply."
- under review: "Your claim requires manual review. You will hear from us within 5 business days."

---

### 6.6 Rule Engine / Policy Service

**Responsibility:** Centralized, versionable repository of EU261 rules, KLM policy overrides, and thresholds.

**Stored rules:**
- delay thresholds and compensation tables
- extraordinary circumstance codes and descriptions
- exclusion criteria (e.g., connection losses, booked > 2 weeks prior)
- escalation rules (e.g., missing evidence, complex cases)

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
    "state": "INTAKE | STRUCTURING | FLIGHT_VERIFICATION | ELIGIBILITY_EVAL | RESOLUTION | COMPLETE | ESCALATED",
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
    "eligibility": {
      "delay_hours": "number",
      "meets_3h_threshold": "boolean",
      "extraordinary_circumstances": "boolean",
      "compensation_eur": "number",
      "confidence": "number (0-1)"
    },
    "decision": {
      "eligible": "boolean",
      "reason_code": "string",
      "narrative": "string",
      "recommended_action": "APPROVE | DENY | ESCALATE"
    }
  }
}
```

---

## 8. LLM reasoning pipeline

**Model:** Claude (or equivalent) for structured extraction and explanation generation.

**Prompting strategy:**
1. **Extraction:** Zero-shot prompting with JSON schema for fact extraction from complaints
2. **Verification:** Chain-of-thought to cross-check flight data and rule logic
3. **Explanation:** Few-shot examples of clear, compliant decision narratives

**Safeguards:**
- No direct compensation claims; all eligibility decisions flow through rule engine
- Confidence scoring on extractions; low confidence triggers escalation
- All outputs validated against rule engine output before presentation

---

## 9. API contracts

### 9.1 Create claim
```
POST /v1/claims
{
  "complaint_text": "string",
  "claimant": { "name", "email", "country" },
  "attachments": ["url"]
}
→ 202 { "case_id": "uuid", "status_url": "/cases/{id}" }
```

### 9.2 Get claim status
```
GET /v1/cases/{id}
→ 200 { "state", "eligibility", "decision", "next_steps" }
```

### 9.3 (KLM internal) Escalate to manual review
```
POST /v1/cases/{id}/escalate
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

**Tech stack:**
- Backend: Node.js / Python + async workers
- Database: PostgreSQL (cases, audit) + Redis (cache)
- LLM: Claude API via inference service
- Message queue: optional event streaming for async workflows

**Scaling:**
- API Gateway: horizontal autoscaling on CPU/memory
- Agents: async queue workers, scale on backlog depth
- Database: read replicas for reporting

**Monitoring:**
- Case decision latency SLA: p95 < 5 seconds for intake + structuring
- Manual escalation rate: target < 5% of cases
- Audit log completeness: 100% (enforced at DB layer)

---

## 12. Testing strategy

### 12.1 Unit tests
- LLM extraction accuracy on 50+ real complaint samples
- Rule engine matrix coverage (all delay/circumstance combinations)
- State machine transitions (happy path + edge cases)

### 12.2 Integration tests
- End-to-end claim lifecycle (intake → resolution)
- Flight verification with mock data sources
- Rule engine + LLM consistency (decisions match expected outcomes)

### 12.3 Compliance tests
- GDPR data retention and deletion
- audit logging completeness
- decision explainability (staff can trace every rule applied)

---

## 13. Risks & mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| LLM hallucination damages claim accuracy | HIGH | Confidence scoring; systematic prompt validation; human review threshold |
| Rule changes break historical decision reproducibility | MEDIUM | Immutable rule versioning; audit trail; test suite before deployment |
| High manual escalation rate blocks workflow | MEDIUM | Progressive confidence threshold tuning; escalation SLA monitoring |
| Data loss or audit log corruption | HIGH | encrypted backups; read-only audit table; point-in-time recovery testing |
| False negatives (system denies eligible passengers) | CRITICAL | Conservative thresholds; passenger appeal channel; periodic decision audits |

---

## 14. Success metrics

- **Automation rate:** > 85% of cases resolved without manual intervention
- **Decision consistency:** inter-rater agreement > 95% (staff review audit sample)
- **Passenger satisfaction:** NPS > 50 on eligible claim resolution
- **Operational efficiency:** average case decision time < 2 minutes
- **Compliance:** zero audit findings on decision traceability

---

## 15. Future roadmap

- **Phase 2:** cancellation and denied-boarding workflows (same architecture)
- **Phase 3:** multi-language support and regional policy variants
- **Phase 4:** passenger appeal workflow with structured evidence collection
- **Phase 5:** regulatory reporting dashboards (EU transparency requirements)

