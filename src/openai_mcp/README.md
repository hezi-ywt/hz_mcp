# OpenAI MCP Server

A Model Context Protocol (MCP) server that provides OpenAI chat and image generation capabilities.

## Features

- **Chat**: Interact with OpenAI's GPT models through MCP protocol
- **Image Generation**: Create images using DALL-E models (dall-e-2, dall-e-3)
- **Multi-modal Chat**: Chat with vision-capable models using reference images (file paths, URLs, or base64)
- **Universal Image Extraction**: Automatically extract images from various API response formats
- **Image Loading**: Load images from URLs, file paths, or base64 data URLs

## Quick Start

### Installation

1. Install dependencies:
```bash
pip install -e .
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

3. Run the server:
```bash
openai-mcp
```

Or directly with Python:
```bash
python -m openai_mcp.server
```

## MCP Tools

### `chat(message, model?, system_prompt?, temperature?)`

Chat with OpenAI's language models.

**Parameters:**
- `message` (required): The user's message
- `model` (optional): Model to use (default: from env or gpt-4o-mini)
- `system_prompt` (optional): System prompt to guide behavior
- `temperature` (optional): Randomness (0.0-2.0)

**Example:**
```python
chat(message="What is quantum computing?")
```

### `generate_image(prompt, model?, size?, quality?, n?)`

Generate images using DALL-E.

**Parameters:**
- `prompt` (required): Detailed image description
- `model` (optional): Model to use (default: dall-e-3)
- `size` (optional): Image size (default: 1024x1024)
- `quality` (optional): 'standard' or 'hd' (dall-e-3 only)
- `n` (optional): Number of images (default: 1)

**Example:**
```python
generate_image(
    prompt="A serene mountain landscape at sunset",
    size="1024x1024",
    quality="standard"
)
```

### `chat_with_images(message, reference_images?, model?, system_prompt?, temperature?, verbose?)`

Chat with vision-capable models using reference images. Supports text-only conversations or multi-modal conversations with reference images.

**Parameters:**
- `message` (required): The user's message
- `reference_images` (optional): List of image sources (file paths, URLs, or data URLs)
- `model` (optional): Model to use (default: from env or gpt-4o-mini)
- `system_prompt` (optional): System prompt to guide behavior
- `temperature` (optional): Randomness (0.0-2.0)
- `verbose` (optional): Enable debug output for image extraction (default: False)

**Examples:**

```python
# Text-only conversation
chat_with_images(message="Explain quantum computing")

# With reference images (file paths)
chat_with_images(
    message="Generate an image in this style",
    reference_images=["/path/to/ref1.png", "/path/to/ref2.jpg"]
)

# With URLs
chat_with_images(
    message="Describe what you see",
    reference_images=["https://example.com/image.jpg"]
)

# With base64 data URLs
chat_with_images(
    message="Generate similar images",
    reference_images=["data:image/png;base64,..."]
)
```

## Direct Library Usage

You can use the library directly without MCP for more control:

### Image Extraction

```python
from openai import OpenAI
from openai_mcp.image_utils import extract_image_from_response

client = OpenAI(api_key="your_key")

response = client.chat.completions.create(
    model="gemini-3-pro-image-preview",
    messages=[{"role": "user", "content": "Generate a cat"}]
)

# Automatically extract image from response
image = extract_image_from_response(response, verbose=True)
if image:
    image.save("output.png")
```

### Multi-modal Prompts

```python
from openai_mcp.image_utils import create_multi_modal_message

# Simple text message
message = create_multi_modal_message("Describe this image")

# With reference images
message = create_multi_modal_message(
    "Generate a similar image",
    reference_images=["/path/to/ref.png", "https://example.com/ref.jpg"]
)

# Use with OpenAI client
client.chat.completions.create(
    model="gemini-3-pro-image-preview",
    messages=[message]
)
```

### Universal Image Loading

```python
from openai_mcp.image_utils import ImageLoader, ImageSource

# Load from URL
source = ImageSource.from_string("https://example.com/image.jpg")
image = ImageLoader.load(source)

# Load from file path
source = ImageSource.from_string("/path/to/image.png")
image = ImageLoader.load(source)

# Load from base64 data URL
source = ImageSource.from_string("data:image/png;base64,iVBORw0KG...")
image = ImageLoader.load(source)
```

## API Reference

### `ImageExtractor`

Extracts PIL Images from OpenAI API responses, handling multiple response formats.

```python
from openai_mcp.image_utils import ImageExtractor

extractor = ImageExtractor(verbose=True)
image = extractor.extract(response)
```

**Supported Formats:**
- Direct image URLs in content
- Base64 encoded images
- Markdown-formatted image links
- Nested content structures

### `ImageLoader`

Universal image loader supporting multiple source types.

**Methods:**
- `load_from_url(url)`: Load from HTTP URL
- `load_from_file(path)`: Load from local file
- `load_from_base64(data)`: Load from base64 string
- `load_from_data_url(data_url)`: Load from data URL
- `load(source)`: Auto-detect and load from any source

### `UserMessageBuilder`

Builds multi-modal user messages for vision models.

```python
from openai_mcp.image_utils import UserMessageBuilder, MultiModalPrompt

prompt = MultiModalPrompt(
    text="Generate a futuristic city",
    reference_images=["/path/to/style.png", "https://example.com/ref.jpg"]
)
builder = UserMessageBuilder()
message = builder.build(prompt)
```

### `ReferenceImageResolver`

Resolves various image source formats to URLs/data URLs for API calls.

```python
from openai_mcp.image_utils import ReferenceImageResolver

resolver = ReferenceImageResolver()

# Resolve file path to data URL
url = resolver.resolve("/path/to/image.png")

# Pass through URL
url = resolver.resolve("https://example.com/image.jpg")

# Pass through data URL
url = resolver.resolve("data:image/png;base64,...")
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_BASE_URL` | OpenAI API base URL | https://api.openai.com/v1 |
| `OPENAI_MODEL` | Default chat model | gpt-4o-mini |
| `IMAGE_MODEL` | Default image model | dall-e-3 |

## Model Support

### Chat Models
- GPT-4o
- GPT-4o-mini
- GPT-4-turbo
- GPT-3.5-turbo
- And other compatible OpenAI models

### Image Models (DALL-E)
- dall-e-3 (recommended, higher quality)
- dall-e-2 (faster, more options)

### Vision/Image Generation Models
- gemini-3-pro-image-preview
- gemini-2.5-flash-image
- Any OpenAI-compatible vision-capable model

## Examples

After installation, run the example scripts:

```bash
# Direct library usage examples
python examples/enhanced_usage.py

# MCP client test examples
python examples/mcp_client_enhanced.py
```

## Generated Images

When using `chat_with_images` with vision-capable image generation models, generated images are automatically saved to:

```
generated_images/
└── image_<uuid>.png
```

Images are saved with unique filenames based on UUID to prevent overwrites.

## Configuration with Claude Desktop

To use this MCP server with Claude Desktop, add it to your config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "openai": {
      "command": "openai-mcp",
      "env": {
        "OPENAI_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Project Structure

```
openai_mcp/
├── __init__.py
├── server.py          # MCP server with tools
└── image_utils.py     # Image extraction and loading utilities
```

## See Also

- [Main README](../README.md) - Complete documentation and setup guide
- [Examples](../examples/) - Usage examples and tests

## License

MIT
