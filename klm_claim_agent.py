"""
KLM Flight Delay Claim Agent using Vertex AI and EU261 Rules
"""

import vertexai
from vertexai.generative_models import (
    GenerativeModel,
    FunctionDeclaration,
    Tool,
    Content,
    Part,
)
import json
from typing import Dict, List, Optional
from eu261_rules import EU261Rules

# Initialize Vertex AI
PROJECT_ID = "qwiklabs-asl-03-7e6910d4e317"
LOCATION = "us-central1"

vertexai.init(project=PROJECT_ID, location=LOCATION)


class KLMClaimAgent:
    """
    AI Agent for handling KLM flight delay compensation claims based on EU261 regulations.
    """

    def __init__(self):
        """Initialize the KLM Claim Agent with Gemini model and tools."""

        # Define function declarations for the agent tools
        self.calculate_compensation_func = FunctionDeclaration(
            name="calculate_compensation",
            description="Calculate EU261 compensation eligibility and amount for a flight delay or cancellation",
            parameters={
                "type": "object",
                "properties": {
                    "flight_number": {
                        "type": "string",
                        "description": "KLM flight number (e.g., KL1234)",
                    },
                    "delay_hours": {
                        "type": "number",
                        "description": "Flight delay in hours",
                    },
                    "distance_km": {
                        "type": "number",
                        "description": "Flight distance in kilometers",
                    },
                    "departure_airport": {
                        "type": "string",
                        "description": "Departure airport code (e.g., AMS)",
                    },
                    "arrival_airport": {
                        "type": "string",
                        "description": "Arrival airport code (e.g., JFK)",
                    },
                    "is_eu_flight": {
                        "type": "boolean",
                        "description": "Whether flight departs from EU airport",
                        "default": True,
                    },
                    "is_eu_destination": {
                        "type": "boolean",
                        "description": "Whether destination is within EU/EEA/Switzerland",
                        "default": True,
                    },
                    "cancellation": {
                        "type": "boolean",
                        "description": "Whether flight was cancelled",
                        "default": False,
                    },
                    "denied_boarding": {
                        "type": "boolean",
                        "description": "Whether passenger was denied boarding",
                        "default": False,
                    },
                    "extraordinary_circumstance": {
                        "type": "string",
                        "description": "Reason if extraordinary circumstance applies (e.g., weather_conditions, air_traffic_control_strikes)",
                        "default": None,
                    },
                    "advance_notice_days": {
                        "type": "number",
                        "description": "Days of advance notice for cancellation",
                        "default": None,
                    },
                    "number_of_passengers": {
                        "type": "integer",
                        "description": "Number of passengers in the claim",
                        "default": 1,
                    },
                },
                "required": ["delay_hours", "distance_km"],
            },
        )

        self.get_care_rights_func = FunctionDeclaration(
            name="get_care_and_assistance_rights",
            description="Get passenger rights to care and assistance (meals, accommodation, etc.) based on flight delay",
            parameters={
                "type": "object",
                "properties": {
                    "delay_hours": {
                        "type": "number",
                        "description": "Flight delay in hours",
                    },
                    "distance_km": {
                        "type": "number",
                        "description": "Flight distance in kilometers",
                    },
                },
                "required": ["delay_hours", "distance_km"],
            },
        )

        # Create tool with function declarations
        self.tools = Tool(
            function_declarations=[
                self.calculate_compensation_func,
                self.get_care_rights_func,
            ]
        )

        # System instruction for the agent
        self.system_instruction = """You are a helpful AI assistant for KLM Royal Dutch Airlines, specialized in helping passengers with flight delay compensation claims under EU Regulation 261/2004 (EU261).

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

Always be honest about eligibility and provide clear reasoning based on EU261 regulations.
"""

        # Initialize the Gemini model
        # Try different model versions in order of preference
        model_names = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
            "gemini-1.0-pro",
        ]

        for model_name in model_names:
            try:
                self.model = GenerativeModel(
                    model_name,
                    system_instruction=self.system_instruction,
                    tools=[self.tools],
                )
                print(f"Successfully initialized with model: {model_name}")
                break
            except Exception as e:
                print(f"Failed to initialize {model_name}: {str(e)}")
                if model_name == model_names[-1]:
                    raise Exception("No available Gemini models found in this project")

        # Start chat session
        self.chat = self.model.start_chat()

    def calculate_compensation(self, **kwargs) -> Dict:
        """Calculate compensation using EU261 rules."""
        return EU261Rules.calculate_claim_amount(
            delay_hours=kwargs.get("delay_hours", 0),
            distance_km=kwargs.get("distance_km", 0),
            is_eu_flight=kwargs.get("is_eu_flight", True),
            is_klm_operated=True,  # Always True for KLM agent
            cancellation=kwargs.get("cancellation", False),
            denied_boarding=kwargs.get("denied_boarding", False),
            extraordinary_circumstance=kwargs.get("extraordinary_circumstance"),
            advance_notice_days=kwargs.get("advance_notice_days"),
            is_eu_destination=kwargs.get("is_eu_destination", True),
            number_of_passengers=kwargs.get("number_of_passengers", 1),
        )

    def get_care_and_assistance_rights(
        self, delay_hours: float, distance_km: int
    ) -> Dict:
        """Get care and assistance rights."""
        return EU261Rules.get_care_assistance_rights(delay_hours, distance_km)

    def process_function_call(self, function_call) -> str:
        """Process function calls from the model."""
        function_name = function_call.name
        function_args = {}

        # Parse function arguments
        for key, value in function_call.args.items():
            function_args[key] = value

        # Execute the appropriate function
        if function_name == "calculate_compensation":
            result = self.calculate_compensation(**function_args)
        elif function_name == "get_care_and_assistance_rights":
            result = self.get_care_and_assistance_rights(**function_args)
        else:
            result = {"error": f"Unknown function: {function_name}"}

        return json.dumps(result, indent=2)

    def send_message(self, message: str) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            message: User's message

        Returns:
            Agent's response as a string
        """
        response = self.chat.send_message(message)

        # Check if the model wants to call a function
        while response.candidates[0].content.parts[0].function_call:
            function_call = response.candidates[0].content.parts[0].function_call

            # Process the function call
            function_response = self.process_function_call(function_call)

            # Send function response back to the model
            response = self.chat.send_message(
                Content(
                    parts=[
                        Part.from_function_response(
                            name=function_call.name,
                            response={"content": function_response},
                        )
                    ]
                )
            )

        # Return the final text response
        return response.text

    def get_conversation_history(self) -> List[Dict]:
        """Get the conversation history."""
        history = []
        for message in self.chat.history:
            role = message.role
            content = ""

            for part in message.parts:
                if part.text:
                    content += part.text
                elif part.function_call:
                    content += f"[Function Call: {part.function_call.name}]"
                elif part.function_response:
                    content += f"[Function Response]"

            history.append({"role": role, "content": content})

        return history


def main():
    """Main function to run the KLM Claim Agent."""
    print("=" * 60)
    print("KLM Flight Delay Compensation Agent")
    print("Based on EU Regulation 261/2004")
    print("=" * 60)
    print()

    agent = KLMClaimAgent()

    print(
        "Agent: Hello! I'm your KLM compensation assistant. How can I help you today?"
    )
    print()

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
            print("\nAgent: Thank you for contacting KLM. Have a great day!")
            break

        try:
            response = agent.send_message(user_input)
            print(f"\nAgent: {response}\n")
        except Exception as e:
            print(f"\nError: {str(e)}\n")
            print("Please try again or contact KLM customer service directly.\n")


if __name__ == "__main__":
    main()
