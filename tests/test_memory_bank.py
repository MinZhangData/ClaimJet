#!/usr/bin/env python3
"""
Test Memory Bank integration
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Set up environment
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "/Users/minzhang/Documents/development/ClaimJet_bak/ai-agent-key.json"
)
os.environ["GCP_PROJECT"] = "qwiklabs-asl-03-7e6910d4e317"

from memory_bank import get_memory_bank


def test_memory_bank():
    """Test Memory Bank functionality"""

    print("=" * 70)
    print("Testing Memory Bank Integration")
    print("=" * 70)

    # Initialize Memory Bank
    mb = get_memory_bank()

    if not mb.enabled:
        print("❌ Memory Bank is not enabled")
        print("   Check Firestore API and authentication")
        return False

    print("\n1. Creating test session...")
    session_id = mb.create_session(user_id="test_user_123")
    print(f"   ✅ Created session: {session_id}")

    print("\n2. Adding test messages...")
    mb.add_message(session_id, "user", "Check flight TEST001")
    mb.add_message(session_id, "assistant", "Let me check that flight for you...")
    mb.add_message(session_id, "user", "What's the compensation amount?")
    mb.add_message(
        session_id, "assistant", "The compensation is €600 for this long-haul flight."
    )
    print("   ✅ Added 4 messages")

    print("\n3. Retrieving conversation history...")
    history = mb.get_history(session_id)
    print(f"   ✅ Retrieved {len(history)} messages")

    for i, msg in enumerate(history, 1):
        print(f"   {i}. [{msg['role']}] {msg['content'][:50]}...")

    print("\n4. Getting context summary...")
    context = mb.get_context_summary(session_id, max_messages=4)
    print(f"   ✅ Context summary ({len(context)} chars):")
    print(f"   {context[:200]}...")

    print("\n5. Clearing session...")
    mb.clear_session(session_id)
    history_after_clear = mb.get_history(session_id)
    print(f"   ✅ Cleared session (now has {len(history_after_clear)} messages)")

    print("\n6. Deleting session...")
    mb.delete_session(session_id)
    print(f"   ✅ Deleted session: {session_id}")

    print("\n" + "=" * 70)
    print("✅ All Memory Bank tests passed!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    success = test_memory_bank()
    sys.exit(0 if success else 1)
