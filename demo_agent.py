"""
Demo script for the KLM Claim Agent
This script demonstrates the agent with predefined scenarios.
"""

from klm_claim_agent import KLMClaimAgent
import os

# Set the service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "/Users/minzhang/Documents/development/ClaimJet/ai-agent-key.json"
)


def demo_scenario(agent, scenario_name, user_messages):
    """Run a demo scenario with the agent."""
    print("=" * 70)
    print(f"Scenario: {scenario_name}")
    print("=" * 70)
    print()

    for message in user_messages:
        print(f"You: {message}")
        try:
            response = agent.send_message(message)
            print(f"\nAgent: {response}\n")
        except Exception as e:
            print(f"\nError: {str(e)}\n")
            break

    print()


def main():
    """Run demo scenarios."""
    print("=" * 70)
    print("KLM Flight Delay Compensation Agent - Demo")
    print("=" * 70)
    print("\nInitializing agent...")

    try:
        agent = KLMClaimAgent()
        print("Agent initialized successfully!\n")

        # Scenario 1: Eligible delay claim
        demo_scenario(
            agent,
            "Eligible Delay Claim - Amsterdam to Barcelona",
            [
                "Hello, my flight KL1234 from Amsterdam to Barcelona was delayed by 4 hours yesterday.",
                "The distance is about 1200 kilometers. Can I get compensation?",
            ],
        )

        # Create a new agent for scenario 2
        agent2 = KLMClaimAgent()

        # Scenario 2: Weather delay (extraordinary circumstances)
        demo_scenario(
            agent2,
            "Weather Delay - No Compensation",
            [
                "My flight was delayed 5 hours due to severe storms. Can I claim compensation?",
                "The flight was from Amsterdam to London, about 350 km.",
            ],
        )

        # Create a new agent for scenario 3
        agent3 = KLMClaimAgent()

        # Scenario 3: Long-haul flight cancellation
        demo_scenario(
            agent3,
            "Flight Cancellation - Long Distance",
            [
                "My flight KL643 from Amsterdam to New York (about 5900 km) was cancelled with only 3 days notice.",
                "There were 2 passengers. What compensation can we get?",
            ],
        )

        print("=" * 70)
        print("Demo completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\nError initializing agent: {str(e)}")
        print("\nPlease ensure:")
        print("1. Google Cloud APIs are enabled")
        print("2. Service account has proper permissions")
        print("3. Project ID is correct")


if __name__ == "__main__":
    main()
