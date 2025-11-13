"""Model Armor security integration for input/output validation."""

import requests
import google.auth
from google.auth.transport.requests import Request
from typing import List, Dict
import os
from .config import (
    PROJECT_ID, 
    LOCATION,
    MODEL_ARMOR_USER_ENDPOINT,
    MODEL_ARMOR_RESPONSE_ENDPOINT
)


def fetch_access_token() -> str:
    """Get Google Cloud access token for API calls."""
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token


def _sanitize_with_model_armor(endpoint: str, is_user_prompt: bool, text: str) -> str:
    """
    Sanitize text using Model Armor API.
    
    Args:
        endpoint: Model Armor endpoint URL
        is_user_prompt: True for user prompts, False for model responses
        text: Text to validate
    
    Returns:
        Original text if validation passed
    
    Raises:
        ValueError: If Model Armor blocks the text
    """
    token = fetch_access_token()
    
    payload = (
        {"userPromptData": {"text": text}}
        if is_user_prompt
        else {"modelResponseData": {"text": text}}
    )
    
    response = requests.post(
        endpoint,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    result = response.json()
    
    # Parse sanitization result
    sanitization = result.get("sanitizationResult", {})
    filter_results = sanitization.get("filterResults", {})
    
    # Check if any filter found a match
    blocked_filters = []
    for filter_name, filter_data in filter_results.items():
        filter_result = None
        if "csamFilterFilterResult" in filter_data:
            filter_result = filter_data["csamFilterFilterResult"]
        elif "raiFilterResult" in filter_data:
            filter_result = filter_data["raiFilterResult"]
        elif "piAndJailbreakFilterResult" in filter_data:
            filter_result = filter_data["piAndJailbreakFilterResult"]
        
        if filter_result and filter_result.get("matchState") == "MATCH_FOUND":
            blocked_filters.append(filter_name)
    
    if blocked_filters:
        raise ValueError(f"Model Armor blocked: {', '.join(blocked_filters)}")
    
    return text


def validate_input(user_query: str) -> str:
    """
    Validate user input for prompt injection and jailbreak attempts.
    
    Args:
        user_query: User's question
    
    Returns:
        Original query if validation passed
    
    Raises:
        ValueError: If input is blocked
    """
    return _sanitize_with_model_armor(
        MODEL_ARMOR_USER_ENDPOINT,
        True,
        user_query
    )


def validate_output(model_response: str) -> str:
    """
    Validate model output for policy violations.
    
    Args:
        model_response: Generated response from Gemini
    
    Returns:
        Original response if validation passed
    
    Raises:
        ValueError: If output is blocked
    """
    return _sanitize_with_model_armor(
        MODEL_ARMOR_RESPONSE_ENDPOINT,
        False,
        model_response
    )

