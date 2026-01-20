"""
OpenAI MCP Server - FastMCP optimized

MCP protocol layer only. Business logic is in services.py
"""

from typing import Optional, Sequence
from fastmcp import FastMCP
import os
import sys


import dotenv

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

dotenv.load_dotenv()

from openai_mcp.services import chat, generate

# 从环境变量获取API密钥
API_KEY = os.getenv("OPENAI_API_KEY", "")

# 创建FastMCP服务器实例
mcp = FastMCP("OpenAI MCP Server")


@mcp.tool()
async def chat(
    message: str,
    model: Optional[str] = None,
    system_prompt: Optional[str] = None,
) -> str:
    """Chat with text models.

    Args:
        message: User message
        model: Model to use
        system_prompt: Optional system prompt
    """
    result = await chat(
        message=message,
        model=model,
        system_prompt=system_prompt,
    )
    return result["content"] if result["success"] else f"Error: {result['error']}"


@mcp.tool()
async def make_images(
    message: str,
    reference_images: Optional[Sequence[str]] = None,
    model: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
) -> dict:
    """
    Generate images (unified interface).

    Supports:
    - Text-only: leave reference_images empty
    - With reference: provide reference_images

    Args:
        message: Text prompt
        reference_images: Optional list of image paths
        model: Model to use
        aspect_ratio: Image aspect ratio
        resolution: Image resolution
    """
    result = await generate(
        prompt=message,
        reference_images=reference_images,
        model=model or os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview"),
        aspect_ratio=aspect_ratio,
        resolution=resolution,
    )

    if result["success"]:
        return {
            "success": True,
            "image_path": result["image_data"]["path"],
            "model": result["model"],
        }
    return {"success": False, "error": result["error"]}



def main():
    """
    启动MCP服务器。

    支持通过以下环境变量配置：
    - OPENAI_API_KEY: API密钥
    - PORT: 端口号（默认8000）
    - TRANSPORT: 传输方式（默认http）
    """
    port = int(os.getenv("PORT", "8000"))
    transport = os.getenv("TRANSPORT", "http")

    mcp.run(transport=transport, port=port)


if __name__ == "__main__":
    main()
