# OpenAI MCP Server (FastMCP优化版)

统一的MCP服务器，支持OpenAI对话和Google AI图像生成。

## 项目结构

```
hz_mcp/
├── src/openai_mcp/
│   ├── __init__.py       # 包入口
│   ├── client.py         # OpenAI客户端管理
│   ├── server.py         # MCP服务器（FastMCP优化）
│   ├── services.py       # 业务逻辑（纯函数，可独立测试）
│   └── image_utils.py    # 图像工具
├── .env
├── .env.example
├── README.md
└── pyproject.toml
```

## MCP工具

仅提供4个核心工具：

| 工具 | 返回类型 | 用途 | 参数 |
|------|---------|------|------|
| `chat` | str | 文本对话 | message, model, system_prompt, temperature |
| `make_images` | dict | 统一图像生成 | message, reference_images, model, aspect_ratio, resolution, reasoning_effort, thinking_budget |
| `get_models` | dict | 模型查询 | - |
| `get_presets` | dict | 配置预设 | - |

## 使用方式

### 文本对话

```python
chat(message="Hello", model="gpt-4o-mini", temperature=0.7)
```

### 图像生成

**文本生成图像：**
```python
make_images(
    message="A sunset over the ocean",
    aspect_ratio="16:9",
    resolution="2K"
)
```

**参考图生成：**
```python
make_images(
    message="Modify this character's outfit",
    reference_images=["/path/to/character.png", "/path/to/outfit.png"],
    aspect_ratio="5:4",
    resolution="1K"
)
```

## Header授权

服务器通过环境变量`OPENAI_API_KEY`读取API密钥，在调用OpenAI/Gemini API时使用自定义headers（不使用api_key参数）。

### 环境变量配置

创建 `.env` 文件：

```env
# API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gpt-4o-mini
IMAGE_MODEL=gemini-3-pro-image-preview

# Server Configuration
PORT=8000
TRANSPORT=http
```

### Claude Desktop 配置

编辑配置文件：
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openai": {
      "command": "openai-mcp",
      "env": {
        "OPENAI_API_KEY": "your_api_key_here",
        "OPENAI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "IMAGE_MODEL": "gemini-3-pro-image-preview"
      }
    }
  }
}
```

## 支持的模型

### 图像模型
- `gemini-2.5-flash-image` - 最多3张参考图，不支持4K
- `gemini-3-pro-image-preview` - 最多14张参考图，支持4K和思考模式

### 宽高比
`"1:1"`, `"2:3"`, `"3:2"`, `"3:4"`, `"4:3"`, `"4:5"`, `"5:4"`, `"9:16"`, `"16:9"`, `"21:9"`

### 分辨率
`"1K"`, `"2K"`, `"4K"` (仅`gemini-3-pro`支持4K）

### 思考模式
`reasoning_effort`: `'minimal'`, `'low'`, `'medium'`, `'high'`
`thinking_budget`: `'1,024'`, `'8,192'`, `'24,576'`

## 安装

```bash
pip install -e .
```

## 运行

```bash
openai-mcp
```

**自定义端口：**
```bash
PORT=8080 openai-mcp
```

## 独立测试

业务逻辑可以不启动MCP直接测试：

```bash
# 测试文本对话
python -c "from openai_mcp import chat; import asyncio; result = asyncio.run(chat('Hello')); print(result)"

# 测试图像生成
python -c "from openai_mcp import generate; import asyncio; result = asyncio.run(generate('A cat', aspect_ratio='16:9')); print(result)"

# 查询模型
python -c "from openai_mcp import get_models; print(get_models())"
```

## 核心设计原则

1. **单一职责**: `chat` 处理文本，`make_images` 处理图像
2. **统一接口**: `make_images` 一个函数处理文本生成和参考图生成
3. **可测试性**: 业务逻辑在 `services.py`，可独立于MCP测试
4. **最小依赖**: 只依赖必要的库（fastmcp, openai, pillow）
5. **FastMCP优化**: 工具函数使用`async def`，直接`await`调用，避免事件循环冲突
6. **Header授权**: 通过环境变量`OPENAI_API_KEY`配置，自动添加`Authorization: Bearer {api_key}` header
