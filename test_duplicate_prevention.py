"""
Test script for duplicate claim prevention feature
"""

from claim_database import ClaimDatabase


def test_duplicate_prevention():
    """Test the duplicate claim prevention system"""
    
    db = ClaimDatabase()
    
    print("=" * 80)
    print("DUPLICATE CLAIM PREVENTION - TEST SCRIPT")
    print("=" * 80)
    
    # Test 1: Check for existing duplicate
    print("\n📋 Test 1: Checking for existing duplicate claim")
    print("-" * 80)
    email = "john.smith@email.com"
    flight_number = "KL1234"
    flight_date = "2026-01-15"
    
    is_duplicate, existing = db.check_duplicate(email, flight_number, flight_date)
    
    if is_duplicate:
        print(f"✅ Duplicate detected!")
        print(f"   Previous submission: {existing['submission_id']}")
        print(f"   Status: {existing['status']}")
        print(f"   Submitted: {existing['submitted_at'][:10]}")
    else:
        print(f"❌ No duplicate found (unexpected)")
    
    # Test 2: Check for non-existent claim
    print("\n📋 Test 2: Checking for new claim (should not be duplicate)")
    print("-" * 80)
    email_new = "newuser@email.com"
    flight_number_new = "KL9999"
    flight_date_new = "2026-03-20"
    
    is_duplicate, existing = db.check_duplicate(email_new, flight_number_new, flight_date_new)
    
    if is_duplicate:
        print(f"❌ Duplicate detected (unexpected)")
    else:
        print(f"✅ No duplicate found - ready for new submission")
    
    # Test 3: Submit a new claim
    print("\n📋 Test 3: Submitting a new claim")
    print("-" * 80)
    
    new_submission = db.add_submission(
        email=email_new,
        flight_number=flight_number_new,
        flight_date=flight_date_new,
        passenger_name="New User",
        compensation_amount=400.0,
        delay_hours=4.5,
        route="AMS -> LHR",
        status="pending"
    )
    
    print(f"✅ New claim submitted successfully!")
    print(f"   Submission ID: {new_submission['submission_id']}")
    print(f"   Passenger: {new_submission['passenger_name']}")
    print(f"   Flight: {new_submission['flight_number']}")
    print(f"   Compensation: €{new_submission['compensation_amount']}")
    
    # Test 4: Try to submit duplicate of the claim we just created
    print("\n📋 Test 4: Attempting to submit duplicate claim")
    print("-" * 80)
    
    is_duplicate, existing = db.check_duplicate(email_new, flight_number_new, flight_date_new)
    
    if is_duplicate:
        print(f"✅ Duplicate prevention working!")
        print(f"   Blocked duplicate submission")
        print(f"   Original submission: {existing['submission_id']}")
    else:
        print(f"❌ Duplicate not detected (error)")
    
    # Test 5: View all claims for a customer
    print("\n📋 Test 5: View all claims for john.smith@email.com")
    print("-" * 80)
    
    customer_claims = db.get_customer_submissions("john.smith@email.com")
    print(f"Found {len(customer_claims)} claim(s):")
    for claim in customer_claims:
        print(f"  - {claim['submission_id']}: {claim['flight_number']} on {claim['flight_date']} - {claim['status']}")
    
    # Test 6: Update claim status
    print("\n📋 Test 6: Update claim status")
    print("-" * 80)
    
    success = db.update_claim_status(new_submission['submission_id'], 'approved')
    if success:
        print(f"✅ Claim status updated to 'approved'")
    else:
        print(f"❌ Failed to update claim status")
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    test_duplicate_prevention()
