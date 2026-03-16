"""
Simple Rule-Based Chatbot for KLM Flight Delay Compensation
Works without requiring Vertex AI models
"""

import gradio as gr
from eu261_rules import EU261Rules
import re
import os


class SimpleClaimChatbot:
    """Simple rule-based chatbot using EU261 rules"""

    def __init__(self):
        self.conversation_state = {}

    def extract_number(self, text):
        """Extract numbers from text"""
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        return float(numbers[0]) if numbers else None

    def process_message(self, message, state):
        """Process user message and return response"""
        message_lower = message.lower()

        # Mark as greeted
        state["greeted"] = True

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

        message_lower = message.lower()
        for route, distance in routes.items():
            if all(city in message_lower for city in route.split()):
                state["distance_km"] = distance
                return True
        return False

    def calculate_and_respond(self, state):
        """Calculate compensation and format response"""
        result = EU261Rules.calculate_claim_amount(
            delay_hours=state.get("delay_hours", 0),
            distance_km=state.get("distance_km", 0),
            cancellation=state.get("scenario") == "cancellation",
            denied_boarding=state.get("denied_boarding", False),
            extraordinary_circumstance=state.get("extraordinary_circumstance"),
            advance_notice_days=state.get("advance_notice_days"),
            number_of_passengers=state.get("passengers", 1),
        )

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

**Please tell me about your situation:**
- Was your flight delayed, cancelled, or were you denied boarding?
- How long was the delay (in hours)?
- What was your route or distance?

**Examples:**
- "My flight from Amsterdam to Barcelona was delayed 5 hours"
- "Flight was cancelled with 3 days notice, about 1200 km"
- "I was denied boarding on a 400 km flight"

Go ahead, tell me what happened! 😊"""

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
        "My flight from Amsterdam to Barcelona was delayed 5 hours",
        "Flight was cancelled with 3 days notice, distance was 5900 km",
        "I was denied boarding due to overbooking on a 1200 km flight",
        "My flight was delayed 6 hours due to bad weather, about 400 km",
    ],
)

if __name__ == "__main__":
    print("=" * 60)
    print("KLM Flight Compensation Chatbot (Rule-Based)")
    print("=" * 60)
    print("\n✅ No AI model required - uses EU261 rules directly!")
    print("🚀 Starting chatbot...")
    print("\n🌐 Open your browser at: http://localhost:7860")
    print("\n⚠️  Press Ctrl+C to stop the server\n")

    demo.launch(server_name="127.0.0.1", server_port=7860, share=False, show_error=True)
