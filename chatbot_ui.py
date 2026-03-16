"""
Interactive Chatbot Interface for KLM Flight Delay Compensation Agent
Uses Gradio for a beautiful web UI
"""

import gradio as gr
from klm_claim_agent import KLMClaimAgent
import os

# Set up authentication
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(__file__), "ai-agent-key.json"
)

# Initialize agent globally
print("Initializing KLM Claim Agent...")
agent = None


def initialize_agent():
    """Initialize the agent once"""
    global agent
    if agent is None:
        try:
            agent = KLMClaimAgent()
            return True
        except Exception as e:
            print(f"Error initializing agent: {e}")
            return False
    return True


def chat_with_agent(message, history):
    """
    Chat function for Gradio ChatInterface

    Args:
        message: User's message
        history: Chat history (list of [user_msg, bot_msg])

    Returns:
        Bot's response
    """
    if not initialize_agent():
        return "Error: Could not initialize the agent. Please check your configuration."

    try:
        # Send message to agent
        response = agent.send_message(message)
        return response
    except Exception as e:
        return f"Error: {str(e)}\n\nPlease try again or rephrase your question."


def reset_conversation():
    """Reset the conversation by creating a new agent"""
    global agent
    agent = None
    initialize_agent()
    return []


# Create Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), title="KLM Flight Compensation Agent") as demo:
    gr.Markdown(
        """
        # ✈️ KLM Flight Delay Compensation Agent
        
        Welcome! I'm here to help you determine if you're eligible for compensation under **EU Regulation 261/2004**.
        
        ### What I can help with:
        - ✅ Check if your delayed flight qualifies for compensation
        - ✅ Calculate compensation amounts (€250 - €600)
        - ✅ Explain your rights to care and assistance (meals, accommodation)
        - ✅ Guide you through cancellations and denied boarding situations
        
        ### To get started:
        Simply tell me about your flight issue! For example:
        - "My flight from Amsterdam to Barcelona was delayed 5 hours"
        - "KL1234 was cancelled with only 2 days notice"
        - "I was denied boarding due to overbooking"
        
        ---
        """
    )

    chatbot = gr.Chatbot(
        height=500,
        placeholder="<strong>Hello! I'm your KLM compensation assistant.</strong><br>How can I help you today?",
        show_label=False,
        avatar_images=(None, "https://www.klm.com/favicon.ico"),
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Type your message here... (e.g., 'My flight was delayed 4 hours')",
            show_label=False,
            scale=9,
        )
        submit = gr.Button("Send", variant="primary", scale=1)

    with gr.Row():
        clear = gr.Button("🔄 New Conversation")

    gr.Markdown(
        """
        ---
        ### 📋 Quick Examples:
        
        <details>
        <summary>Example 1: Flight Delay</summary>
        
        **You:** "My flight KL1234 from Amsterdam to Barcelona was delayed by 4 hours yesterday."
        
        **Agent will ask for:** Distance, any special circumstances
        
        **Result:** Compensation eligibility and amount
        </details>
        
        <details>
        <summary>Example 2: Flight Cancellation</summary>
        
        **You:** "My flight was cancelled. It was KL643 from Amsterdam to New York."
        
        **Agent will ask for:** When you were notified, distance
        
        **Result:** Compensation calculation based on notice period
        </details>
        
        <details>
        <summary>Example 3: Weather Delay</summary>
        
        **You:** "My flight was delayed 5 hours due to severe storms."
        
        **Result:** Explanation of extraordinary circumstances
        </details>
        
        ---
        
        ### 💡 Tips:
        - Include your **flight number** if you know it
        - Mention the **delay duration** in hours
        - State your **departure and arrival cities**
        - Mention any **special circumstances** (weather, strikes, etc.)
        - Tell me the **number of passengers** if claiming for multiple people
        
        ---
        
        **Based on EU Regulation 261/2004** | Powered by Google Vertex AI
        """
    )

    # Set up event handlers
    msg.submit(chat_with_agent, [msg, chatbot], [chatbot])
    msg.submit(lambda: "", None, [msg])  # Clear input after submit

    submit.click(chat_with_agent, [msg, chatbot], [chatbot])
    submit.click(lambda: "", None, [msg])  # Clear input after submit

    clear.click(reset_conversation, None, [chatbot])

if __name__ == "__main__":
    print("Starting KLM Flight Compensation Chatbot...")
    print("Initializing agent...")

    if initialize_agent():
        print("✅ Agent initialized successfully!")
        print("🌐 Starting web interface...")
        demo.launch(
            server_name="0.0.0.0", server_port=7860, share=False, show_error=True
        )
    else:
        print("❌ Failed to initialize agent. Please check your configuration.")
