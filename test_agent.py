"""
Test script for the KLM Claim Agent
"""

from eu261_rules import EU261Rules


def test_eu261_rules():
    """Test the EU261 rules engine with various scenarios."""

    print("=" * 70)
    print("Testing EU261 Rules Engine")
    print("=" * 70)
    print()

    # Test Case 1: Eligible - Short flight with 4 hour delay
    print("Test 1: Short flight (800km) with 4-hour delay")
    result1 = EU261Rules.calculate_claim_amount(
        delay_hours=4.0, distance_km=800, number_of_passengers=2
    )
    print(f"  Eligible: {result1['eligible']}")
    print(f"  Reason: {result1['reason']}")
    print(f"  Compensation per passenger: €{result1['compensation_per_passenger']}")
    print(f"  Total compensation: €{result1['total_compensation']}")
    print()

    # Test Case 2: Not eligible - Delay below threshold
    print("Test 2: Medium flight (2000km) with 2.5-hour delay")
    result2 = EU261Rules.calculate_claim_amount(
        delay_hours=2.5, distance_km=2000, number_of_passengers=1
    )
    print(f"  Eligible: {result2['eligible']}")
    print(f"  Reason: {result2['reason']}")
    print(f"  Compensation: €{result2['total_compensation']}")
    print()

    # Test Case 3: Long flight with cancellation
    print("Test 3: Long flight (5000km) cancelled with 5 days notice")
    result3 = EU261Rules.calculate_claim_amount(
        delay_hours=0,
        distance_km=5000,
        cancellation=True,
        advance_notice_days=5,
        number_of_passengers=1,
    )
    print(f"  Eligible: {result3['eligible']}")
    print(f"  Reason: {result3['reason']}")
    print(f"  Compensation: €{result3['total_compensation']}")
    print()

    # Test Case 4: Extraordinary circumstances
    print("Test 4: Flight delayed 5 hours due to severe weather")
    result4 = EU261Rules.calculate_claim_amount(
        delay_hours=5.0,
        distance_km=1200,
        extraordinary_circumstance="weather_conditions",
        number_of_passengers=1,
    )
    print(f"  Eligible: {result4['eligible']}")
    print(f"  Reason: {result4['reason']}")
    print(f"  Compensation: €{result4['total_compensation']}")
    print()

    # Test Case 5: Denied boarding (overbooking)
    print("Test 5: Denied boarding due to overbooking")
    result5 = EU261Rules.calculate_claim_amount(
        delay_hours=0, distance_km=1500, denied_boarding=True, number_of_passengers=1
    )
    print(f"  Eligible: {result5['eligible']}")
    print(f"  Reason: {result5['reason']}")
    print(f"  Compensation: €{result5['total_compensation']}")
    print()

    # Test Case 6: Care and assistance rights
    print("Test 6: Care and assistance rights for 6-hour delay on long flight")
    rights = EU261Rules.get_care_assistance_rights(delay_hours=6.0, distance_km=4000)
    print(f"  Meals and refreshments: {rights['meals_and_refreshments']}")
    print(f"  Hotel accommodation: {rights['hotel_accommodation']}")
    print(f"  Transport to hotel: {rights['transport_to_accommodation']}")
    print(f"  Two phone calls: {rights['two_phone_calls']}")
    print(f"  Right to reimbursement: {rights['right_to_reimbursement']}")
    print()

    print("=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_eu261_rules()
