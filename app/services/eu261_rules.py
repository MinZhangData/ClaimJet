"""
EU261 Flight Compensation Rules Engine for KLM
This module implements the EU261/2004 regulation rules for flight compensation.
"""

from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta


class EU261Rules:
    """
    EU261/2004 regulation implementation for flight compensation claims.
    """

    # Compensation amounts based on flight distance (in EUR)
    COMPENSATION_AMOUNTS = {
        "short": 250,  # Less than 1500 km
        "medium": 400,  # 1500-3500 km
        "long": 600,  # Over 3500 km (within EU)
        "long_non_eu": 600,  # Over 3500 km (outside EU) - can be reduced to 300 if delay < 4h
    }

    # Minimum delay thresholds for compensation (in hours)
    DELAY_THRESHOLDS = {
        "short": 3,  # >= 3 hours for flights < 1500 km
        "medium": 3,  # >= 3 hours for flights 1500-3500 km
        "long": 4,  # >= 4 hours for flights > 3500 km
    }

    # Extraordinary circumstances (no compensation)
    EXTRAORDINARY_CIRCUMSTANCES = [
        "political_instability",
        "weather_conditions",
        "security_risks",
        "air_traffic_control_strikes",
        "air_traffic_management_restrictions",
        "bird_strike",
        "hidden_manufacturing_defect",
        "terrorism_risk",
        "medical_emergency",
    ]

    @staticmethod
    def calculate_distance_category(
        distance_km: int, is_eu_destination: bool = True
    ) -> str:
        """
        Categorize flight distance according to EU261 rules.

        Args:
            distance_km: Flight distance in kilometers
            is_eu_destination: Whether destination is within EU/EEA/Switzerland

        Returns:
            Distance category: 'short', 'medium', 'long', or 'long_non_eu'
        """
        if distance_km < 1500:
            return "short"
        elif distance_km <= 3500:
            return "medium"
        else:
            return "long" if is_eu_destination else "long_non_eu"

    @staticmethod
    def is_eligible_for_compensation(
        delay_hours: float,
        distance_km: int,
        is_eu_flight: bool,
        is_klm_operated: bool,
        cancellation: bool = False,
        denied_boarding: bool = False,
        extraordinary_circumstance: Optional[str] = None,
        advance_notice_days: Optional[int] = None,
        is_eu_destination: bool = True,
    ) -> Tuple[bool, str, int]:
        """
        Determine if a passenger is eligible for EU261 compensation.

        Args:
            delay_hours: Flight delay in hours
            distance_km: Flight distance in kilometers
            is_eu_flight: Whether flight departs from EU airport
            is_klm_operated: Whether flight is operated by KLM
            cancellation: Whether flight was cancelled
            denied_boarding: Whether passenger was denied boarding
            extraordinary_circumstance: Reason if extraordinary circumstance applies
            advance_notice_days: Days of advance notice for cancellation
            is_eu_destination: Whether destination is within EU/EEA/Switzerland

        Returns:
            Tuple of (is_eligible, reason, compensation_amount)
        """

        # Check if EU261 applies
        if not is_eu_flight and not is_klm_operated:
            return (
                False,
                "EU261 does not apply - flight did not depart from EU and not operated by EU carrier",
                0,
            )

        # Check for extraordinary circumstances
        if (
            extraordinary_circumstance
            and extraordinary_circumstance.lower()
            in EU261Rules.EXTRAORDINARY_CIRCUMSTANCES
        ):
            return (
                False,
                f"No compensation due to extraordinary circumstances: {extraordinary_circumstance}",
                0,
            )

        # Get distance category and compensation amount
        distance_category = EU261Rules.calculate_distance_category(
            distance_km, is_eu_destination
        )
        compensation = EU261Rules.COMPENSATION_AMOUNTS[distance_category]

        # Handle denied boarding
        if denied_boarding:
            return (
                True,
                "Denied boarding (overbooking)",
                compensation,
            )

        # Handle cancellation
        if cancellation:
            # If cancelled with less than 14 days notice
            if advance_notice_days is None or advance_notice_days < 14:
                # Check if alternative flight was offered
                if advance_notice_days is not None and advance_notice_days >= 7:
                    # Between 7-14 days: depends on alternative flight timing
                    return (
                        True,
                        f"Cancelled with {advance_notice_days} days notice",
                        compensation,
                    )
                else:
                    # Less than 7 days notice
                    return (
                        True,
                        "Cancelled with insufficient notice",
                        compensation,
                    )
            else:
                return False, "Cancellation with adequate notice (14+ days)", 0

        # Handle delay
        threshold = EU261Rules.DELAY_THRESHOLDS.get(
            "long"
            if distance_category in ["long", "long_non_eu"]
            else distance_category,
            3,
        )

        if threshold and delay_hours >= threshold:
            # Special case: long non-EU flights with delay < 4 hours get reduced compensation
            if distance_category == "long_non_eu" and delay_hours < 4:
                compensation = 300
                return (
                    True,
                    f"{delay_hours:.1f}h delay (reduced for non-EU)",
                    compensation,
                )

            return True, f"{delay_hours:.1f}h delay", compensation
        else:
            return (
                False,
                f"Delay {delay_hours:.1f}h below {threshold}h threshold",
                0,
            )

    @staticmethod
    def calculate_claim_amount(
        delay_hours: float,
        distance_km: int,
        is_eu_flight: bool = True,
        is_klm_operated: bool = True,
        cancellation: bool = False,
        denied_boarding: bool = False,
        extraordinary_circumstance: Optional[str] = None,
        advance_notice_days: Optional[int] = None,
        is_eu_destination: bool = True,
        number_of_passengers: int = 1,
    ) -> Dict:
        """
        Calculate the total compensation claim.

        Returns:
            Dictionary with eligibility status, reason, compensation per passenger,
            total compensation, and additional details
        """
        eligible, reason, compensation = EU261Rules.is_eligible_for_compensation(
            delay_hours=delay_hours,
            distance_km=distance_km,
            is_eu_flight=is_eu_flight,
            is_klm_operated=is_klm_operated,
            cancellation=cancellation,
            denied_boarding=denied_boarding,
            extraordinary_circumstance=extraordinary_circumstance,
            advance_notice_days=advance_notice_days,
            is_eu_destination=is_eu_destination,
        )

        total_compensation = compensation * number_of_passengers
        distance_category = EU261Rules.calculate_distance_category(
            distance_km, is_eu_destination
        )

        return {
            "eligible": eligible,
            "reason": reason,
            "compensation_per_passenger": compensation,
            "total_compensation": total_compensation,
            "number_of_passengers": number_of_passengers,
            "distance_category": distance_category,
            "distance_km": distance_km,
            "delay_hours": delay_hours,
            "currency": "EUR",
        }

    @staticmethod
    def get_care_assistance_rights(delay_hours: float, distance_km: int) -> Dict:
        """
        Determine care and assistance rights based on delay duration.

        Returns:
            Dictionary with rights to meals, refreshments, accommodation, etc.
        """
        distance_category = EU261Rules.calculate_distance_category(distance_km)

        # Delay thresholds for care assistance
        care_thresholds = {
            "short": 2,  # >= 2 hours for flights < 1500 km
            "medium": 3,  # >= 3 hours for flights 1500-3500 km
            "long": 4,  # >= 4 hours for flights > 3500 km
        }

        threshold = care_thresholds.get(
            "long"
            if distance_category in ["long", "long_non_eu"]
            else distance_category,
            3,
        )

        rights = {
            "meals_and_refreshments": delay_hours >= threshold if threshold else False,
            "hotel_accommodation": delay_hours >= 5,  # If delay extends to next day
            "transport_to_accommodation": delay_hours >= 5,
            "two_phone_calls": delay_hours >= threshold if threshold else False,
            "right_to_reimbursement": delay_hours
            >= 5,  # Right to refund if choosing not to fly
            "threshold_hours": threshold,
        }

        return rights
