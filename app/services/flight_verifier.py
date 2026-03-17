"""
Flight Verification Module using AeroDataBox API
Verifies real flight data and determines EU261 eligibility
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from app.services.eu261_rules import EU261Rules


class FlightVerifier:
    """
    Verifies flight information using AeroDataBox API and determines EU261 eligibility
    """

    API_BASE_URL = "https://prod.api.market/api/v1/aedbx/aerodatabox/flights"
    DEFAULT_API_KEY = "cmmtn2ach000djm04lbnkeege"

    # Mock test flights for EU261 demonstration
    MOCK_FLIGHTS = {
        "TEST001": {
            "success": True,
            "flight_number": "KL TEST001",
            "airline": "KLM (Test Flight)",
            "departure_airport": "AMS",
            "departure_city": "Amsterdam Schiphol",
            "arrival_airport": "JFK",
            "arrival_city": "New York JFK",
            "scheduled_arrival": "2026-03-10 18:30-05:00",
            "actual_arrival": "2026-03-11 01:15-05:00",
            "flight_status": "Landed - Delayed",
            "delay_hours": 6.75,
            "delay_minutes": 405,
            "distance_km": 5860,
            "flight_date": "2026-03-10",
            "is_mock": True,
            "mock_scenario": "Long-haul flight delayed over 6 hours (March 10, 2026)",
        },
        "TEST002": {
            "success": True,
            "flight_number": "KL TEST002",
            "airline": "KLM (Test Flight)",
            "departure_airport": "AMS",
            "departure_city": "Amsterdam Schiphol",
            "arrival_airport": "BCN",
            "arrival_city": "Barcelona El Prat",
            "scheduled_arrival": "2026-03-12 14:30+01:00",
            "actual_arrival": "2026-03-12 18:45+01:00",
            "flight_status": "Landed - Delayed",
            "delay_hours": 4.25,
            "delay_minutes": 255,
            "distance_km": 1250,
            "flight_date": "2026-03-12",
            "is_mock": True,
            "mock_scenario": "Medium distance flight delayed 4+ hours (March 12, 2026)",
        },
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FlightVerifier with API key

        Args:
            api_key: AeroDataBox API key (defaults to env var or hardcoded key)
        """
        self.api_key = (
            api_key or os.environ.get("AERODATABOX_API_KEY") or self.DEFAULT_API_KEY
        )

    def verify_flight(
        self, flight_number: str, flight_date: Optional[str] = None
    ) -> Dict:
        """
        Verify flight information and determine EU261 eligibility

        Args:
            flight_number: Flight number (e.g., "KL1234", "KL 1234", "0895")
            flight_date: Flight date in YYYY-MM-DD format (required for this API)

        Returns:
            Dictionary containing flight info and EU261 decision
        """
        try:
            # Clean up flight number (remove spaces)
            flight_number_clean = flight_number.replace(" ", "").upper()

            # Check if this is a mock test flight
            if flight_number_clean in self.MOCK_FLIGHTS:
                result = self.MOCK_FLIGHTS[flight_number_clean].copy()
                # Calculate EU261 eligibility for mock flight
                result.update(self._calculate_eu261_decision(result))
                return result

            # If no date provided, use today's date
            if not flight_date:
                flight_date = datetime.now().strftime("%Y-%m-%d")
                search_for_latest = True
            else:
                search_for_latest = False

            # Try to get flight data, searching backwards if needed
            result = self._fetch_flight_data(
                flight_number_clean, flight_date, search_for_latest
            )

            return result

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "error_type": "api_error",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unknown_error",
            }

    def _fetch_flight_data(
        self, flight_number: str, flight_date: str, search_for_latest: bool = False
    ) -> Dict:
        """
        Fetch flight data from API, searching backwards if no data found

        Args:
            flight_number: Clean flight number (e.g., "KL1234")
            flight_date: Flight date in YYYY-MM-DD format
            search_for_latest: If True, search backwards for latest available data

        Returns:
            Dictionary containing flight info and EU261 decision
        """
        headers = {"x-api-market-key": self.api_key}
        original_date = flight_date

        # Try up to 14 days backwards if search_for_latest is True
        max_attempts = 14 if search_for_latest else 1

        for days_back in range(max_attempts):
            current_date = (
                datetime.strptime(flight_date, "%Y-%m-%d") - timedelta(days=days_back)
            ).strftime("%Y-%m-%d")

            # Build API URL
            url = f"{self.API_BASE_URL}/Number/{flight_number}/{current_date}"

            # Call AeroDataBox API
            response = requests.get(url, headers=headers, timeout=10)

            # Check for API errors that should stop the search
            if response.status_code == 401:
                return {
                    "success": False,
                    "error": "API authentication failed. Please check your API key.",
                    "error_type": "api_auth_error",
                }

            if response.status_code == 403:
                return {
                    "success": False,
                    "error": "API access denied. Your plan may not support this feature.",
                    "error_type": "api_forbidden",
                }

            # Handle 404 or 204 - no data for this date, continue searching if enabled
            if (
                response.status_code == 404
                or response.status_code == 204
                or len(response.content) == 0
            ):
                if search_for_latest and days_back < max_attempts - 1:
                    # Continue searching backwards
                    continue
                else:
                    # No more attempts or not searching - return error
                    return {
                        "success": False,
                        "error": f"No flight data found for {flight_number} on {original_date}.\n\n💡 This could mean:\n"
                        + "• Flight number doesn't exist or is incorrect\n"
                        + "• Flight doesn't operate on this date\n"
                        + "• Try a different date, or use manual entry mode",
                        "error_type": "not_found",
                    }

            # Try to parse JSON response
            try:
                response.raise_for_status()
                flights_data = response.json()
            except ValueError as e:
                # JSON parsing error - likely empty response
                if search_for_latest and days_back < max_attempts - 1:
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"No flight data found for {flight_number} on {original_date}.\n\n💡 Try using manual entry mode instead.",
                        "error_type": "not_found",
                    }

            # Check if flights data is a list and has results
            if not isinstance(flights_data, list) or len(flights_data) == 0:
                if search_for_latest and days_back < max_attempts - 1:
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"No flight data found for {flight_number} on {original_date}.\n\n💡 Try using manual entry mode instead.",
                        "error_type": "not_found",
                    }

            # Found valid flight data!
            flight = flights_data[0]

            # Extract flight information
            result = self._extract_flight_info(flight, current_date)

            # Add note if we used a different date
            if current_date != original_date:
                result["date_note"] = (
                    f"Using data from {current_date} (latest available)"
                )

            # Calculate EU261 eligibility
            result.update(self._calculate_eu261_decision(result))

            return result

        # If we get here, we've exhausted all attempts
        return {
            "success": False,
            "error": f"No flight data found for {flight_number} in the past {max_attempts} days.\n\n💡 Try using manual entry mode instead.",
            "error_type": "not_found",
        }

    def _extract_flight_info(self, flight: Dict, flight_date: str) -> Dict:
        """
        Extract relevant flight information from AeroDataBox API response

        Args:
            flight: Flight data from API
            flight_date: The requested flight date

        Returns:
            Structured flight information
        """
        # Get departure and arrival info
        departure = flight.get("departure", {})
        arrival = flight.get("arrival", {})

        # Extract airport information
        dep_airport = departure.get("airport", {})
        arr_airport = arrival.get("airport", {})

        dep_iata = dep_airport.get("iata", "Unknown")
        dep_name = dep_airport.get("name", "Unknown")
        arr_iata = arr_airport.get("iata", "Unknown")
        arr_name = arr_airport.get("name", "Unknown")

        # Extract scheduled and actual/predicted times
        scheduled_dep = departure.get("scheduledTime", {})
        scheduled_arr = arrival.get("scheduledTime", {})
        actual_arr = arrival.get("actualTime", {})
        revised_arr = arrival.get("revisedTime", {})
        predicted_arr = arrival.get("predictedTime", {})

        # Use actual if available, otherwise revised, otherwise predicted
        final_arr = (
            actual_arr
            if actual_arr
            else (revised_arr if revised_arr else predicted_arr)
        )

        # Calculate delay
        delay_hours = 0
        delay_minutes = 0
        if scheduled_arr and final_arr:
            try:
                # Get UTC times
                scheduled_utc = scheduled_arr.get("utc")
                final_utc = final_arr.get("utc")

                if scheduled_utc and final_utc:
                    # Parse times (format: "2026-03-31 01:25Z")
                    scheduled_time = datetime.strptime(scheduled_utc, "%Y-%m-%d %H:%MZ")
                    final_time = datetime.strptime(final_utc, "%Y-%m-%d %H:%MZ")

                    delay_seconds = (final_time - scheduled_time).total_seconds()
                    delay_minutes = delay_seconds / 60
                    delay_hours = delay_minutes / 60
            except Exception as e:
                print(f"Error calculating delay: {e}")
                delay_hours = 0
                delay_minutes = 0

        # Get distance (provided by API in greatCircleDistance)
        distance_km = 0
        great_circle = flight.get("greatCircleDistance", {})
        if great_circle:
            distance_km = great_circle.get("km", 0)

        # Extract flight status
        flight_status = flight.get("status", "Unknown")

        # Extract airline and flight number
        airline_info = flight.get("airline", {})
        airline_name = airline_info.get("name", "Unknown")
        flight_number = flight.get("number", "Unknown")

        # Format times for display
        scheduled_arr_display = (
            scheduled_arr.get("local", "N/A") if scheduled_arr else "N/A"
        )
        final_arr_display = final_arr.get("local", "N/A") if final_arr else "N/A"

        return {
            "success": True,
            "flight_number": flight_number,
            "airline": airline_name,
            "departure_airport": dep_iata,
            "departure_city": dep_name,
            "arrival_airport": arr_iata,
            "arrival_city": arr_name,
            "scheduled_arrival": scheduled_arr_display,
            "actual_arrival": final_arr_display,
            "flight_status": flight_status,
            "delay_hours": round(delay_hours, 2),
            "delay_minutes": round(delay_minutes, 0),
            "distance_km": round(distance_km, 0),
            "flight_date": flight_date,
        }

    def _calculate_eu261_decision(self, flight_info: Dict) -> Dict:
        """
        Calculate EU261 compensation decision based on flight information

        Args:
            flight_info: Extracted flight information

        Returns:
            EU261 decision with eligibility and compensation amount
        """
        if not flight_info.get("success"):
            return {"eu261_eligible": False, "reason": "Flight data incomplete"}

        delay_hours = flight_info.get("delay_hours", 0)
        distance_km = flight_info.get("distance_km", 0)
        flight_status = flight_info.get("flight_status", "").lower()

        # Check if flight was cancelled
        cancellation = "cancel" in flight_status

        # Calculate based on actual scenario
        if cancellation:
            # Cancelled flights are eligible (unless given adequate notice)
            claim_result = EU261Rules.calculate_claim_amount(
                delay_hours=0,
                distance_km=distance_km,
                cancellation=True,
                denied_boarding=False,
                extraordinary_circumstance=None,
                advance_notice_days=0,  # Assume no advance notice
                number_of_passengers=1,
            )
        else:
            # Calculate based on delay
            claim_result = EU261Rules.calculate_claim_amount(
                delay_hours=delay_hours,
                distance_km=distance_km,
                cancellation=False,
                denied_boarding=False,
                extraordinary_circumstance=None,
                advance_notice_days=None,
                number_of_passengers=1,
            )

        return {
            "eu261_eligible": claim_result["eligible"],
            "compensation_amount": claim_result["compensation_per_passenger"],
            "compensation_reason": claim_result["reason"],
            "distance_category": claim_result["distance_category"],
        }

    def format_decision(self, result: Dict) -> str:
        """
        Format the verification result as a human-readable message

        Args:
            result: Verification result dictionary

        Returns:
            Formatted decision message
        """
        if not result.get("success"):
            error_msg = f"❌ Error: {result.get('error', 'Unknown error')}"
            return error_msg

        # Determine if there's a delay worth mentioning
        delay_hours = result.get("delay_hours", 0)
        delay_minutes = result.get("delay_minutes", 0)

        # Format delay display
        if delay_hours >= 1:
            delay_display = f"{delay_hours} hours"
        elif delay_minutes > 0:
            delay_display = f"{int(delay_minutes)} minutes"
        elif delay_hours < 0:
            delay_display = f"{abs(delay_hours)} hours early"
        else:
            delay_display = "On time"

        # Add date note if present
        date_note = ""
        if result.get("date_note"):
            date_note = f"\n💡 **Note:** {result['date_note']}"

        # Add mock flight indicator
        mock_note = ""
        if result.get("is_mock"):
            mock_note = f"\n\n🧪 **TEST SCENARIO:** {result.get('mock_scenario', 'Demonstration flight')}"

        # Build eligibility decision first
        if result.get("eu261_eligible"):
            decision_header = f"""
✅ **ELIGIBLE FOR COMPENSATION**

**Amount:** €{result["compensation_amount"]} per passenger
**Reason:** {result["compensation_reason"]}
**Distance Category:** {result["distance_category"]}{mock_note}
"""
        else:
            decision_header = f"""
❌ **NOT ELIGIBLE FOR COMPENSATION**

**Reason:** {result["compensation_reason"]}{mock_note}
"""

        # Build full message with eligibility first
        message = f"""
{decision_header}
---

✈️ **Flight Details:**
- Flight: {result["flight_number"]} ({result["airline"]})
- Route: {result["departure_city"]} ({result["departure_airport"]}) → {result["arrival_city"]} ({result["arrival_airport"]})
- Date: {result["flight_date"]}
- Distance: {result["distance_km"]} km
- Status: {result["flight_status"]}

**Timing:**
- Scheduled Arrival: {result.get("scheduled_arrival", "N/A")}
- Actual/Predicted Arrival: {result.get("actual_arrival", "N/A")}
- Delay: {delay_display}{date_note}
"""

        # Add next steps only if eligible
        if result.get("eu261_eligible"):
            message += f"""
---

**Next Steps:**
1. File a claim with the airline
2. Include your booking reference and this flight information
3. You have up to 3 years to claim (varies by country)
"""
        else:
            message += """

💡 However, you may still have rights to care and assistance if the delay was significant.
"""

        return message


# Test function
def test_flight_verification():
    """Test flight verification with a sample flight"""
    verifier = FlightVerifier()

    # Test with KL0895 on a specific date
    print("Testing flight verification with AeroDataBox API...")
    print("=" * 60)

    print("\nTest 1: KL0895 on 2026-03-01")
    result = verifier.verify_flight("KL0895", "2026-03-01")
    print(verifier.format_decision(result))

    print("\n" + "=" * 60)
    print("\nTest 2: KL0895 (today's date)")
    result2 = verifier.verify_flight("KL0895")
    print(verifier.format_decision(result2))


if __name__ == "__main__":
    test_flight_verification()
