# Duplicate Claim Prevention Feature

## Overview
This feature prevents customers from submitting multiple compensation claims for the same flight, ensuring data integrity and reducing fraudulent submissions.

## Files Added

### 1. `claim_database.py`
Main database manager for handling claim submissions.

**Key Features:**
- Track all customer claim submissions
- Check for duplicate claims (same email + flight + date)
- Store claim details (customer info, flight info, compensation)
- Update claim status (pending, approved, rejected)
- Query customer submission history

**Main Methods:**
```python
# Check if claim already exists
is_duplicate, existing_claim = db.check_duplicate(email, flight_number, flight_date)

# Submit new claim
submission = db.add_submission(
    email="customer@email.com",
    flight_number="KL1234",
    flight_date="2026-03-10",
    passenger_name="John Doe",
    compensation_amount=400.0,
    delay_hours=4.5,
    route="AMS -> JFK",
    status="pending"
)

# Get all claims for a customer
claims = db.get_customer_submissions("customer@email.com")

# Update claim status
db.update_claim_status("CLM202603170001", "approved")
```

### 2. `claims_database.json`
JSON file storing all claim submissions with sample data.

**Sample Entry:**
```json
{
  "submission_id": "CLM202601150001",
  "email": "john.smith@email.com",
  "passenger_name": "John Smith",
  "flight_number": "KL1234",
  "flight_date": "2026-01-15",
  "route": "AMS -> JFK",
  "delay_hours": 4.5,
  "compensation_amount": 600.0,
  "status": "approved",
  "submitted_at": "2026-01-16T10:30:00"
}
```

### 3. Updated `chatbot.py`
Enhanced chatbot with claim submission workflow.

**New Features:**
- Extracts customer email and name from messages
- Collects flight date for submission
- Checks for duplicate claims before submitting
- Shows detailed duplicate warning if claim exists
- Stores successful claims in database
- Provides submission confirmation with ID

**User Flow:**
1. Customer describes flight delay/cancellation
2. Chatbot calculates eligibility and compensation
3. If eligible, chatbot asks for email, name, and flight date
4. System checks for duplicates
5. If duplicate: Shows warning with existing claim details
6. If new: Submits claim and provides confirmation

### 4. `test_duplicate_prevention.py`
Test script demonstrating all features.

## Usage Example

### Testing the Feature
```bash
python test_duplicate_prevention.py
```

### Using in Chatbot
```
User: "My flight KL1234 from Amsterdam to New York was delayed 5 hours"

Chatbot: "✅ You are eligible for €600 compensation!
          
          To submit your claim, please provide:
          1. Your email address
          2. Your full name  
          3. Flight date (YYYY-MM-DD)"

User: "My email is john.smith@email.com, my name is John Smith, flight date was 2026-01-15"

Chatbot: "⚠️ Duplicate Claim Detected!
          
          You have already submitted a claim for this flight:
          - Submission ID: CLM202601150001
          - Status: APPROVED
          - Submitted on: 2026-01-16
          
          You cannot submit multiple claims for the same flight."
```

## Sample Database

The `claims_database.json` includes 7 sample claims:

| Email | Flight | Date | Status | Amount |
|-------|--------|------|--------|--------|
| john.smith@email.com | KL1234 | 2026-01-15 | approved | €600 |
| maria.garcia@email.com | KL0895 | 2026-01-20 | pending | €250 |
| pierre.dubois@email.com | KL1956 | 2026-02-01 | approved | €250 |
| anna.mueller@email.com | KL1234 | 2026-02-10 | rejected | €600 |
| carlos.rodriguez@email.com | KL0703 | 2026-03-01 | pending | €250 |
| lisa.anderson@email.com | KL0643 | 2026-03-05 | rejected | €0 |
| john.smith@email.com | KL0895 | 2026-03-10 | pending | €250 |

## Testing Scenarios

### Scenario 1: Duplicate Detection
**Input:** john.smith@email.com, KL1234, 2026-01-15
**Expected:** Duplicate detected, shows existing claim CLM202601150001

### Scenario 2: New Submission
**Input:** newuser@email.com, KL9999, 2026-03-20
**Expected:** No duplicate, claim submitted successfully

### Scenario 3: Same customer, different flight
**Input:** john.smith@email.com, KL0895, 2026-03-10
**Expected:** No duplicate (different flight/date combination)

## Implementation Details

### Duplicate Detection Logic
A claim is considered duplicate if ALL three match:
1. Email address (case-insensitive)
2. Flight number (case-insensitive)
3. Flight date (exact match)

### Submission ID Format
- Format: `CLM{YYYYMMDD}{NNNN}`
- Example: `CLM202603170001`
- Includes date and sequential number

### Status Values
- `pending`: Claim submitted, awaiting review
- `approved`: Claim approved, payment processing
- `rejected`: Claim rejected due to ineligibility

## Future Enhancements

Potential improvements:
1. Add database persistence (SQLite/PostgreSQL)
2. Email notification system
3. Admin dashboard for claim management
4. Appeal process for rejected claims
5. Integration with payment systems
6. Multi-language support
7. Document upload capability

## Branch Information

**Branch:** `feature/duplicate-claim-prevention`
**Base:** main
**Status:** Ready for review

## Testing

Run the test suite:
```bash
# Test duplicate prevention logic
python test_duplicate_prevention.py

# Run chatbot with new feature
python chatbot.py
```

## Notes

- Database file is auto-created if it doesn't exist
- All timestamps are in ISO 8601 format
- Email matching is case-insensitive
- Flight number matching is case-insensitive
- Date must match exactly (YYYY-MM-DD format)
