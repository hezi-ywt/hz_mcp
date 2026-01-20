# OpenAI MCP Server 部署指南

本指南详细介绍了如何在不同环境下部署并配置您的 OpenAI MCP 服务器。

---

## 📋 部署前准备

无论选择哪种部署方式，您都需要准备以下核心配置：

1.  **OpenAI API Key**: 访问 OpenAI 或其兼容代理（如 Google Gemini OpenAI API）的密钥。
2.  **Base URL**: (可选) 如果您使用的是兼容 API (如 Gemini)，请确保设置了正确的 `OPENAI_BASE_URL`。
3.  **Python 环境**: 本地运行建议使用 Python 3.10 或更高版本。

---

## 💻 本地部署 (Local Deployment)

本地部署是最快的方式，特别适合开发和在 Claude Desktop 中使用。

### 1. 安装
```bash
git clone https://github.com/hezi-ywt/hz_mcp.git
cd hz_mcp
pip install -e .
```

### 2. 环境配置
在项目根目录创建 `.env` 文件：
```env
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://...
AUTH_ENABLED=false
```

### 3. 运行
- **调试模式**: `openai-mcp` (默认端口 8000)
- **自定义端口**: `PORT=8080 openai-mcp`

### 4. Claude Desktop 集成
编辑 `claude_desktop_config.json`，添加如下配置：
```json
{
  "mcpServers": {
    "hz_openai": {
      "command": "openai-mcp",
      "env": {
        "OPENAI_API_KEY": "your_key",
        "AUTH_ENABLED": "false"
      }
    }
  }
}
```

---

## ☁️ Cloudflare Workers 部署

本项目支持在 Cloudflare Workers 的 Python 运行时环境上部署。

### 1. 安装 Wrangler
```bash
npm install -g wrangler
```

### 2. 配置 `wrangler.toml` (示例)
在根目录下创建或修改 `wrangler.toml`：
```toml
name = "hz-mcp-server"
main = "src/openai_mcp/worker.py"
compatibility_date = "2024-04-01"
compatibility_flags = ["python_workers"]

[vars]
OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
OPENAI_MODEL = "gpt-4o-mini"
IMAGE_MODEL = "gemini-3-pro-image-preview"
AUTH_ENABLED = "true"

# 如果使用 R2，请绑定 R2 存储桶
[[r2_buckets]]
binding = "MY_BUCKET"
bucket_name = "hz-mcp-images"
```

### 3. 设置机密变量 (Secrets)
**不要在 `wrangler.toml` 中明文填写 API Key！** 使用以下命令：
```bash
wrangler secret put OPENAI_API_KEY
wrangler secret put BEARER_TOKEN
# 如果使用 R2 且通过环境变量配置
wrangler secret put R2_ACCESS_KEY_ID
wrangler secret put R2_SECRET_ACCESS_KEY
```

### 4. 部署
```bash
wrangler deploy
```

---

## 🗄️ Cloudflare R2 存储配置

启用 R2 存储后，生成的图像将直接上传到云端，服务器将返回持久化的 HTTP 链接。

### 配置步骤：
1.  在 Cloudflare 控制台创建一个 R2 Bucket。
2.  为该 Bucket 启用 **Public Access** 或绑定自定义域名。
3.  获取 R2 的 `Account ID`, `Access Key ID` 和 `Secret Access Key`。
4.  在环境变量中填写相关配置：
    - `R2_ACCOUNT_ID`: 您的 Cloudflare 账户 ID。
    - `R2_BUCKET_NAME`: Bucket 名称。
    - `R2_PUBLIC_DOMAIN`: 生成图片链接的基础域名 (例如 `https://img.example.com`)。

---

## 🔐 身份验证 (Authentication)

为了防止接口被盗刷，建议在生产环境（如部署到 Workers 后）启用 Bearer Token 认证。

**启用方法：**
1.  设置 `AUTH_ENABLED=true`。
2.  设置 `BEARER_TOKEN=your-random-long-string`。

**客户端使用：**
在 HTTP 请求头中添加：`Authorization: Bearer your-random-long-string`。

---

## ❓ 常见问题 (FAQ)

- **Q: 为什么生成的图片是 Base64 字符串？**
  - A: 默认在未配置 R2 时会返回 Base64。请检查 R2 相关环境变量是否完整。
- **Q: 为什么连接提示 502 或 Timeout？**
  - A: 请检查 `OPENAI_API_KEY` 是否有效，以及 `OPENAI_BASE_URL` 是否能够从部署环境访问。
- **Q: 是否支持所有 OpenAI 模型？**
  - A: 理论上支持所有符合 OpenAI Chat Completions 规范的模型。

---

> [!TIP]
> 建议在本地使用 SSE (Server-Sent Events) 传输方式进行调试，这样可以更直观地看到日志输出。
