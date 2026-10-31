"""
MCP server that lets Claude call a local model (e.g. Qwen3.8-27B, Gemma)

Two backends (choose with the LLM_BACKEND variable):
  - "ollama"  : Ollama / LM Studio in Ollama mode   (default http://localhost:11434)
  - "openai"  : vLLM / SGLang / LM Studio / llama.cpp server, OpenAI-compatible
                (default http://localhost:8000/v1)

Install:
    pip install "mcp[cli]<2" httpx   (this file uses the mcp 1.x FastMCP API)
"""
import os
import httpx
from mcp.server.fastmcp import FastMCP

BACKEND = os.environ.get("LLM_BACKEND", "ollama").lower()
BASE_URL = os.environ.get(
    "LLM_BASE_URL",
    "http://localhost:11434" if BACKEND == "ollama" else "http://localhost:8000/v1",
).rstrip("/")
DEFAULT_MODEL = os.environ.get("LLM_DEFAULT_MODEL", "qwen3:8b")
API_KEY = os.environ.get("LLM_API_KEY", "local")
TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "600"))
# summarize_file_locally may only read files under this folder (default: this project).
ALLOWED_ROOT = os.path.realpath(
    os.environ.get("LLM_ALLOWED_ROOT", os.path.dirname(os.path.abspath(__file__)))
)

mcp = FastMCP("local-llm")


def _chat(messages: list[dict], model: str, think: bool) -> str:
    if BACKEND == "ollama":
        r = httpx.post(
            f"{BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "think": think,
                "options": {"temperature": 1.0 if think else 0.7,
                            "top_p": 0.95 if think else 0.8, "top_k": 20},
            },
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]

    # OpenAI-compatible (vLLM / SGLang)
    body = {
        "model": model,
        "messages": messages,
        "temperature": 1.0 if think else 0.7,
        "top_p": 0.95 if think else 0.8,
        "top_k": 20,
        "presence_penalty": 0.0 if think else 1.5,
        "chat_template_kwargs": {"enable_thinking": think},
    }
    r = httpx.post(
        f"{BASE_URL}/chat/completions",
        json=body,
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


@mcp.tool()
def list_local_models() -> list[str]:
    """List the models available on the local server."""
    if BACKEND == "ollama":
        r = httpx.get(f"{BASE_URL}/api/tags", timeout=30)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    r = httpx.get(f"{BASE_URL}/models",
                  headers={"Authorization": f"Bearer {API_KEY}"}, timeout=30)
    r.raise_for_status()
    return [m["id"] for m in r.json().get("data", [])]


@mcp.tool()
def ask_local_llm(prompt: str, model: str = DEFAULT_MODEL, system: str = "",
                  think: bool = False) -> str:
    """Send a prompt to the local model and return its answer.
    think=True enables thinking mode (more accurate but slower); use it for hard tasks.
    """
    messages = [{"role": "system", "content": system}] if system else []
    messages.append({"role": "user", "content": prompt})
    return _chat(messages, model, think)


@mcp.tool()
def summarize_file_locally(path: str, instruction: str = "Summarize the key points in English, as at most 5 short bullets. No emojis, headings or closing remarks.",
                           model: str = DEFAULT_MODEL) -> str:
    """Have the local model read a text file on this machine and summarize it.
    Claude sees only the summary, never the original file content.
    """
    real = os.path.realpath(os.path.expanduser(path))
    try:
        inside = os.path.commonpath([real, ALLOWED_ROOT]) == ALLOWED_ROOT
    except ValueError:  # different drives on Windows
        inside = False
    if not inside:
        return f"Refused: {path} is outside {ALLOWED_ROOT}"
    if os.path.basename(real).startswith(".env"):
        return "Refused: .env files are never read"
    with open(real, encoding="utf-8", errors="ignore") as f:
        text = f.read()[:200000]
    return _chat([{"role": "user", "content": f"{instruction}\n\n---\n{text}"}],
                 model, think=False)


if __name__ == "__main__":
    mcp.run()
