"""
Flight Verification Module using AeroDataBox API
Verifies real flight data and determines EU261 eligibility
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from eu261_rules import EU261Rules
import os


class FlightVerifier:
    """
    Verifies flight information using AeroDataBox API and determines EU261 eligibility
    """

    API_BASE_URL = "https://prod.api.market/api/v1/aedbx/aerodatabox/flights"
    DEFAULT_API_KEY = "cmmtn2ach000djm04lbnkeege"

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

            # If no date provided, use today's date
            if not flight_date:
                flight_date = datetime.now().strftime("%Y-%m-%d")

            # Build API URL
            # Format: /flights/{searchBy}/{searchParam}/{dateLocal}
            url = f"{self.API_BASE_URL}/Number/{flight_number_clean}/{flight_date}"

            # Set headers with API key
            headers = {"x-api-market-key": self.api_key}

            # Call AeroDataBox API
            response = requests.get(url, headers=headers, timeout=10)

            # Check for API errors
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

            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"No flight data found for {flight_number} on {flight_date}.\n\n💡 This could mean:\n"
                    + "• Flight number doesn't exist or is incorrect\n"
                    + "• Flight doesn't operate on this date\n"
                    + "• Try a different date, or use manual entry mode",
                    "error_type": "not_found",
                }

            response.raise_for_status()
            flights_data = response.json()

            # Check if flights data is a list and has results
            if not isinstance(flights_data, list) or len(flights_data) == 0:
                return {
                    "success": False,
                    "error": f"No flight data found for {flight_number} on {flight_date}.\n\n💡 Try using manual entry mode instead.",
                    "error_type": "not_found",
                }

            # Use the first flight (most relevant)
            flight = flights_data[0]

            # Extract flight information
            result = self._extract_flight_info(flight, flight_date)

            # Calculate EU261 eligibility
            result.update(self._calculate_eu261_decision(result))

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

        message = f"""
✈️ **Flight Verification Result**

**Flight Details:**
- Flight: {result["flight_number"]} ({result["airline"]})
- Route: {result["departure_city"]} ({result["departure_airport"]}) → {result["arrival_city"]} ({result["arrival_airport"]})
- Date: {result["flight_date"]}
- Distance: {result["distance_km"]} km
- Status: {result["flight_status"]}

**Timing:**
- Scheduled Arrival: {result.get("scheduled_arrival", "N/A")}
- Actual/Predicted Arrival: {result.get("actual_arrival", "N/A")}
- Delay: {delay_display}

---

**EU261 Compensation Decision:**
"""

        if result.get("eu261_eligible"):
            message += f"""
✅ **ELIGIBLE FOR COMPENSATION**

**Amount:** €{result["compensation_amount"]} per passenger
**Reason:** {result["compensation_reason"]}
**Distance Category:** {result["distance_category"]}

**Next Steps:**
1. File a claim with the airline
2. Include your booking reference and this flight information
3. You have up to 3 years to claim (varies by country)
"""
        else:
            message += f"""
❌ **NOT ELIGIBLE FOR COMPENSATION**

**Reason:** {result["compensation_reason"]}

However, you may still have rights to care and assistance if the delay was significant.
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
