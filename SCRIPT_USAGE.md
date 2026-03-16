# Flight Delay Analysis Scripts - Usage Guide

## Overview
Two complementary Python scripts for analyzing flight delays and evaluating EU 261/2004 compensation eligibility:

1. **test_api.py** - Flight search and analysis interface
2. **eu261_decision_rule.py** - EU 261/2004 compensation logic engine

---

## Script 1: test_api.py

### Purpose
Interactive script that accepts user input for flight date and flight number, retrieves flight data, and evaluates EU 261/2004 compensation eligibility.

### Input Parameters
Users are prompted for:
- **Flight Date** (format: YYYY-MM-DD, e.g., `2026-03-17`)
- **Flight Number** (numeric only, e.g., `1605` or `4929`)

### Data Sources (in priority order)
1. **Local API Results File** (`api_results.json`) - Used first if available
2. **Aviation Stack API** - Fallback if local file not available

### Usage

```bash
# Activate virtual environment
source venv/bin/activate

# Run the script
python aviationstack/test_api.py
```

### Interactive Session Example
```
FLIGHT DELAY ANALYSIS - EU 261/2004 Compensation Checker
==============================================================

Enter flight date (YYYY-MM-DD, e.g., 2026-03-17): 2026-03-17
Enter flight number (e.g., 4929 or 1605): 1605

📂 Found local data file. Loading...
✓ Found 1 flight(s) from local file

FLIGHT DETAILS
==============================================================
Date: 2026-03-17
IATA Code: NH1605
Flight Number: 1605
Status: scheduled
Airline: ANA (NH)

DEPARTURE:
  Airport: Itami (ITM)
  Scheduled: 2026-03-17T10:00:00+00:00
  Delay: 300 min

ARRIVAL:
  Airport: Kochi (KCZ)
  Scheduled: 2026-03-17T10:45:00+00:00
  Delay: 320 min

EU 261/2004 ANALYSIS FOR FLIGHT 1:
Status: PENDING
Arrival Delay: 320 minutes (threshold: 180 min)
Decision: Flight has not yet arrived at final destination...
```

### Output
- Flight details (departure, arrival, airline, status)
- EU 261/2004 eligibility determination
- Compensation amount (if applicable)
- Clear explanation of decision logic

---

## Script 2: eu261_decision_rule.py

### Purpose
Standalone engine for evaluating flight delay compensation eligibility under EU 261/2004 regulations.

### Key Rules Implemented
- **Eligibility Threshold**: Arrival delay ≥ 3 hours (180 minutes)
- **Extraordinary Circumstances**: Exempts compensation (weather, strikes, security, etc.)
- **Compensation Tiers**:
  - €250 for flights ≤1,500 km
  - €400 for flights 1,500–3,500 km
  - €600 for flights >3,500 km

### Usage as Standalone Script

```bash
python aviationstack/eu261_decision_rule.py
```

This loads `api_results.json` and displays analysis for the flight in that file.

### Usage as Imported Module

```python
from eu261_decision_rule import EU261DecisionRule

# flight_data is a dict from the API response
engine = EU261DecisionRule(flight_data)

# Evaluate eligibility
result = engine.evaluate(
    is_extraordinary_circumstance=False,
    flight_distance_km=850  # optional
)

# Access results
print(result.status)  # EligibilityStatus.ELIGIBLE, NOT_ELIGIBLE, or PENDING
print(result.delay_minutes)
print(result.compensation_amount_eur)
print(result.reason)  # Human-readable explanation
```

### Decision Output States

| Status | Meaning | When It Occurs |
|--------|---------|----------------|
| `PENDING` | Cannot determine yet | Flight hasn't arrived, arrival delay unknown |
| `ELIGIBLE` | Entitled to compensation | Arrival delay ≥ 180 min, no extraordinary circumstances |
| `NOT_ELIGIBLE` | No compensation due | Delay < 180 min, or extraordinary circumstances apply |

---

## API Result Format

Expected JSON structure for `api_results.json`:

```json
{
  "pagination": {
    "limit": 100,
    "offset": 0,
    "count": 1,
    "total": 1
  },
  "data": [
    {
      "flight_date": "2026-03-17",
      "flight_status": "scheduled",
      "departure": {
        "airport": "Itami",
        "iata": "ITM",
        "delay": 300,
        "scheduled": "2026-03-17T10:00:00+00:00"
      },
      "arrival": {
        "airport": "Kochi",
        "iata": "KCZ",
        "delay": 320,
        "scheduled": "2026-03-17T10:45:00+00:00"
      },
      "airline": {
        "name": "ANA",
        "iata": "NH"
      },
      "flight": {
        "number": "1605",
        "iata": "NH1605"
      }
    }
  ]
}
```

---

## Configuration

### Aviation Stack API
- **Endpoint**: `https://api.aviationstack.com/v1/flights`
- **API Key**: Stored in `test_api.py` (update as needed)
- **Parameters**:
  - `flight_date`: YYYY-MM-DD format
  - `flight_number`: Numeric flight number
  - `access_key`: Your API key

---

## Error Handling

The scripts include handling for:
- Invalid date format
- Missing API data
- Network connectivity issues
- File not found errors
- JSON parsing errors

All errors display helpful messages guiding the user on next steps.

---

## Integration with DelaySlayer

These scripts are designed to be integrated into the DelaySlayer system:
- **Modular Design**: EU261DecisionRule can be imported independently
- **Clear Output**: Human-readable explanations for both staff and passengers
- **Audit Trail**: Decision logic is explicit and documented
- **Extensible**: Easy to add new rules or compensationmodels

