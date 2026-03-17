"""
ClaimJet Chatbot UI - ADK Version with Memory Bank
Uses Google ADK agent for intelligent flight compensation assistance
Includes persistent conversation memory using Firestore
"""

import os
import gradio as gr
from adk_agent import FlightCompensationAgent
from memory_bank import get_memory_bank

# Initialize the ADK agent and Memory Bank
agent = FlightCompensationAgent()
memory_bank = get_memory_bank()

# Store session IDs per Gradio session
session_store = {}


def chat_with_agent(message: str, history: list, session_id: str = None) -> str:
    """
    Process user message through ADK agent with Memory Bank

    Args:
        message: User's input message
        history: Conversation history (from Gradio UI)
        session_id: Session identifier for persistent memory

    Returns:
        Agent's response
    """
    try:
        # Create session if not exists
        if not session_id:
            session_id = memory_bank.create_session()

        # Get agent response with session context
        response = agent.chat(message, history, session_id=session_id)
        return response

    except Exception as e:
        return f"❌ Error: {str(e)}\n\nPlease try again or check your API key configuration."


# Create the Gradio interface
def create_ui():
    """Create the Gradio chat interface"""

    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        font-family: 'Arial', sans-serif;
    }
    .message {
        padding: 10px;
        border-radius: 8px;
    }
    """

    with gr.Blocks(
        css=custom_css, title="ClaimJet - Flight Compensation Assistant"
    ) as demo:
        # Session state for memory bank
        session_id_state = gr.State(value=None)

        gr.Markdown(
            """
            # ✈️ ClaimJet - EU261 Flight Compensation Assistant (ADK + Memory Bank)
            
            I can help you check if your flight qualifies for EU261 compensation.
            **Your conversation history is saved for context across messages.**
            
            **Try these:**
            - `Check flight TEST001` - Long-haul test flight (€600)
            - `Check flight TEST002 2026-03-12` - Short-haul test flight (€250)
            - `My flight was delayed 5 hours and flew 2000km` - Manual calculation
            - `What are the EU261 delay thresholds?` - Get information
            
            **Or enter a real flight:**
            - `Check flight KL1234 2026-03-15` - Real flight verification
            """
        )

        chatbot = gr.Chatbot(
            label="Chat with ClaimJet Agent",
            height=500,
            show_label=True,
        )

        msg = gr.Textbox(
            label="Your Message",
            placeholder="Enter a flight number (e.g., 'Check flight KL1234') or ask a question...",
            lines=2,
        )

        with gr.Row():
            submit = gr.Button("Send", variant="primary")
            clear = gr.Button("Clear Chat")
            new_session = gr.Button("New Session", variant="secondary")

        def respond(message, chat_history, session_id):
            """Handle user message and update chat"""
            if not message.strip():
                return "", chat_history, session_id

            # Create session if needed
            if not session_id:
                session_id = memory_bank.create_session()

            bot_response = chat_with_agent(message, chat_history, session_id)

            # Gradio 6.0 format: list of dicts with 'role' and 'content'
            if chat_history is None:
                chat_history = []

            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": bot_response})

            return "", chat_history, session_id

        def clear_chat(session_id):
            """Clear the chat history"""
            if session_id and memory_bank.enabled:
                memory_bank.clear_session(session_id)
            return [], session_id

        def start_new_session():
            """Start a completely new session"""
            new_session_id = memory_bank.create_session()
            return [], new_session_id

        msg.submit(
            respond, [msg, chatbot, session_id_state], [msg, chatbot, session_id_state]
        )
        submit.click(
            respond, [msg, chatbot, session_id_state], [msg, chatbot, session_id_state]
        )
        clear.click(clear_chat, [session_id_state], [chatbot, session_id_state])
        new_session.click(start_new_session, None, [chatbot, session_id_state])

        gr.Markdown(
            """
            ---
            **Powered by Google Gemini 2.5 Flash with ADK + Memory Bank**
            
            💡 **How it works:**
            - Uses AI agents with function calling
            - Automatically selects the right tool for your query
            - Verifies real flight data (when API is configured)
            - Calculates accurate EU261 compensation
            - **Remembers conversation context across messages** 🧠
            
            🧪 **Test Flights Available:**
            - TEST001: Long-haul AMS→JFK, delayed 6h45m (€600)
            - TEST002: Short-haul AMS→BCN, delayed 4h15m (€250)
            
            💾 **Memory Bank:**
            - Conversations are saved in Google Cloud Firestore
            - Clear Chat: Clears UI and Memory Bank history
            - New Session: Starts a fresh conversation with new session ID
            """
        )

    return demo


if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY environment variable is not set!")
        print("Please set it with: export GEMINI_API_KEY='your-key-here'")
        print("Get your key from: https://aistudio.google.com/apikey")
        exit(1)

    print("✅ Starting ClaimJet ADK Chatbot...")
    print(f"✅ Using Gemini 2.5 Flash model")
    print(f"✅ API Key configured")

    # Get port from environment or use default
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7860))

    # Create and launch the UI
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        css="""
        .gradio-container {
            font-family: 'Arial', sans-serif;
        }
        .message {
            padding: 10px;
            border-radius: 8px;
        }
        """,
    )
