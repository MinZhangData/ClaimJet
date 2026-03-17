"""
Model Armor callbacks for the KLM Claim Agent.

Sanitizes user prompts (before_model_callback) and model responses
(after_model_callback) via Google Cloud Model Armor.

Requires the following environment variables to be active:
  MODEL_ARMOR_TEMPLATE_ID  - full resource name of the template, e.g.
      projects/PROJECT/locations/LOCATION/templates/TEMPLATE_ID
  GOOGLE_CLOUD_LOCATION    - region that matches the template (default: us-central1)

If MODEL_ARMOR_TEMPLATE_ID is not set the callbacks are no-ops so the agent
still works without Model Armor configured.
"""

import os
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai.types import Content, Part

_ma_client = None


def _get_client():
    """Lazily initialise the Model Armor client (cached after first call)."""
    global _ma_client
    if _ma_client is None:
        try:
            from google.cloud import modelarmor_v1
            from google.api_core.client_options import ClientOptions

            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
            _ma_client = modelarmor_v1.ModelArmorClient(
                client_options=ClientOptions(
                    api_endpoint=f"modelarmor.{location}.rep.googleapis.com"
                )
            )
        except Exception as e:
            print(f"[Model Armor] Client init failed: {e}")
    return _ma_client


def _is_flagged(sanitization_result) -> bool:
    """Return True if Model Armor matched a policy violation."""
    try:
        from google.cloud.modelarmor_v1.types import FilterMatchState
        return (
            sanitization_result.filter_match_state == FilterMatchState.MATCH_FOUND
        )
    except Exception:
        return False


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Sanitize the user prompt before it reaches the LLM.

    Returns a blocking LlmResponse if Model Armor flags the content,
    otherwise returns None so the normal LLM call proceeds.
    """
    template_id = os.environ.get("MODEL_ARMOR_TEMPLATE_ID")
    if not template_id:
        return None

    # Extract text from the last user turn
    user_text = ""
    for content in reversed(llm_request.contents or []):
        if content.role == "user":
            user_text = " ".join(
                part.text for part in (content.parts or []) if part.text
            )
            break

    if not user_text:
        return None

    try:
        from google.cloud import modelarmor_v1

        client = _get_client()
        if client is None:
            return None

        response = client.sanitize_user_prompt(
            request=modelarmor_v1.SanitizeUserPromptRequest(
                name=template_id,
                user_prompt_data=modelarmor_v1.DataItem(text=user_text),
            )
        )

        if _is_flagged(response.sanitization_result):
            print(f"[Model Armor] Blocked user prompt.")
            return LlmResponse(
                content=Content(
                    role="model",
                    parts=[Part(text="I'm sorry, I can't process that request as it violates our safety policies.")],
                ),
                turn_complete=True,
            )

    except Exception as e:
        print(f"[Model Armor] before_model_callback error: {e}")

    return None


def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """Sanitize the model response before it is returned to the user.

    Returns a replacement LlmResponse if Model Armor flags the content,
    otherwise returns None so the original response is used as-is.
    """
    template_id = os.environ.get("MODEL_ARMOR_TEMPLATE_ID")
    if not template_id:
        return None

    if not llm_response.content:
        return None

    response_text = " ".join(
        part.text for part in (llm_response.content.parts or []) if part.text
    )

    if not response_text:
        return None

    try:
        from google.cloud import modelarmor_v1

        client = _get_client()
        if client is None:
            return None

        response = client.sanitize_model_response(
            request=modelarmor_v1.SanitizeModelResponseRequest(
                name=template_id,
                model_response_data=modelarmor_v1.DataItem(text=response_text),
            )
        )

        if _is_flagged(response.sanitization_result):
            print(f"[Model Armor] Blocked model response.")
            return LlmResponse(
                content=Content(
                    role="model",
                    parts=[Part(text="I'm sorry, I'm unable to provide that response.")],
                ),
                turn_complete=True,
            )

    except Exception as e:
        print(f"[Model Armor] after_model_callback error: {e}")

    return None
