"""
OpenAI MCP Server - Simplified Architecture

Unified business logic for chat and image generation.
All functions are independent of MCP framework and can be tested directly.
"""

import os
import uuid
import base64
from io import BytesIO
from typing import Optional, Sequence
from PIL import Image
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from openai_mcp.client import (
    get_async_client,
    get_default_model,
    get_default_image_model,
)
from openai_mcp.image_utils import extract_image_from_response, image2base64
from openai_mcp.r2_storage import upload_image_to_r2, is_r2_configured


async def chat(
    message: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    temperature: Optional[float] = None,
) -> dict:
    """Chat with text-only models.

    Args:
        message: The user's message
        model: Model to use
        system_prompt: Optional system prompt
        temperature: Optional temperature (0.0-2.0)

    Returns:
        dict with success, content, model, or error
    """
    try:
        client = get_async_client()
        model_name = model or get_default_model()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        kwargs = {"model": model_name, "messages": messages}
        if temperature is not None:
            kwargs["temperature"] = temperature

        response = await client.chat.completions.create(**kwargs)

        return {
            "success": True,
            "content": response.choices[0].message.content,
            "model": model_name,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "model": model or "unknown"}


async def generate(
    prompt: str,
    reference_images: Optional[Sequence[str]] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """
    Unified image generation interface.

    Supports text-only and reference image generation.
    Reference code standard with OpenAI-compatible Gemini API.

    Args:
        prompt: Text prompt
        reference_images: Optional list of image paths
        aspect_ratio: "1:1", "16:9", etc.
        resolution: "1K", "2K", "4K"        
        model: Model to use

    Returns:
        dict with success, image_data, model, or error
    """
    try:
        client = get_async_client()
        target_model = model or get_default_image_model()

        # Build content
        content = [{"type": "text", "text": prompt}]

        # Add reference images
        if reference_images:
            for img_path in reference_images:
                if os.path.exists(img_path):
                    with Image.open(img_path) as img:
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")
                        if max(img.size) > 1024:
                            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                        buffered = BytesIO()
                        img.save(buffered, format="JPEG", quality=85)
                        b64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        content.append(
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64_data}"
                                },
                            }
                        )

        # Build extra_body
        extra_body = {"modalities": ["image"]}
        if aspect_ratio:
            extra_body["aspect_ratio"] = aspect_ratio
        if resolution:
            extra_body["resolution"] = resolution

        # Call API
        response = await client.chat.completions.create(
            model=target_model,
            messages=[{"role": "user", "content": content}],
            extra_body=extra_body,
        )

        # Extract and save image
        image = extract_image_from_response(response, verbose=False)
        if not image:
            return {
                "success": False,
                "error": "No image generated",
                "model": target_model,
            }

        # Upload to R2 if configured, otherwise use base64
        if is_r2_configured():
            try:
                # Upload to R2 and get public URL
                image_url = upload_image_to_r2(image)
                return {
                    "success": True,
                    "image_data": {"path": image_url, "format": "url"},
                    "model": target_model,
                }
            except Exception as e:
                # Fallback to base64 if R2 upload fails
                print(f"R2 upload failed, falling back to base64: {str(e)}")
                return {
                    "success": True,
                    "image_data": {"path": image2base64(image), "format": "base64"},
                    "model": target_model,
                    "warning": f"R2 upload failed: {str(e)}"
                }
        else:
            # R2 not configured, use base64
            return {
                "success": True,
                "image_data": {"path": image2base64(image), "format": "base64"},
                "model": target_model,
            }
    except Exception as e:
        return {"success": False, "error": str(e), "model": target_model or "unknown"}
