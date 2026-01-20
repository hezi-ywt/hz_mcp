"""
Enhanced Image Extraction and Multi-modal Support for OpenAI API.

This module provides utilities for extracting images from OpenAI API responses
and building multi-modal prompts with reference images.
"""

import base64
import json
import mimetypes
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Sequence, Union, List, Dict, Any

from PIL import Image


@dataclass(frozen=True)
class ImageSource:
    """Represents an image source (URL, file path, or base64 data)."""

    source: str
    source_type: str  # "url", "file", "base64"

    @classmethod
    def from_string(cls, source_str: str) -> "ImageSource":
        """Create ImageSource from a string, auto-detecting type."""
        if not source_str:
            raise ValueError("Image source cannot be empty")

        source_str = source_str.strip()

        if source_str.startswith("data:image/"):
            return cls(source_str, "base64")
        if source_str.startswith("http://") or source_str.startswith("https://"):
            return cls(source_str, "url")
        return cls(source_str, "file")


class ImageLoader:
    """
    Universal image loader that handles URLs, file paths, and base64 data.
    """

    @staticmethod
    def load_from_url(url: str) -> Image.Image:
        """Load an image from a URL."""
        try:
            import requests

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            raise RuntimeError(f"Failed to load image from URL: {e}")

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> Image.Image:
        """Load an image from a local file path."""
        path = Path(file_path).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        return Image.open(path)

    @staticmethod
    def load_from_base64(base64_data: str) -> Image.Image:
        """Load an image from base64 encoded data."""
        cleaned = base64_data.replace("\n", "").replace("\r", "").replace(" ", "")
        image_data = base64.b64decode(cleaned)
        return Image.open(BytesIO(image_data))

    @staticmethod
    def load_from_data_url(data_url: str) -> Image.Image:
        """Load an image from a data URL (e.g., data:image/png;base64,...)."""
        comma_idx = data_url.find(",")
        if comma_idx == -1:
            raise ValueError("Invalid data URL format")
        base64_data = data_url[comma_idx + 1 :]
        return ImageLoader.load_from_base64(base64_data)

    @staticmethod
    def load(source: ImageSource) -> Image.Image:
        """Load an image from any supported source type."""
        if source.source_type == "url":
            return ImageLoader.load_from_url(source.source)
        elif source.source_type == "file":
            return ImageLoader.load_from_file(source.source)
        elif source.source_type == "base64":
            if source.source.startswith("data:image/"):
                return ImageLoader.load_from_data_url(source.source)
            return ImageLoader.load_from_base64(source.source)
        else:
            raise ValueError(f"Unsupported image source type: {source.source_type}")


class ImageExtractor:
    """
    Extracts PIL Images from OpenAI API responses.

    Handles multiple response formats:
    - Direct image URLs in content
    - Base64 encoded images in content
    - Markdown-formatted image links
    - Nested content structures
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def extract(self, response) -> Optional[Image.Image]:
        """
        Extract an image from an OpenAI API response.

        Args:
            response: OpenAI API response object

        Returns:
            PIL Image or None if no image found
        """
        try:
            message = response.choices[0].message

            # Try different extraction strategies in order
            strategies = [
                self._extract_from_images_field,
                self._extract_from_content_list,
                self._extract_from_content_string,
                self._extract_from_response_dict,
            ]

            for strategy in strategies:
                image = strategy(message, response)
                if image:
                    if self.verbose:
                        print(f"Image extracted using: {strategy.__name__}")
                    return image

        except Exception as e:
            print(f"Error extracting image from response: {e}")

        return None

    def _extract_from_images_field(self, message, _response) -> Optional[Image.Image]:
        """Extract from message.images field (if present)."""
        if not (hasattr(message, "images") and message.images):
            return None

        for img in message.images:
            if not isinstance(img, dict):
                continue

            image_url = img.get("image_url") or img.get("url")
            if image_url:
                try:
                    return ImageLoader.load(ImageSource.from_string(image_url))
                except Exception:
                    continue

        return None

    def _extract_from_content_list(self, message, _response) -> Optional[Image.Image]:
        """Extract from list-type content with image_url items."""
        if not hasattr(message, "content") or not isinstance(message.content, list):
            return None

        for item in message.content:
            if not isinstance(item, dict):
                continue

            # Try image_url field
            image_url = item.get("image_url")
            if image_url:
                if isinstance(image_url, dict):
                    image_url = image_url.get("url")
                if image_url:
                    try:
                        return ImageLoader.load(ImageSource.from_string(image_url))
                    except Exception:
                        continue

            # Try inline_data field
            inline_data = item.get("inline_data")
            if inline_data and isinstance(inline_data, dict):
                base64_data = inline_data.get("data")
                if base64_data:
                    try:
                        return ImageLoader.load_from_base64(base64_data)
                    except Exception:
                        continue

        return None

    def _extract_from_content_string(self, message, _response) -> Optional[Image.Image]:
        """Extract from string-type content (markdown links, data URLs, or raw base64)."""
        if not hasattr(message, "content") or not isinstance(message.content, str):
            return None

        content = message.content

        # Try markdown image syntax: ![alt](data:image/...)
        markdown_match = re.search(r"!\[.*?\]\((data:image/[^)]+)\)", content)
        if markdown_match:
            try:
                return ImageLoader.load_from_data_url(markdown_match.group(1))
            except Exception:
                pass

        # Try raw data:image URL
        if content.startswith("data:image"):
            try:
                return ImageLoader.load_from_data_url(content)
            except Exception:
                pass

        # Try to parse as JSON array
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return self._extract_from_content_list(
                    type("obj", (object,), {"content": parsed})(), None
                )
        except Exception:
            pass

        # Try as raw base64 (if long enough)
        if len(content) > 100:
            try:
                return ImageLoader.load_from_base64(content)
            except Exception:
                pass

        return None

    def _extract_from_response_dict(self, _message, response) -> Optional[Image.Image]:
        """Extract by exploring the response dictionary structure."""
        if self.verbose:
            print("Exploring response dictionary structure...")

        try:
            response_dict = (
                response.model_dump()
                if hasattr(response, "model_dump")
                else response.__dict__
            )

            if self.verbose:
                response_str = json.dumps(
                    response_dict, indent=2, ensure_ascii=False, default=str
                )
                print(f"Response structure preview:\n{response_str[:500]}")

            choices = response_dict.get("choices", [])
            if not choices:
                return None

            choice = choices[0]
            message = choice.get("message", {}) if isinstance(choice, dict) else {}
            content = message.get("content")

            if isinstance(content, str) and content.startswith("data:image"):
                if self.verbose:
                    print("Found data:image in response dictionary")
                return ImageLoader.load_from_data_url(content)

        except Exception as e:
            if self.verbose:
                print(f"Error exploring response dict: {e}")

        return None


def extract_image_from_response(
    response, verbose: bool = False
) -> Optional[Image.Image]:
    """
    Convenience function to extract an image from an OpenAI API response.

    Args:
        response: OpenAI API response object
        verbose: Enable debug output

    Returns:
        PIL Image or None

    Example:
        >>> response = client.chat.completions.create(...)
        >>> image = extract_image_from_response(response)
        >>> if image:
        ...     image.save("output.png")
    """
    return ImageExtractor(verbose).extract(response)

def image2base64(image: Image.Image) -> str:
    """Convert a PIL Image to a base64 encoded string."""
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

@dataclass(frozen=True)
class MultiModalPrompt:
    """A prompt that combines text with optional reference images."""

    text: str
    reference_images: Sequence[str] = ()


class ReferenceImageResolver:
    """
    Resolves reference image sources to proper format for API calls.
    """

    @staticmethod
    def resolve(source: str) -> str:
        """
        Resolve an image source to a URL/data URL format suitable for API calls.

        Args:
            source: File path, HTTP URL, or data URL

        Returns:
            URL or data URL string
        """
        img_source = ImageSource.from_string(source)

        if img_source.source_type == "url":
            return img_source.source
        elif img_source.source_type == "base64":
            return img_source.source
        else:  # file
            return ReferenceImageResolver._file_to_data_url(
                Path(img_source.source).expanduser()
            )

    @staticmethod
    def _file_to_data_url(path: Path) -> str:
        """Convert a local file to a data URL."""
        if not path.exists():
            raise FileNotFoundError(f"Reference image file not found: {path}")

        mime, _ = mimetypes.guess_type(str(path))
        mime = mime or "image/png"

        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"


class UserMessageBuilder:
    """
    Builds user messages for multi-modal API calls.
    """

    def __init__(self, resolver: Optional[ReferenceImageResolver] = None):
        self.resolver = resolver or ReferenceImageResolver()

    def build(self, prompt: MultiModalPrompt) -> Dict[str, Any]:
        """
        Build a user message with text and optional reference images.

        Args:
            prompt: MultiModalPrompt containing text and reference images

        Returns:
            Dictionary formatted for OpenAI API

        Example:
            >>> builder = UserMessageBuilder()
            >>> prompt = MultiModalPrompt(
            ...     text="Generate an image in this style",
            ...     reference_images=["/path/to/ref.png"]
            ... )
            >>> message = builder.build(prompt)
        """
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt.text}]  # type: ignore

        for image_source in prompt.reference_images or []:
            resolved_url = self.resolver.resolve(image_source)
            content.append({"type": "image_url", "image_url": {"url": resolved_url}})

        return {"role": "user", "content": content}


# Convenience function for common use case
def create_multi_modal_message(
    text: str, reference_images: Optional[Sequence[str]] = None
) -> Dict[str, Any]:
    """
    Create a multi-modal user message for OpenAI API.

    Args:
        text: The text prompt
        reference_images: Optional list of image sources (file paths, URLs, or data URLs)

    Returns:
        Dictionary formatted for OpenAI API

    Example:
        >>> message = create_multi_modal_message(
        ...     "Generate a futuristic city",
        ...     reference_images=["/path/to/style.png", "https://example.com/ref.jpg"]
        ... )
    """
    prompt = MultiModalPrompt(text=text, reference_images=reference_images or ())
    return UserMessageBuilder().build(prompt)
