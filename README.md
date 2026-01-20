# OpenAI MCP Server (FastMCP 极速版)

[![MCP](https://img.shields.io/badge/MCP-Protocol-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/Powered%20By-FastMCP-orange)](https://github.com/jlowin/fastmcp)

一个功能强大且高度优化的 Model Context Protocol (MCP) 服务器，无缝集成 OpenAI 的对话能力与 Google Gemini 的顶级图像生成技术。通过统一的 API 接口，为您提供文本对话、视觉理解及高质量图像创作的一站式解决方案。

---

## 🌟 核心特性

- **🚀 极速响应**: 基于 FastMCP 框架重构，异步非阻塞设计，显著降低延迟。
- **🎨 万能画笔**: 深度集成 Google Gemini 3.0 Pro Image，支持文本生图、参考图生图、4K 超清输出及“思考模式”。
- **👁️ 视觉理解**: 完美支持视觉模型，可对上传的参考图进行深入分析、修改或风格迁移。
- **☁️ R2 云存储**: 自动将生成的图像上传至 Cloudflare R2，返回持久化 CDN 链接，避免 Base64 传输压力。
- **🔒 安全可控**: 内建 Bearer Token 认证机制，确保您的 API 接口不被未经授权访问。
- **🛠️ 极简集成**: 专为 Claude Desktop 优化，几行配置即可启用强大的 AI 扩展功能。

---

## 🛠️ 核心工具 (Tools)

本服务器仅提供 4 个精心设计的核心工具，涵盖了 99% 的应用场景：

| 工具名称 | 返回类型 | 用途描述 | 关键参数 |
| :--- | :--- | :--- | :--- |
| **`chat`** | `String` | 纯文本对话 | `message`, `model`, `system_prompt` |
| **`make_images`**| `Dict` | **全功能图像生成/处理** | `message`, `reference_images`, `aspect_ratio`, `resolution` |
| **`get_models`** | `Dict` | 查询支持的模型列表 | - |
| **`get_presets`**| `Dict` | 获取内置的配置预设 | - |

---

## ❤️ 快速开始

### 1. 安装环境
```bash
# 克隆仓库并进入目录
git clone https://github.com/hezi-ywt/hz_mcp.git
cd hz_mcp

# 以编辑模式安装
pip install -e .
```

### 2. 配置环境变量
创建 `.env` 文件（参考 `.env.example`）：
```env
# API 基础配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/

# 默认模型设置
OPENAI_MODEL=gpt-4o-mini
IMAGE_MODEL=gemini-3-pro-image-preview

# 存储配置 (可选：启用 R2 以获得 URL 链接)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_PUBLIC_DOMAIN=https://images.yourdomain.com
```

### 3. 运行服务器
```bash
openai-mcp
```

---

## 🖼️ 图像生成示例

### 基础文本生图
```python
make_images(
    message="一只在霓虹灯下的机械猫，赛博朋克风格",
    aspect_ratio="16:9",
    resolution="2K"
)
```

### 风格参考生图 (Image-to-Image)
```python
make_images(
    message="以此图为参考，将角色更换成宇航员制服",
    reference_images=["/path/to/character.png"],
    aspect_ratio="3:4"
)
```

---

## 🔧 Claude Desktop 配置

将以下配置添加到您的 `claude_desktop_config.json`：

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "hz_openai": {
      "command": "openai-mcp",
      "env": {
        "OPENAI_API_KEY": "你的API密钥",
        "AUTH_ENABLED": "false"
      }
    }
  }
}
```

---

## 🛳️ 部署说明

### 本地部署
直接使用 `pip install` 并在后台运行 `openai-mcp` 即可。

### Cloudflare Workers
本项目支持在 Cloudflare Workers (Python Runtime) 上运行。详细的部署步骤、环境配置及 R2 桶设置，请参考：
👉 **[详细部署文档 (DEPLOYMENT.md)](./DEPLOYMENT.md)**

---

## 📜 核心设计原则

1.  **简单即美**: 拒绝臃肿，通过极简的接口完成复杂的视觉任务。
2.  **透明授权**: 严格遵循 OpenAI API 标准头规范，支持自定义 BaseURL，完美适配各种代理前端。
3.  **可测试性**: 业务逻辑与驱动框架解耦，可在不启动 MCP 的情况下通过 `services.py` 独立测试。

---

## 🤝 贡献与反馈
如果有任何问题或建议，欢迎提交 Issue。

**License**: MIT
