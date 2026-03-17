"""
Configuration management for ClaimJet
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # Gemini API
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")

    # GCP Configuration
    GCP_PROJECT: Optional[str] = os.environ.get("GCP_PROJECT") or os.environ.get(
        "GOOGLE_CLOUD_PROJECT"
    )
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )

    # Firestore
    FIRESTORE_COLLECTION: str = os.environ.get("FIRESTORE_COLLECTION", "conversations")

    # AeroDataBox API
    AERODATABOX_API_KEY: str = os.environ.get(
        "AERODATABOX_API_KEY", "cmmtn2ach000djm04lbnkeege"
    )

    # Gradio Server
    GRADIO_SERVER_PORT: int = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    GRADIO_SERVER_NAME: str = os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0")

    # Model Configuration
    MODEL_NAME: str = "gemini-2.5-flash"
    MODEL_TEMPERATURE: float = 0.3

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is required. "
                "Get your key from: https://aistudio.google.com/apikey"
            )
        return True


# Export config instance
config = Config()
