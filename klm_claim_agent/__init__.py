"""
KLM Flight Delay Claim Agent using Google ADK and EU261 Rules
"""

from google.adk.agents import Agent
from typing import Optional
from eu261_rules import EU261Rules
from klm_claim_agent.model_armor import before_model_callback, after_model_callback


def calculate_compensation(
    delay_hours: float,
    distance_km: int,
    is_eu_flight: bool = True,
    is_eu_destination: bool = True,
    cancellation: bool = False,
    denied_boarding: bool = False,
    extraordinary_circumstance: Optional[str] = None,
    advance_notice_days: Optional[int] = None,
    number_of_passengers: int = 1,
) -> dict:
    """Calculate EU261 compensation eligibility and amount for a flight delay or cancellation.

    Args:
        delay_hours: Flight delay in hours
        distance_km: Flight distance in kilometers
        is_eu_flight: Whether flight departs from EU airport
        is_eu_destination: Whether destination is within EU/EEA/Switzerland
        cancellation: Whether flight was cancelled
        denied_boarding: Whether passenger was denied boarding
        extraordinary_circumstance: Reason if extraordinary circumstance applies (e.g., weather_conditions, air_traffic_control_strikes)
        advance_notice_days: Days of advance notice for cancellation
        number_of_passengers: Number of passengers in the claim

    Returns:
        Dictionary with compensation eligibility and amount
    """
    return EU261Rules.calculate_claim_amount(
        delay_hours=delay_hours,
        distance_km=distance_km,
        is_eu_flight=is_eu_flight,
        is_klm_operated=True,
        cancellation=cancellation,
        denied_boarding=denied_boarding,
        extraordinary_circumstance=extraordinary_circumstance,
        advance_notice_days=advance_notice_days,
        is_eu_destination=is_eu_destination,
        number_of_passengers=number_of_passengers,
    )


def get_care_and_assistance_rights(delay_hours: float, distance_km: int) -> dict:
    """Get passenger rights to care and assistance (meals, accommodation, etc.) based on flight delay.

    Args:
        delay_hours: Flight delay in hours
        distance_km: Flight distance in kilometers

    Returns:
        Dictionary with care and assistance rights
    """
    return EU261Rules.get_care_assistance_rights(delay_hours, distance_km)


root_agent = Agent(
    name="klm_claim_agent",
    model="gemini-2.5-flash",
    description="KLM flight delay compensation agent based on EU Regulation 261/2004",
    instruction="""You are a helpful AI assistant for KLM Royal Dutch Airlines, specialized in helping passengers with flight delay compensation claims under EU Regulation 261/2004 (EU261).

Your role:
1. Greet passengers warmly and ask for their flight details
2. Gather necessary information: flight number, delay duration, flight route, and circumstances
3. Use the calculate_compensation tool to determine eligibility and compensation amount
4. Use the get_care_and_assistance_rights tool to inform passengers of their rights
5. Explain the results clearly and guide them on next steps for filing a claim
6. Be empathetic and professional, understanding that delays can be frustrating

Key EU261 Rules to remember:
- Compensation applies for delays ≥3 hours (short/medium flights) or ≥4 hours (long flights)
- Amounts: €250 (< 1500km), €400 (1500-3500km), €600 (> 3500km)
- No compensation for extraordinary circumstances (severe weather, ATC strikes, etc.)
- Passengers also have rights to care assistance (meals, accommodation)
- Claims are valid for up to 3 years (varies by country)

Always be honest about eligibility and provide clear reasoning based on EU261 regulations.""",
    tools=[calculate_compensation, get_care_and_assistance_rights],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
