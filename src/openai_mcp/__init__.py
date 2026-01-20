"""OpenAI MCP Server (Simplified)"""

__version__ = "0.1.0"

from openai_mcp.services import chat, generate

__all__ = [
    "__version__",
    "chat",
    "generate",
]
