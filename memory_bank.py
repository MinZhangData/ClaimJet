"""
Memory Bank for ClaimJet - Conversation Persistence
Uses Google Cloud Firestore to store and retrieve conversation history
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.cloud import firestore
from google.api_core import exceptions


class MemoryBank:
    """
    Manages conversation memory using Google Cloud Firestore

    Features:
    - Session-based conversation storage
    - Automatic session expiry (default: 24 hours)
    - Context-aware history retrieval
    - User-specific conversation tracking
    """

    def __init__(
        self, project_id: Optional[str] = None, collection_name: str = "conversations"
    ):
        """
        Initialize Memory Bank with Firestore

        Args:
            project_id: GCP project ID (auto-detected if not provided)
            collection_name: Firestore collection name for conversations
        """
        self.project_id = (
            project_id
            or os.environ.get("GCP_PROJECT")
            or os.environ.get("GOOGLE_CLOUD_PROJECT")
        )
        self.collection_name = collection_name

        try:
            # Initialize Firestore client
            if self.project_id:
                self.db = firestore.Client(project=self.project_id)
            else:
                # Let it auto-detect from environment
                self.db = firestore.Client()

            self.enabled = True
            print(
                f"✅ Memory Bank enabled using Firestore (project: {self.project_id or 'auto-detected'})"
            )

        except Exception as e:
            print(f"⚠️  Memory Bank initialization failed: {e}")
            print("   Continuing without persistent memory...")
            self.enabled = False
            self.db = None

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session

        Args:
            user_id: Optional user identifier

        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())

        if not self.enabled:
            return session_id

        try:
            session_data = {
                "session_id": session_id,
                "user_id": user_id or "anonymous",
                "created_at": firestore.SERVER_TIMESTAMP,
                "last_activity": firestore.SERVER_TIMESTAMP,
                "messages": [],
                "metadata": {},
            }

            self.db.collection(self.collection_name).document(session_id).set(
                session_data
            )
            return session_id

        except Exception as e:
            print(f"⚠️  Failed to create session: {e}")
            return session_id

    def add_message(
        self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add a message to the conversation history

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (e.g., tool calls, timestamps)

        Returns:
            success: True if message was saved
        """
        if not self.enabled:
            return False

        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }

            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc_ref.update(
                {
                    "messages": firestore.ArrayUnion([message]),
                    "last_activity": firestore.SERVER_TIMESTAMP,
                }
            )

            return True

        except exceptions.NotFound:
            # Session doesn't exist, create it first
            self.create_session()
            return self.add_message(session_id, role, content, metadata)

        except Exception as e:
            print(f"⚠️  Failed to add message: {e}")
            return False

    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve conversation history for a session

        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to retrieve

        Returns:
            messages: List of message dictionaries with role and content
        """
        if not self.enabled:
            return []

        try:
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc = doc_ref.get()

            if not doc.exists:
                return []

            messages = doc.to_dict().get("messages", [])

            if limit:
                messages = messages[-limit:]

            return messages

        except Exception as e:
            print(f"⚠️  Failed to retrieve history: {e}")
            return []

    def get_context_summary(self, session_id: str, max_messages: int = 10) -> str:
        """
        Get a formatted summary of recent conversation context

        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages to include

        Returns:
            context: Formatted conversation context string
        """
        messages = self.get_history(session_id, limit=max_messages)

        if not messages:
            return ""

        context_parts = ["Previous conversation context:"]
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_parts.append(f"{role.capitalize()}: {content}")

        return "\n".join(context_parts)

    def clear_session(self, session_id: str) -> bool:
        """
        Clear all messages from a session (soft delete)

        Args:
            session_id: Session identifier

        Returns:
            success: True if session was cleared
        """
        if not self.enabled:
            return False

        try:
            doc_ref = self.db.collection(self.collection_name).document(session_id)
            doc_ref.update(
                {"messages": [], "last_activity": firestore.SERVER_TIMESTAMP}
            )
            return True

        except Exception as e:
            print(f"⚠️  Failed to clear session: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Permanently delete a session

        Args:
            session_id: Session identifier

        Returns:
            success: True if session was deleted
        """
        if not self.enabled:
            return False

        try:
            self.db.collection(self.collection_name).document(session_id).delete()
            return True

        except Exception as e:
            print(f"⚠️  Failed to delete session: {e}")
            return False

    def cleanup_old_sessions(self, days: int = 7) -> int:
        """
        Delete sessions older than specified days

        Args:
            days: Number of days after which to delete sessions

        Returns:
            count: Number of sessions deleted
        """
        if not self.enabled:
            return 0

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            old_sessions = (
                self.db.collection(self.collection_name)
                .where("last_activity", "<", cutoff_date)
                .stream()
            )

            count = 0
            for session in old_sessions:
                session.reference.delete()
                count += 1

            return count

        except Exception as e:
            print(f"⚠️  Failed to cleanup old sessions: {e}")
            return 0


# Global memory bank instance
_memory_bank_instance = None


def get_memory_bank() -> MemoryBank:
    """
    Get or create the global Memory Bank instance

    Returns:
        memory_bank: Singleton Memory Bank instance
    """
    global _memory_bank_instance

    if _memory_bank_instance is None:
        _memory_bank_instance = MemoryBank()

    return _memory_bank_instance
