"""
Flight Compensation ADK Agent
Uses Google ADK to create an intelligent agent for EU261 compensation claims
"""

import os
from datetime import datetime
from typing import Optional, Dict, List
from google import genai
from google.genai import types
from flight_verifier import FlightVerifier
from eu261_rules import EU261Rules
from dotenv import load_dotenv
from memory_bank import get_memory_bank

# Load environment variables from .env file
load_dotenv()

# Initialize the GenAI client
# Use Gemini API with API key (get from https://aistudio.google.com/apikey)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "GEMINI_API_KEY environment variable is required. "
        "Get your API key from: https://aistudio.google.com/apikey"
    )

client = genai.Client(api_key=api_key)


# Define tools for the ADK agent
def verify_flight_data(flight_number: str, flight_date: Optional[str] = None) -> str:
    """
    Verify flight information using real-time API data and determine EU261 eligibility.

    Args:
        flight_number: Flight number (e.g., "KL1234", "TEST001", "0895")
        flight_date: Optional flight date in YYYY-MM-DD format. If not provided, uses today's date.

    Returns:
        A formatted string with flight details and EU261 compensation decision
    """
    verifier = FlightVerifier()
    result = verifier.verify_flight(flight_number, flight_date)
    return verifier.format_decision(result)


def calculate_compensation(
    delay_hours: float,
    distance_km: int,
    cancellation: bool = False,
    denied_boarding: bool = False,
    advance_notice_days: Optional[int] = None,
) -> str:
    """
    Calculate EU261 compensation based on flight disruption details.

    Args:
        delay_hours: Flight delay in hours
        distance_km: Flight distance in kilometers
        cancellation: Whether the flight was cancelled
        denied_boarding: Whether passenger was denied boarding
        advance_notice_days: Days of advance notice for cancellation (if applicable)

    Returns:
        A formatted string with compensation eligibility and amount
    """
    result = EU261Rules.calculate_claim_amount(
        delay_hours=delay_hours,
        distance_km=distance_km,
        cancellation=cancellation,
        denied_boarding=denied_boarding,
        advance_notice_days=advance_notice_days,
        number_of_passengers=1,
    )

    if result["eligible"]:
        return f"""✅ ELIGIBLE FOR COMPENSATION

Amount: €{result["compensation_per_passenger"]} per passenger
Reason: {result["reason"]}
Distance Category: {result["distance_category"]}

The flight qualifies for EU261 compensation. You can file a claim with the airline."""
    else:
        return f"""❌ NOT ELIGIBLE FOR COMPENSATION

Reason: {result["reason"]}

However, you may still have rights to care and assistance if the delay was significant."""


def get_eu261_info(query: str) -> str:
    """
    Get information about EU261 regulations and passenger rights.

    Args:
        query: Question about EU261 rules (e.g., "What are the delay thresholds?")

    Returns:
        Information about EU261 regulations
    """
    info = {
        "delay_thresholds": """EU261 Delay Thresholds:
- Short flights (<1500km): 3+ hours delay qualifies for €250
- Medium flights (1500-3500km): 3+ hours delay qualifies for €400
- Long flights (>3500km): 4+ hours delay qualifies for €600 (or €300 for 3-4 hours)""",
        "eligibility": """EU261 applies when:
- Flight departs from an EU airport, OR
- Flight arrives at an EU airport AND is operated by an EU airline
- The delay/cancellation was within the airline's control
- You checked in on time and had a confirmed booking""",
        "compensation_amounts": """EU261 Compensation Amounts:
- Flights under 1,500 km: €250
- Flights between 1,500-3,500 km: €400
- Flights over 3,500 km: €600 (can be reduced to €300 for 3-4h delays)""",
        "cancellation": """Cancellation Rights:
- Less than 14 days notice: Usually eligible for compensation
- 7-14 days notice: May be eligible depending on alternative flight
- 14+ days notice: No compensation, but entitled to refund/rebooking""",
        "extraordinary_circumstances": """Extraordinary Circumstances (No Compensation):
- Severe weather conditions
- Political instability or security risks
- Air traffic control strikes
- Medical emergencies
- Bird strikes
- Hidden manufacturing defects""",
    }

    query_lower = query.lower()

    if any(word in query_lower for word in ["delay", "threshold", "hours"]):
        return info["delay_thresholds"]
    elif any(word in query_lower for word in ["eligible", "qualify", "applies"]):
        return info["eligibility"]
    elif any(
        word in query_lower for word in ["amount", "money", "compensation", "how much"]
    ):
        return info["compensation_amounts"]
    elif any(word in query_lower for word in ["cancel", "cancellation"]):
        return info["cancellation"]
    elif any(word in query_lower for word in ["extraordinary", "weather", "strike"]):
        return info["extraordinary_circumstances"]
    else:
        return f"""EU261 Flight Compensation Information:

{info["delay_thresholds"]}

{info["compensation_amounts"]}

For more specific information, please ask about:
- Delay thresholds
- Eligibility criteria
- Cancellation rights
- Extraordinary circumstances"""


# Create the ADK agent
class FlightCompensationAgent:
    """ADK-based agent for flight compensation claims"""

    def __init__(self):
        self.tools = [verify_flight_data, calculate_compensation, get_eu261_info]
        self.memory_bank = get_memory_bank()

        self.system_instruction = """You are a helpful flight compensation assistant specializing in EU261 regulations.

Your role is to:
1. Help passengers check if their flights qualify for compensation
2. Verify real flight data using flight numbers
3. Calculate compensation amounts based on delay/distance
4. Explain EU261 rules and passenger rights

Key behaviors:
- Always be concise and clear
- Show eligibility status FIRST, then provide details
- Use the verify_flight_data tool when given a flight number
- Use calculate_compensation for manual calculations
- Use get_eu261_info to answer questions about regulations
- Be empathetic but factual about passenger rights

When a user provides a flight number:
1. Use verify_flight_data to get real-time data
2. Present the eligibility decision prominently at the top
3. Show compensation amount if eligible
4. Provide next steps for filing claims

Test flights available:
- TEST001: Long-haul delayed 6h45m (€600 compensation)
- TEST002: Short-haul delayed 4h15m (€250 compensation)
"""

    def chat(
        self,
        user_message: str,
        history: Optional[list] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Process user message and return agent response

        Args:
            user_message: User's input message
            history: Optional conversation history (from UI)
            session_id: Optional session ID for persistent memory

        Returns:
            Agent's response
        """
        try:
            # Build context with memory bank history if session_id is provided
            enhanced_message = user_message

            if session_id and self.memory_bank.enabled:
                # Get conversation context from memory bank
                context = self.memory_bank.get_context_summary(
                    session_id, max_messages=10
                )
                if context:
                    enhanced_message = (
                        f"{context}\n\nCurrent user message: {user_message}"
                    )

            # Create a chat session with tools
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=enhanced_message,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=self.tools,
                    temperature=0.3,
                ),
            )

            # Get the response text
            response_text = (
                response.text
                if response.text
                else "I apologize, but I couldn't process that request. Please try rephrasing or provide a flight number to verify."
            )

            # Store in memory bank if session_id is provided
            if session_id and self.memory_bank.enabled:
                self.memory_bank.add_message(session_id, "user", user_message)
                self.memory_bank.add_message(session_id, "assistant", response_text)

            return response_text

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}\n\nPlease try again or contact support if the issue persists."

            # Still try to save error context
            if session_id and self.memory_bank.enabled:
                self.memory_bank.add_message(session_id, "user", user_message)
                self.memory_bank.add_message(
                    session_id, "assistant", error_msg, {"error": True}
                )

            return error_msg


def test_adk_agent():
    """Test the ADK agent with sample queries"""
    agent = FlightCompensationAgent()

    test_cases = [
        "Check flight TEST001",
        "Check flight TEST002 2026-03-12",
        "What are the EU261 delay thresholds?",
        "My flight was delayed 5 hours and flew 2000km, am I eligible?",
    ]

    print("=" * 70)
    print("ADK Agent Test Cases")
    print("=" * 70)

    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. User: {test}")
        print("-" * 70)
        response = agent.chat(test)
        print(f"Agent: {response}")
        print()


if __name__ == "__main__":
    test_adk_agent()
