"""
OpenAI Client initialization for Google AI API compatibility.

This module provides a centralized client initialization with support for Google AI's
OpenAI-compatible interface, including thinking modes, response modalities, and image configs.
"""

import os
from openai import AsyncOpenAI, OpenAI

# Global client instances
_sync_client = None
_async_client = None


def get_sync_client() -> OpenAI:
    """Get or create the synchronous OpenAI client.

    The client is configured to use Google AI's OpenAI-compatible endpoint.
    """
    global _sync_client
    if _sync_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        base_url = os.getenv(
            "OPENAI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        _sync_client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    return _sync_client


def get_async_client() -> AsyncOpenAI:
    """Get or create the asynchronous OpenAI client.

    The client is configured to use Google AI's OpenAI-compatible endpoint.
    """
    global _async_client
    if _async_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        base_url = os.getenv(
            "OPENAI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        _async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
    return _async_client


def get_default_model() -> str:
    """Get the default model from environment variable."""
    return os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def get_default_image_model() -> str:
    """Get the default image model from environment variable."""
    return os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview")
