"""
Simple Rule-Based Chatbot for KLM Flight Delay Compensation
Works without requiring Vertex AI models
Supports real-time flight verification via AviationStack API
"""

import gradio as gr
from eu261_rules import EU261Rules
from flight_verifier import FlightVerifier
from claim_database import ClaimDatabase
from typing import Optional
import re
import os


class SimpleClaimChatbot:
    """Simple rule-based chatbot using EU261 rules with flight verification"""

    def __init__(self):
        self.conversation_state = {}
        self.flight_verifier = FlightVerifier()
        self.claim_db = ClaimDatabase()

    def extract_number(self, text):
        """Extract numbers from text"""
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        return float(numbers[0]) if numbers else None

    def extract_email(self, text):
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None

    def extract_name(self, text):
        """Extract name from text - simple heuristic"""
        # Remove common phrases to isolate name
        text = re.sub(r'(my name is|i am|i\'m|name:)\s*', '', text.lower())
        # Look for capitalized words (2-4 words)
        words = text.split()
        name_parts = []
        for word in words:
            if word and word[0].isupper() and len(name_parts) < 4:
                name_parts.append(word)
        return ' '.join(name_parts) if name_parts else None

    def extract_flight_number(self, text):
        """Extract flight number from text (e.g., KL1234, BA456, TEST001, or just 0895)"""
        text_upper = text.upper()

        # Pattern 0: Test flights (e.g., TEST001, TEST002)
        match = re.search(r"\b(TEST\d{3})\b", text_upper)
        if match:
            return match.group(1)

        # Pattern 1: Full format with airline code (e.g., KL1234, BA456)
        match = re.search(r"\b([A-Z]{2})\s*(\d{3,4})\b", text_upper)
        if match:
            return match.group(1) + match.group(2)

        # Pattern 2: Just numbers (e.g., 0895, 1234) - assume KL airline
        match = re.search(r"\b(\d{3,4})\b", text)
        if match:
            flight_num = match.group(1)
            # For 3-4 digit numbers, assume it's a KL flight number
            # (KLM is the primary airline for this chatbot)
            if len(flight_num) >= 3:
                return f"KL{flight_num}"

        return None

    def extract_date(self, text):
        """Extract date from text (YYYY-MM-DD format or variations)"""
        # Match YYYY-MM-DD format
        match = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", text)
        if match:
            return match.group(0)

        
        # Check if we're awaiting claim submission details
        if state.get("awaiting_submission"):
            return self.process_claim_submission(message, state)
        # Match YYYY/MM/DD format
        match = re.search(r"\b(\d{4})/(\d{2})/(\d{2})\b", text)
        if match:
            return match.group(0).replace("/", "-")

        # Match "on YYYY-MM-DD" or "date YYYY-MM-DD"
        match = re.search(r"(?:on|date)\s+(\d{4})-(\d{2})-(\d{2})", text.lower())
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        return None

    def process_message(self, message, state):
        """Process user message and return response"""
        message_lower = message.lower()

        # Mark as greeted
        state["greeted"] = True

        # PRIORITY 1: Check for flight number first (before extracting delays)
        # This prevents misinterpreting flight numbers as delay hours
        flight_number = self.extract_flight_number(message)
        if flight_number:
            state["flight_number"] = flight_number  # Store for later use
            flight_date = self.extract_date(message)

            # Check if this is likely a flight verification request
            # Conditions:
            # 1. Has keywords: check, verify, lookup, flight, delayed, cancelled, denied, was
            # 2. Has a date (strong indicator)
            # 3. Message is very short (likely just a flight number, e.g., "0895")
            is_verification_request = (
                any(
                    word in message_lower
                    for word in [
                        "check",
                        "verify",
                        "lookup",
                        "flight",
                        "delayed",
                        "cancelled",
                        "denied",
                        "was",
                    ]
                )
                or flight_date is not None
                or len(message.strip()) <= 8  # Short input like "0895" or "KL1234"
            )

            if is_verification_request:
                # Call API to verify the flight
                return self.verify_flight_info(flight_number, flight_date)

        # Extract delay information
        if "delay" in message_lower or "late" in message_lower:
            delay = self.extract_number(message)
            if delay:
                state["delay_hours"] = delay
                state["scenario"] = "delay"

                # Try to extract route
                if self.extract_route_distance(message, state):
                    return self.calculate_and_respond(state)

                return f"I understand your flight was delayed {delay} hours. Could you tell me the approximate flight distance in kilometers? (e.g., 'about 1200 km' or 'Amsterdam to Barcelona is roughly 1200 km')"

        # Extract cancellation
        if "cancel" in message_lower:
            state["scenario"] = "cancellation"
            days = self.extract_number(message)
            if days:
                state["advance_notice_days"] = int(days)
            return "I understand your flight was cancelled. Could you tell me:\n1. The flight distance in km?\n2. How many days notice did you receive?"

        # Extract denied boarding
        if "denied" in message_lower or "overbook" in message_lower:
            state["scenario"] = "denied_boarding"
            state["denied_boarding"] = True
            return "I understand you were denied boarding. Could you tell me the approximate flight distance in kilometers?"

        # Extract weather/extraordinary circumstances
        if any(
            word in message_lower for word in ["weather", "storm", "strike", "medical"]
        ):
            if "weather" in message_lower or "storm" in message_lower:
                state["extraordinary_circumstance"] = "weather_conditions"
            elif "strike" in message_lower:
                state["extraordinary_circumstance"] = "air_traffic_control_strikes"
            return "I understand there were extraordinary circumstances. Unfortunately, under EU261, extraordinary circumstances like severe weather, strikes, or medical emergencies typically don't qualify for compensation. However, you still have rights to care and assistance.\n\nWould you like me to calculate if compensation might still apply, or explain your care rights?"

        # Extract distance
        distance = self.extract_number(message)
        if distance and "km" in message_lower:
            state["distance_km"] = distance

            # If we have enough info, calculate
            if state.get("delay_hours") or state.get("scenario") == "denied_boarding":
                return self.calculate_and_respond(state)
            elif state.get("scenario") == "cancellation":
                if not state.get("advance_notice_days"):
                    return (
                        "How many days notice did you receive before the cancellation?"
                    )
                else:
                    return self.calculate_and_respond(state)

        # Extract passengers
        if "passenger" in message_lower:
            num = self.extract_number(message)
            if num:
                state["passengers"] = int(num)
                return (
                    f"Got it, {int(num)} passengers. Let me recalculate...\n\n"
                    + self.calculate_and_respond(state)
                )

        # Extract city pairs (common routes)
        if self.extract_route_distance(message, state):
            if state.get("delay_hours") or state.get("scenario"):
                return self.calculate_and_respond(state)

        # Default - ask for more info
        return self.get_help_message(state)

    def extract_route_distance(self, message, state):
        """Extract distance from common city pairs"""
        routes = {
            "amsterdam barcelona": 1200,
            "amsterdam paris": 430,
            "amsterdam london": 360,
            "amsterdam new york": 5900,
            "amsterdam dubai": 5000,
            "amsterdam berlin": 580,
            "amsterdam rome": 1300,
            "amsterdam madrid": 1450,
        }

        
        # Store result in state for later submission
        state["compensation_result"] = result

        response = "📊 **Compensation Assessment**\n\n"

        if result["eligible"]:
            response += f"✅ **Good news!** You ARE eligible for compensation.\n\n"
            response += f"**Reason:** {result['reason']}\n\n"
            response += f"**Details:**\n"
            response += f"- Distance: {result['distance_km']} km ({result['distance_category']})\n"
            if result["delay_hours"] > 0:
                response += f"- Delay: {result['delay_hours']} hours\n"
            response += f"- Compensation per passenger: €{result['compensation_per_passenger']}\n"
            if result["number_of_passengers"] > 1:
                response += (
                    f"- Number of passengers: {result['number_of_passengers']}\n"
                )
                response += (
                    f"- **Total compensation: €{result['total_compensation']}**\n"
                )
            else:
                response += (
                    f"- **Total compensation: €{result['total_compensation']}**\n"
                )

            # Ask for contact information to submit claim
            if not state.get("claim_submitted"):
                response += f"\n📝 **To submit your claim, please provide:**\n"
                response += f"1. Your email address\n"
                response += f"2. Your full name\n"
                response += f"3. Flight date (YYYY-MM-DD)\n\n"
                response += f"Example: 'My email is john@email.com, my name is John Smith, flight date was 2026-03-10'\n"
                state["awaiting_submission"] = True
            else:
                response += f"\n**Next steps:**\n"
                response += f"1. File a claim with KLM customer service\n"
                response += f"2. Include your booking reference and flight details\n"
                if result["delay_hours"] > 0:
                response += f"- Delay: {result['delay_hours']} hours\n"
            response += f"- Compensation per passenger: €{result['compensation_per_passenger']}\n"
            if result["number_of_passengers"] > 1:
                response += (
                    f"- Number of passengers: {result['number_of_passengers']}\n"
                )
                response += (
                    f"- **Total compensation: €{result['total_compensation']}**\n"
                )
            else:
                response += (
                    f"- **Total compensation: €{result['total_compensation']}**\n"
                )

            response += f"\n**Next steps:**\n"
            response += f"1. File a claim with KLM customer service\n"
            response += f"2. Include your booking reference and flight details\n"
            response += f"3. You have up to 3 years to claim (varies by country)\n"
        else:
            response += f"❌ Unfortunately, you are NOT eligible for compensation.\n\n"
            response += f"**Reason:** {result['reason']}\n\n"
            if state.get("extraordinary_circumstance"):
                response += "However, you still have rights to care and assistance!\n"

        # Add care rights if delayed
        if state.get("delay_hours", 0) >= 2:
            rights = EU261Rules.get_care_assistance_rights(
                state.get("delay_hours", 0), state.get("distance_km", 0)
            )
            response += f"\n🛡️ **Your Care & Assistance Rights:**\n"
            if rights["meals_and_refreshments"]:
                response += "✅ Meals and refreshments\n"
            if rights["hotel_accommodation"]:
                response += "✅ Hotel accommodation\n"
            if rights["transport_to_accommodation"]:
                response += "✅ Transport to/from hotel\n"
            if rights["two_phone_calls"]:
                response += "✅ Two phone calls or emails\n"
            if rights["right_to_reimbursement"]:
                response += "✅ Right to full reimbursement\n"

        response += "\n\nWould you like to check another flight?"
        return response

    def get_greeting(self):
        return """👋 **Welcome to KLM Flight Compensation Assistant!**

I'm here to help you check if you're eligible for compensation under EU Regulation 261/2004.

**Two ways to check your eligibility:**

**Option 1: Verify a specific flight** (Real-time data!)
- Just tell me: "Check flight KL1234" or "Verify flight BA456"
- I'll look up the actual flight data and determine eligibility
- Note: Works for current and upcoming flights

**Option 2: Describe your situation manually**
- Was your flight delayed, cancelled, or were you denied boarding?
- How long was the delay (in hours)?
- What was your route or distance?

**Examples:**
- "Check flight KL1234"
- "Verify flight BA456 on 2026-03-16"
- "My flight from Amsterdam to Barcelona was delayed 5 hours"
- "Flight was cancelled with 3 days notice, about 1200 km"

Go ahead, tell me what happened! 😊"""

    def verify_flight_info(self, flight_number: str, flight_date: Optional[str] = None):
        """Verify flight using AviationStack API"""
        result = self.flight_verifier.verify_flight(flight_number, flight_date)
        return self.flight_verifier.format_decision(result)

    def process_claim_submission(self, message, state):
        """Process claim submission with email, name, and flight date"""
        email = self.extract_email(message)
        name = self.extract_name(message)
        flight_date = self.extract_date(message)
        
        # Store what we found
        if email:
            state["email"] = email
        if name:
            state["passenger_name"] = name
        if flight_date:
            state["flight_date"] = flight_date
            
        # Check if we have all required information
        missing = []
        if not state.get("email"):
            missing.append("email address")
        if not state.get("passenger_name"):
            missing.append("full name")
        if not state.get("flight_date"):
            missing.append("flight date (YYYY-MM-DD)")
        if not state.get("flight_number"):
            missing.append("flight number")
            
        if missing:
            return f"I still need your {', '.join(missing)}. Please provide them."
        
        # All information collected - check for duplicate
        is_duplicate, existing_claim = self.claim_db.check_duplicate(
            email=state["email"],
            flight_number=state["flight_number"],
            flight_date=state["flight_date"]
        )
        
        if is_duplicate:
            response = "⚠️ **Duplicate Claim Detected!**\n\n"
            response += f"You have already submitted a claim for this flight:\n\n"
            response += f"**Previous Submission Details:**\n"
            response += f"- Submission ID: {existing_claim['submission_id']}\n"
            response += f"- Flight: {existing_claim['flight_number']}\n"
            response += f"- Date: {existing_claim['flight_date']}\n"
            response += f"- Route: {existing_claim['route']}\n"
            response += f"- Status: {existing_claim['status'].upper()}\n"
            response += f"- Submitted on: {existing_claim['submitted_at'][:10]}\n"
            response += f"- Compensation amount: €{existing_claim['compensation_amount']}\n\n"
            response += "**You cannot submit multiple claims for the same flight.**\n\n"
            
            if existing_claim['status'] == 'pending':
                response += "Your claim is currently being processed. Please wait for a decision.\n"
            elif existing_claim['status'] == 'approved':
                response += "Your claim was already approved!\n"
            elif existing_claim['status'] == 'rejected':
                response += "Your previous claim was rejected. Contact customer service if you believe this was an error.\n"
                
            response += "\nWould you like to check a different flight?"
            state["awaiting_submission"] = False
            return response
        
        # No duplicate - submit the claim
        result = state.get("compensation_result", {})
        
        # Determine route from distance or use generic
        route = "Unknown Route"
        if state.get("departure") and state.get("arrival"):
            route = f"{state['departure']} -> {state['arrival']}"
            
        submission = self.claim_db.add_submission(
            email=state["email"],
            flight_number=state["flight_number"],
            flight_date=state["flight_date"],
            passenger_name=state["passenger_name"],
            compensation_amount=result.get("total_compensation", 0),
            delay_hours=result.get("delay_hours", 0),
            route=route,
            status="pending"
        )
        
        response = "✅ **Claim Submitted Successfully!**\n\n"
        response += f"**Submission Details:**\n"
        response += f"- Submission ID: {submission['submission_id']}\n"
        response += f"- Passenger: {submission['passenger_name']}\n"
        response += f"- Email: {submission['email']}\n"
        response += f"- Flight: {submission['flight_number']}\n"
        response += f"- Date: {submission['flight_date']}\n"
        response += f"- Compensation: €{submission['compensation_amount']}\n\n"
        response += "**Next Steps:**\n"
        response += "1. You will receive a confirmation email shortly\n"
        response += "2. Your claim will be reviewed within 7-14 business days\n"
        response += "3. Track your claim status using the Submission ID above\n\n"
        response += "Would you like to check another flight?"
        
        state["claim_submitted"] = True
        state["awaiting_submission"] = False
        
        return response

    def get_help_message(self, state):
        if not state.get("scenario"):
            return "I need more information. Please tell me:\n- Was your flight **delayed**, **cancelled**, or were you **denied boarding**?\n- How many **hours** was the delay?\n- What was the **flight distance** in kilometers or the route (e.g., Amsterdam to Paris)?"

        if not state.get("distance_km"):
            return "I need to know the flight distance. Please tell me:\n- The distance in kilometers (e.g., '1200 km')\n- Or the route (e.g., 'Amsterdam to Barcelona')"

        if state.get("scenario") == "delay" and not state.get("delay_hours"):
            return "How many hours was the delay?"

        return "I'm not sure I understood. Could you rephrase that?"


# Global chatbot instance
chatbot = SimpleClaimChatbot()
conversation_states = {}


def chat(message, history):
    """Process chat message"""
    # Use session state (simple - one user for demo)
    if "state" not in conversation_states:
        conversation_states["state"] = {}

    state = conversation_states["state"]

    # First message - show greeting
    if not history:
        return chatbot.get_greeting()

    response = chatbot.process_message(message, state)
    return response


def reset():
    """Reset conversation"""
    conversation_states.clear()
    return []


# Create Gradio interface
demo = gr.ChatInterface(
    fn=chat,
    title="✈️ KLM Flight Compensation Chatbot",
    description="""
    **Check your EU261 compensation eligibility in seconds!**
    
    Just tell me about your flight issue and I'll help you determine if you qualify for compensation.
    """,
    examples=[
        "Check flight KL1234",
        "Check flight TEST001",
        "Check flight TEST002",
        "My flight from Amsterdam to Barcelona was delayed 5 hours",
        "Flight was cancelled with 3 days notice, distance was 5900 km",
        "I was denied boarding due to overbooking on a 1200 km flight",
    ],
)

if __name__ == "__main__":
    import os

    print("=" * 60)
    print("KLM Flight Compensation Chatbot (Rule-Based)")
    print("=" * 60)
    print("\n✅ No AI model required - uses EU261 rules directly!")
    print("🚀 Starting chatbot...")

    # Allow port to be configured via environment variable or find available port
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))
    print(f"\n🌐 Open your browser at: http://localhost:{port}")
    print("\n⚠️  Press Ctrl+C to stop the server\n")

    demo.launch(server_name="127.0.0.1", server_port=port, share=False, show_error=True)
