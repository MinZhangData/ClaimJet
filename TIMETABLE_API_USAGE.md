# Flight Delay Analysis Scripts - Timetable API Guide

## Overview
Three complementary Python scripts for analyzing flight delays using Aviation Stack **Timetable API** and evaluating EU 261/2004 compensation eligibility:

1. **fetch_api_data.py** - Aviation Stack Timetable data fetcher
2. **test_api.py** - Flight search and analysis interface
3. **eu261_decision_rule.py** - EU 261/2004 compensation logic engine

---

## Quick Workflow

```bash
# Step 1: Fetch timetable data and save to api_results.json
python aviationstack/fetch_api_data.py
# → Select option (e.g., 3 for JFK arrivals)
# → Data saves to api_results.json

# Step 2: Search and analyze flights from the saved data
python aviationstack/test_api.py
# → Enter flight number to search
# → Get EU 261/2004 compensation analysis
```

---

## Script 1: fetch_api_data.py

### Purpose
Fetches flight timetable data from Aviation Stack `/timetable` endpoint and saves complete response to `api_results.json` for offline analysis.

### API Endpoint
- **URL**: `https://api.aviationstack.com/v1/timetable`
- **Parameters**:
  - `type`: `arrival` or `departure` (required)
  - `iataCode`: Optional IATA airport code filter (e.g., `JFK`)
  - `icaoCode`: Optional ICAO airport code filter (e.g., `KJFK`)
  - `access_key`: Your Aviation Stack API key

### Usage

```bash
source venv/bin/activate
python aviationstack/fetch_api_data.py
```

### Interactive Menu

```
Fetch options:
1. Fetch arrival timetables (no filters)
2. Fetch departure timetables (no filters)
3. Fetch arrivals for specific IATA airport code
4. Fetch departures for specific IATA airport code
5. Exit

Select option (1-5): 3
Enter IATA airport code (e.g., JFK): JFK
```

### Example Output
```
🌐 Fetching arrival timetable data from Aviation Stack API...
   IATA Code: JFK

✓ Successfully fetched 100 flight(s)
  Pagination Info:
    - Limit: 100
    - Total Available: 1669022
    - Offset: 0
    - Count: 100

💾 Data saved to: /path/to/api_results.json
   File size: 523.4 KB

✓ Data fetch and save completed successfully!
```

---

## Script 2: test_api.py

### Purpose
Interactive script for searching flights by flight number and analyzing EU 261/2004 compensation eligibility.

### Input
- **Flight Number**: Numeric flight number (e.g., `4511`, `1605`)

### Data Sources (priority order)
1. **Local API Results File** (`api_results.json`)
2. **Aviation Stack Timetable API** (arrival timetables)

### Usage

```bash
source venv/bin/activate
python aviationstack/test_api.py
```

### Example Session

```
FLIGHT DELAY ANALYSIS - EU 261/2004 Compensation Checker
==============================================================

Search by flight NUMBER from loaded timetable data:
Enter flight number (e.g., 4511): 4511

📂 Found local data file. Loading from api_results.json...
✓ Found 2 flight(s) from local file

======================================================================
FLIGHT DETAILS
======================================================================
IATA Code: AV4511
Flight Number: 4511
Status: scheduled
Type: arrival
Airline: SA AVIANCA (AV)

DEPARTURE:
  Airport: TPE (RCTP)
  Terminal: 2
  Gate: C4
  Scheduled: 2024-06-18T19:10:00.000
  Actual: 2024-06-18T20:46:00.000
  Delay: 97 min

ARRIVAL:
  Airport: JFK (KJFK)
  Terminal: 1
  Gate: 3
  Scheduled: 2024-06-18T22:05:00.000
  Actual: 2024-06-18T14:15:22Z
  Delay: 65 min
======================================================================

EU 261/2004 ANALYSIS FOR FLIGHT 1:
Status: NOT_ELIGIBLE
Arrival Delay: 65 minutes (threshold: 180 min)

Decision: Arrival delay of 1 hour 5 minutes is less than the required 
3-hour threshold. No compensation due.
```

### Output Details
- **Flight Information**: IATA code, flight number, operator, status
- **Departure Details**: Airport, terminal, gate, scheduled/actual times, delay
- **Arrival Details**: Airport, terminal, gate, scheduled/actual times, delay
- **EU 261/2004 Analysis**: Eligibility status and compensation amount
- **Decision Explanation**: Clear reasoning for the decision

---

## Script 3: eu261_decision_rule.py

### Purpose
Standalone decision engine for EU 261/2004 compensation eligibility evaluation.

### EU 261/2004 Rules Implemented
1. **Arrival Delay Threshold**: ≥ 3 hours (180 minutes)
2. **Extraordinary Circumstances**: Exempts compensation
3. **Compensation Amounts**:
   - €250: Flights ≤ 1,500 km
   - €400: Flights 1,500–3,500 km
   - €600: Flights > 3,500 km

### Usage as Standalone Script

```bash
python aviationstack/eu261_decision_rule.py
```

Analyzes the first flight in `api_results.json`.

### Usage as Imported Module

```python
from eu261_decision_rule import EU261DecisionRule

# Load flight data from API response
flight_data = {...}  # From Timetable API

# Create engine
engine = EU261DecisionRule(flight_data)

# Evaluate eligibility
result = engine.evaluate(
    is_extraordinary_circumstance=False,
    flight_distance_km=850  # optional
)

# Access results
print(result.status)                # ELIGIBLE, NOT_ELIGIBLE, or PENDING
print(result.delay_minutes)         # Actual delay in minutes
print(result.compensation_amount_eur)  # € amount or None
print(result.reason)                # Human-readable explanation
```

### Eligibility Decision States

| Status | Meaning | Triggers |
|--------|---------|----------|
| `PENDING` | Cannot determine eligibility | Flight hasn't arrived yet (no `actualTime`), or delay unknown |
| `ELIGIBLE` | Passenger entitled to compensation | Arrival delay ≥ 180 min AND no extraordinary circumstances |
| `NOT_ELIGIBLE` | No compensation owed | Arrival delay < 180 min OR extraordinary circumstances apply |

---

## Timetable API Response Format

Example `api_results.json` structure:

```json
{
  "pagination": {
    "limit": 100,
    "offset": 0,
    "count": 100,
    "total": 1669022
  },
  "data": [
    {
      "airline": {
        "iataCode": "AV",
        "icaoCode": "AVA",
        "name": "SA AVIANCA"
      },
      "arrival": {
        "actualTime": "2024-06-18T14:15:22Z",
        "actualRunway": "2024-06-18T14:15:22Z",
        "delay": "65",
        "estimatedTime": "2024-06-18T23:10:00.000",
        "gate": "3",
        "iataCode": "JFK",
        "icaoCode": "KJFK",
        "scheduledTime": "2024-06-18T22:05:00.000",
        "terminal": "1"
      },
      "departure": {
        "actualTime": "2024-06-18T20:46:00.000",
        "actualRunway": "2024-06-18T20:46:00.000",
        "delay": "97",
        "estimatedTime": "2024-06-18T19:10:00.000",
        "gate": "C4",
        "iataCode": "TPE",
        "icaoCode": "RCTP",
        "scheduledTime": "2024-06-18T19:10:00.000",
        "terminal": "2"
      },
      "flight": {
        "iataNumber": "AV4511",
        "icaoNumber": "AVA4511",
        "number": "4511"
      },
      "codeshared": null,
      "status": "scheduled",
      "type": "arrival"
    }
  ]
}
```

### Field Notes
- **Delays**: Stored as **strings** (e.g., `"65"`), automatically parsed to integers
- **Airport codes**: Use `iataCode`/`icaoCode` format
- **Flight ID**: Use `iataNumber`/`icaoNumber` format
- **Arrival Status**: `actualTime` being present indicates flight has completed
- **Type**: Indicates `arrival` or `departure` timetable

---

## Configuration

### API Settings
- **Endpoint**: `https://api.aviationstack.com/v1/timetable`
- **API Key**: Edit `api_key = 'e20e7bed45a2ceacb137580a8dae223f'` in:
  - `fetch_api_data.py`
  - `test_api.py`

### Local Cache
- **File**: `aviationstack/api_results.json`
- **Purpose**: Stores fetched timetable data for offline use
- **Update**: Run `fetch_api_data.py` to refresh

---

## Error Handling

Scripts handle:
- ✓ Missing or malformed API responses
- ✓ Network connectivity issues
- ✓ File not found errors
- ✓ JSON parsing errors
- ✓ Invalid delay values (string-to-integer conversion)
- ✓ Missing required fields

All errors display clear messages with guidance.

---

## Integration with DelaySlayer

These scripts integrate with DelaySlayer for:
- **Real-time timetable data**: Fetches current flight information
- **Automated eligibility assessment**: Evaluates EU 261/2004 compliance
- **Passenger-facing analysis**: Provides clear compensation decisions
- **Staff tools**: Supports complaint moderation and assessment
- **Audit trail**: Documents decision logic and supporting data
- **Extensible architecture**: Easy to add rules or integration points

