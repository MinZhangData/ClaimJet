"""
EU 261/2004 Flight Delay Compensation Decision Rule Engine

Evaluates flight delay data against EU 261/2004 passenger compensation eligibility criteria.
Key rule: Passengers are entitled to compensation when they reach their final destination 
with a delay of 3 hours or more, unless the delay was caused by extraordinary circumstances.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class EligibilityStatus(Enum):
    """Eligibility determination outcomes."""
    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    PENDING = "pending"  # Flight status doesn't allow determination yet


@dataclass
class DelayAnalysis:
    """Result of EU 261/2004 delay analysis."""
    status: EligibilityStatus
    delay_minutes: Optional[int]
    reason: str
    threshold_minutes: int = 180  # 3 hours in minutes
    compensation_amount_eur: Optional[int] = None
    is_extraordinary_circumstance: bool = False


class EU261DecisionRule:
    """
    Decision rule engine for EU 261/2004 flight delay compensation.
    
    EU 261/2004 compensation rules:
    - 250 EUR for flights up to 1,500 km
    - 400 EUR for EU flights >1,500 km or other flights 1,500-3,500 km
    - 600 EUR for flights >3,500 km (outside EU)
    """
    
    COMPENSATION_THRESHOLDS = {
        "up_to_1500km": 250,
        "1500_to_3500km": 400,
        "over_3500km": 600,
    }
    
    MINIMUM_DELAY_MINUTES = 180  # 3 hours
    
    def __init__(self, flight_data: Dict[str, Any]):
        """
        Initialize with flight data from API.
        
        Args:
            flight_data: Dictionary containing flight information from Timetable API
        """
        self.flight_data = flight_data
        self.flight_status = flight_data.get('status', 'unknown').lower()
        
        # Parse departure delay (may be string or null)
        departure_delay = flight_data.get('departure', {}).get('delay')
        self.departure_delay = self._parse_delay(departure_delay)
        
        # Parse arrival delay (may be string or null)
        arrival_delay = flight_data.get('arrival', {}).get('delay')
        self.arrival_delay = self._parse_delay(arrival_delay)
    
    def _parse_delay(self, delay_value) -> Optional[int]:
        """
        Parse delay value which may be string, int, or null.
        
        Args:
            delay_value: Delay value (string, int, or None)
        
        Returns:
            Delay in minutes as integer, or None if not available
        """
        if delay_value is None:
            return None
        
        try:
            return int(str(delay_value).strip())
        except (ValueError, AttributeError):
            return None
    
    def evaluate(self, 
                 is_extraordinary_circumstance: bool = False,
                 flight_distance_km: Optional[int] = None) -> DelayAnalysis:
        """
        Evaluate flight eligibility for EU 261/2004 compensation.
        
        Args:
            is_extraordinary_circumstance: Whether the delay was due to extraordinary 
                                         circumstances (exempt from compensation)
            flight_distance_km: Optional flight distance to determine compensation amount
        
        Returns:
            DelayAnalysis object with eligibility status and reasoning
        """
        
        # Rule 1: Check if flight has actually arrived (actual arrival time must exist)
        arrival_data = self.flight_data.get('arrival', {})
        has_arrived = arrival_data.get('actualTime') is not None
        
        if not has_arrived:
            return DelayAnalysis(
                status=EligibilityStatus.PENDING,
                delay_minutes=self.arrival_delay,
                reason="Flight has not yet arrived at final destination. "
                       "Decision can be made once flight lands.",
                is_extraordinary_circumstance=is_extraordinary_circumstance
            )
        
        # Rule 2: If extraordinary circumstance, passenger is not eligible
        if is_extraordinary_circumstance:
            return DelayAnalysis(
                status=EligibilityStatus.NOT_ELIGIBLE,
                delay_minutes=self.arrival_delay,
                reason="Delay attributed to extraordinary circumstances (e.g., weather, "
                       "security risk, ATC strikes). No compensation required under EU 261/2004.",
                is_extraordinary_circumstance=True
            )
        
        # Rule 3: Check arrival delay against 3-hour threshold
        # The decisive delay is the arrival delay (actual arrival vs scheduled)
        if self.arrival_delay is None:
            return DelayAnalysis(
                status=EligibilityStatus.PENDING,
                delay_minutes=None,
                reason="Arrival delay is not yet determined. Flight may still be in progress.",
                is_extraordinary_circumstance=False
            )
        
        if self.arrival_delay < self.MINIMUM_DELAY_MINUTES:
            return DelayAnalysis(
                status=EligibilityStatus.NOT_ELIGIBLE,
                delay_minutes=self.arrival_delay,
                reason=f"Arrival delay of {self._format_delay(self.arrival_delay)} is less than "
                       f"the required 3-hour threshold. No compensation due.",
                is_extraordinary_circumstance=False
            )
        
        # Rule 4: Delay >= 3 hours - passenger is eligible
        compensation = self._calculate_compensation(flight_distance_km)
        
        return DelayAnalysis(
            status=EligibilityStatus.ELIGIBLE,
            delay_minutes=self.arrival_delay,
            reason=f"Arrival delay of {self._format_delay(self.arrival_delay)} exceeds the "
                   f"3-hour threshold. Passenger is eligible for compensation under EU 261/2004.",
            compensation_amount_eur=compensation,
            is_extraordinary_circumstance=False
        )
    
    def _calculate_compensation(self, flight_distance_km: Optional[int]) -> Optional[int]:
        """
        Calculate compensation amount based on flight distance.
        
        Args:
            flight_distance_km: Distance of the flight in kilometers
        
        Returns:
            Compensation amount in EUR, or None if distance not provided
        """
        if flight_distance_km is None:
            return None
        
        if flight_distance_km <= 1500:
            return self.COMPENSATION_THRESHOLDS["up_to_1500km"]
        elif flight_distance_km <= 3500:
            return self.COMPENSATION_THRESHOLDS["1500_to_3500km"]
        else:
            return self.COMPENSATION_THRESHOLDS["over_3500km"]
    
    def _format_delay(self, minutes: int) -> str:
        """Format delay in minutes to human-readable format."""
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return f"{hours} hour{'s' if hours != 1 else ''} {mins} minute{'s' if mins != 1 else ''}"


def load_flight_data(filepath: str) -> Dict[str, Any]:
    """Load flight data from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def main():
    """Example usage: analyze flight from api_results.json"""
    
    # Load flight data
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flight_data = load_flight_data(os.path.join(script_dir, "api_results.json"))
    
    # Create decision rule engine
    engine = EU261DecisionRule(flight_data)
    
    # Evaluate eligibility (assuming no extraordinary circumstances for this example)
    result = engine.evaluate(
        is_extraordinary_circumstance=False,
        flight_distance_km=None  # Set to actual distance if available
    )
    
    # Display results
    print("=" * 70)
    print("EU 261/2004 COMPENSATION ELIGIBILITY ANALYSIS")
    print("=" * 70)
    print(f"\nFlight: {flight_data['flight']['iataNumber']}")
    print(f"Status: {flight_data['status']}")
    print(f"Type: {flight_data['type']}")
    print(f"From: {flight_data['departure']['iataCode']} → To: {flight_data['arrival']['iataCode']}")
    print()
    print(f"Eligibility Status: {result.status.value.upper()}")
    print(f"Arrival Delay: {result.delay_minutes} minutes")
    if result.compensation_amount_eur:
        print(f"Compensation (if eligible): €{result.compensation_amount_eur}")
    print()
    print("Decision Reason:")
    print(f"  {result.reason}")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    main()
