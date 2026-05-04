from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

# ── 各厂商 API 配置 ──────────────────────────────────────────
PROVIDERS = {
    "anthropic": {
        "url": "https://api.anthropic.com/v1/messages",
        "key_env": "ANTHROPIC_API_KEY",
    },
    "deepseek": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "key_env": "DEEPSEEK_API_KEY",
    },
    "qwen": {
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "key_env": "QWEN_API_KEY",
    },
    "glm": {
        "url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "key_env": "GLM_API_KEY",
    },
}


def call_anthropic(api_key, payload):
    """调用 Anthropic 原生格式 API"""
    req = urllib.request.Request(
        PROVIDERS["anthropic"]["url"],
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def call_openai_compat(api_key, url, payload):
    """调用 OpenAI 兼容格式 API（DeepSeek / Qwen / GLM）"""
    system_prompt = payload.get("system", "")
    messages = payload.get("messages", [])
    model = payload.get("model", "")
    max_tokens = payload.get("max_tokens", 4000)

    openai_messages = []
    if system_prompt:
        openai_messages.append({"role": "system", "content": system_prompt})
    openai_messages.extend(messages)

    openai_payload = {
        "model": model,
        "messages": openai_messages,
        "max_tokens": max_tokens,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(openai_payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()

    # 将 OpenAI 格式响应统一转换为 Anthropic 格式，方便前端统一解析
    data = json.loads(raw)
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    anthropic_resp = {
        "content": [{"type": "text", "text": text}],
        "model": model,
    }
    return json.dumps(anthropic_resp).encode("utf-8")


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            payload = json.loads(body)

            provider = payload.pop("provider", "anthropic")

            if provider == "custom":
                api_key = payload.pop("custom_key", "").strip()
                api_url = payload.pop("custom_url", "").strip()
                if not api_key or not api_url:
                    self._error(400, "自定义模式需要提供 API Key 和 Endpoint URL")
                    return
                result = call_openai_compat(api_key, api_url, payload)
            elif provider not in PROVIDERS:
                self._error(400, f"不支持的模型厂商: {provider}")
                return
            else:
                cfg = PROVIDERS[provider]
                api_key = os.environ.get(cfg["key_env"], "")
                if not api_key:
                    self._error(500, f"未配置环境变量: {cfg['key_env']}，请在 Vercel 中添加")
                    return
                if provider == "anthropic":
                    result = call_anthropic(api_key, payload)
                else:
                    result = call_openai_compat(api_key, cfg["url"], payload)

            self.send_response(200)
            self._set_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(result)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            self._error(e.code, f"上游 API 错误: {body[:300]}")
        except Exception as e:
            self._error(500, str(e))

    def _set_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _error(self, code, msg):
        self.send_response(code)
        self._set_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode("utf-8"))

    def log_message(self, format, *args):
        pass
