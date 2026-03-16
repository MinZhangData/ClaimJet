"""
Flight Verification Module using AviationStack API
Verifies real flight data and determines EU261 eligibility
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from eu261_rules import EU261Rules
import os


class FlightVerifier:
    """
    Verifies flight information using AviationStack API and determines EU261 eligibility
    """

    API_BASE_URL = "https://api.aviationstack.com/v1/flights"
    DEFAULT_ACCESS_KEY = "e20e7bed45a2ceacb137580a8dae223f"

    def __init__(self, access_key: Optional[str] = None):
        """
        Initialize FlightVerifier with API access key

        Args:
            access_key: AviationStack API access key (defaults to env var or hardcoded key)
        """
        self.access_key = (
            access_key
            or os.environ.get("AVIATIONSTACK_API_KEY")
            or self.DEFAULT_ACCESS_KEY
        )

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula

        Args:
            lat1, lon1: Origin coordinates
            lat2, lon2: Destination coordinates

        Returns:
            Distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        # Earth radius in kilometers
        r = 6371

        return c * r

    def _estimate_distance_from_airports(self, dep_iata: str, arr_iata: str) -> float:
        """
        Estimate flight distance based on common routes

        Args:
            dep_iata: Departure airport IATA code
            arr_iata: Arrival airport IATA code

        Returns:
            Estimated distance in kilometers (0 if unknown)
        """
        # Common airport pairs and their distances
        routes = {
            ("AMS", "GOT"): 770,  # Amsterdam - Gothenburg
            ("GOT", "AMS"): 770,
            ("AMS", "BCN"): 1200,  # Amsterdam - Barcelona
            ("BCN", "AMS"): 1200,
            ("AMS", "CDG"): 430,  # Amsterdam - Paris
            ("CDG", "AMS"): 430,
            ("AMS", "LHR"): 360,  # Amsterdam - London
            ("LHR", "AMS"): 360,
            ("AMS", "JFK"): 5900,  # Amsterdam - New York
            ("JFK", "AMS"): 5900,
            ("AMS", "DXB"): 5000,  # Amsterdam - Dubai
            ("DXB", "AMS"): 5000,
        }

        return routes.get((dep_iata, arr_iata), 0)

    def verify_flight(
        self, flight_number: str, flight_date: Optional[str] = None
    ) -> Dict:
        """
        Verify flight information and determine EU261 eligibility

        Args:
            flight_number: Flight number (e.g., "KL1234")
            flight_date: Flight date in YYYY-MM-DD format (optional for current/future flights)

        Returns:
            Dictionary containing flight info and EU261 decision

        Note:
            Free tier API only supports current and future flights.
            Historical flight queries require a paid plan.
        """
        try:
            # Call AviationStack API
            params = {
                "access_key": self.access_key,
                "flight_iata": flight_number,
                "limit": 100,
            }

            # Try to add date parameter (works on paid plans)
            if flight_date:
                params["flight_date"] = flight_date

            response = requests.get(self.API_BASE_URL, params=params, timeout=10)

            # Check for API errors
            if response.status_code == 403:
                api_data = response.json()
                error_msg = api_data.get("error", {}).get(
                    "message", "API access denied"
                )

                # If date parameter caused the error, retry without it
                if flight_date and "subscription" in error_msg.lower():
                    # Retry without date parameter
                    params_no_date = {
                        "access_key": self.access_key,
                        "flight_iata": flight_number,
                        "limit": 100,
                    }
                    response = requests.get(
                        self.API_BASE_URL, params=params_no_date, timeout=10
                    )

                    if response.status_code != 200:
                        return {
                            "success": False,
                            "error": f"Free tier API cannot query specific dates. Requested: {flight_date}. Available: recent flights only. Upgrade to paid plan for historical data.",
                            "error_type": "api_limitation",
                        }
                else:
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "api_forbidden",
                    }

            response.raise_for_status()
            api_data = response.json()

            # Check for API error in response
            if "error" in api_data:
                return {
                    "success": False,
                    "error": api_data["error"].get("message", "Unknown API error"),
                    "error_type": "api_error",
                }

            # Check if flight data exists
            if not api_data.get("data") or len(api_data["data"]) == 0:
                return {
                    "success": False,
                    "error": f"No flight data found for {flight_number}"
                    + (f" on {flight_date}" if flight_date else ""),
                    "error_type": "not_found",
                }

            # If date was specified, try to find matching flight
            flights = api_data["data"]
            if flight_date:
                matching_flights = [
                    f for f in flights if f.get("flight_date") == flight_date
                ]
                if matching_flights:
                    flight = matching_flights[0]
                else:
                    # No exact match - show available dates
                    available_dates = list(set([f.get("flight_date") for f in flights]))
                    return {
                        "success": False,
                        "error": f"Flight {flight_number} not found for {flight_date}. Available: {', '.join(sorted(available_dates))}. Note: Free tier shows recent flights only.",
                        "error_type": "date_not_available",
                        "available_dates": available_dates,
                    }
            else:
                # Use most recent flight
                flight = flights[0]

            # Extract flight information
            result = self._extract_flight_info(flight)

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

    def _extract_flight_info(self, flight: Dict) -> Dict:
        """
        Extract relevant flight information from API response

        Args:
            flight: Flight data from API

        Returns:
            Structured flight information
        """
        # Get departure and arrival info
        departure = flight.get("departure", {})
        arrival = flight.get("arrival", {})
        flight_info = flight.get("flight", {})

        # Extract airport codes
        dep_airport = departure.get("iata", "Unknown")
        arr_airport = arrival.get("iata", "Unknown")

        # Extract scheduled and actual times
        scheduled_dep = departure.get("scheduled")
        actual_dep = departure.get("actual") or departure.get("estimated")
        scheduled_arr = arrival.get("scheduled")
        actual_arr = arrival.get("actual") or arrival.get("estimated")

        # Calculate delay
        delay_hours = 0
        if scheduled_arr and actual_arr:
            try:
                scheduled_time = datetime.fromisoformat(
                    scheduled_arr.replace("Z", "+00:00")
                )
                actual_time = datetime.fromisoformat(actual_arr.replace("Z", "+00:00"))
                delay_minutes = (actual_time - scheduled_time).total_seconds() / 60
                delay_hours = delay_minutes / 60
            except:
                delay_hours = 0

        # Calculate distance
        distance_km = 0
        try:
            dep_lat = departure.get("latitude")
            dep_lon = departure.get("longitude")
            arr_lat = arrival.get("latitude")
            arr_lon = arrival.get("longitude")

            if all([dep_lat, dep_lon, arr_lat, arr_lon]):
                distance_km = self.calculate_distance(
                    float(dep_lat), float(dep_lon), float(arr_lat), float(arr_lon)
                )
            else:
                # If coordinates not available, try to estimate based on common routes
                distance_km = self._estimate_distance_from_airports(
                    dep_airport, arr_airport
                )
        except:
            # If calculation fails, try to estimate based on common routes
            distance_km = self._estimate_distance_from_airports(
                dep_airport, arr_airport
            )

        # Extract flight status
        flight_status = flight.get("flight_status", "unknown")

        return {
            "success": True,
            "flight_number": flight_info.get("iata", "Unknown"),
            "airline": flight_info.get("airline", {}).get("name", "Unknown"),
            "departure_airport": dep_airport,
            "departure_city": departure.get("airport", "Unknown"),
            "arrival_airport": arr_airport,
            "arrival_city": arrival.get("airport", "Unknown"),
            "scheduled_departure": scheduled_dep,
            "actual_departure": actual_dep,
            "scheduled_arrival": scheduled_arr,
            "actual_arrival": actual_arr,
            "flight_status": flight_status,
            "delay_hours": round(delay_hours, 2),
            "distance_km": round(distance_km, 0),
            "flight_date": flight.get("flight_date", "Unknown"),
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
        cancellation = flight_status == "cancelled"

        # Check if flight was delayed enough for compensation
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

            # Add helpful suggestion for date limitations
            if result.get("error_type") in ["api_limitation", "date_not_available"]:
                available = result.get("available_dates", [])
                error_msg += "\n\n💡 **Alternative Options:**\n"
                if available:
                    error_msg += (
                        f"1. Check available dates: {', '.join(sorted(available))}\n"
                    )
                error_msg += "2. Use manual entry: Tell me your flight delay details (route, delay hours)\n"
                error_msg += "3. Upgrade API plan for historical data access\n"

            return error_msg

        message = f"""
✈️ **Flight Verification Result**

**Flight Details:**
- Flight: {result["flight_number"]} ({result["airline"]})
- Route: {result["departure_airport"]} → {result["arrival_airport"]}
- Date: {result["flight_date"]}
- Distance: {result["distance_km"]} km
- Status: {result["flight_status"].upper()}

**Delay Information:**
- Scheduled Arrival: {result.get("scheduled_arrival", "N/A")}
- Actual Arrival: {result.get("actual_arrival", "N/A")}
- Delay: {result["delay_hours"]} hours

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

    # Test with a recent flight (adjust date as needed)
    print("Testing flight verification...")
    print("=" * 60)

    # Example: KL1234 flight (without date - free tier limitation)
    print("\nTest 1: KL1234 (current/upcoming flights)")
    result = verifier.verify_flight("KL1234")
    print(verifier.format_decision(result))

    print("\n" + "=" * 60)
    print("\nTest 2: BA123 (example)")
    result2 = verifier.verify_flight("BA123")
    print(verifier.format_decision(result2))


if __name__ == "__main__":
    test_flight_verification()
