"""
LLM Client — Local Service + Google Gemini Fallback
=====================================================
This module provides a single interface to two LLM backends:

  1. LOCAL SERVICE (primary)  — University GPU cluster running Qwen2.5
  2. GOOGLE GEMINI (fallback) — Free tier via Google AI Studio

The module auto-detects which service is available. If the local service
is unreachable, it falls back to Gemini automatically.

Setup:
    # In your .env file set ONE or BOTH of these:
    LLM_SERVICE_URL=http://localhost:8000
    LLM_API_TOKEN=your-local-token

    GEMINI_API_KEY=your-google-api-key
"""

import os
import re
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8000")
LLM_API_TOKEN = os.getenv("LLM_API_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

LOCAL_HEADERS = {
    "Authorization": f"Bearer {LLM_API_TOKEN}",
    "Content-Type": "application/json",
}

# Which backend is active — set automatically by check_health()
_active_backend = None  # "local" | "gemini" | None


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def check_health() -> dict:
    """Check which LLM backend is available.

    Returns a dict with:
        status: "online" or "offline"
        backend: "local" or "gemini" or None
        model: name of the model
        model_loaded: bool
    """
    global _active_backend

    # Try local first
    try:
        resp = requests.get(
            f"{LLM_SERVICE_URL}/health",
            headers=LOCAL_HEADERS,
            timeout=5,
        )
        data = resp.json()
        if data.get("model_loaded"):
            _active_backend = "local"
            return {
                "status": "online",
                "backend": "local",
                "model": data.get("model", "Unknown"),
                "model_loaded": True,
            }
    except Exception:
        pass

    # Try Gemini
    if GEMINI_API_KEY:
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models"
                f"?key={GEMINI_API_KEY}"
            )
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                _active_backend = "gemini"
                return {
                    "status": "online",
                    "backend": "gemini",
                    "model": GEMINI_MODEL,
                    "model_loaded": True,
                }
        except Exception:
            pass

    _active_backend = None
    return {
        "status": "offline",
        "backend": None,
        "model": None,
        "model_loaded": False,
    }


# ---------------------------------------------------------------------------
# Local service helpers
# ---------------------------------------------------------------------------

def format_chat_prompt(messages: list[dict]) -> str:
    """Convert chat messages to Qwen2.5 chat template format."""
    prompt = ""
    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")
        prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt


def _local_generate(prompt: str, max_tokens=2048, temperature=0.7) -> str:
    """Send a raw prompt to the local service and poll for the result."""
    resp = requests.post(
        f"{LLM_SERVICE_URL}/generate",
        headers=LOCAL_HEADERS,
        json={
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    )
    resp.raise_for_status()
    task_id = resp.json()["task_id"]

    while True:
        result = requests.get(
            f"{LLM_SERVICE_URL}/result/{task_id}",
            headers=LOCAL_HEADERS,
        ).json()
        if result["status"] == "completed":
            return result["response"]
        elif result["status"] == "failed":
            raise RuntimeError(
                f"Generation failed: {result.get('error', 'Unknown')}"
            )
        time.sleep(0.5)


def _local_chat(messages: list[dict], max_tokens=2048, temperature=0.7) -> str:
    """Chat via the local service."""
    prompt = format_chat_prompt(messages)
    return _local_generate(prompt, max_tokens, temperature)


# ---------------------------------------------------------------------------
# Gemini helpers
# ---------------------------------------------------------------------------

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def _gemini_chat(messages: list[dict], max_tokens=2048, temperature=0.7) -> str:
    """Chat via Google Gemini API.

    Converts the OpenAI-style messages list into Gemini's format.
    """
    # Separate system prompt from conversation
    system_text = ""
    contents = []

    for msg in messages:
        role = msg["role"]
        content = msg.get("content", "")

        if role == "system":
            system_text += content + "\n"
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
        elif role == "tool":
            # Wrap tool results as user messages for Gemini
            tool_name = msg.get("name", "tool")
            contents.append({
                "role": "user",
                "parts": [{"text": f"[Tool result from {tool_name}]:\n{content}"}],
            })

    # Ensure contents is not empty
    if not contents:
        contents = [{"role": "user", "parts": [{"text": "Hello"}]}]

    body = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    # Add system instruction if present
    if system_text.strip():
        body["systemInstruction"] = {
            "parts": [{"text": system_text.strip()}]
        }

    resp = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json=body,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    # Extract text from response
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return f"[Gemini returned unexpected format: {json.dumps(data)[:200]}]"


# ---------------------------------------------------------------------------
# Public API — simple chat (no tool calling)
# ---------------------------------------------------------------------------

def chat(messages: list[dict], max_tokens=2048, temperature=0.7, tools=None):
    """Send a chat request to the active LLM backend.

    If `tools` is provided, returns a dict with:
        content: the text response (without tool_call tags)
        raw: the full raw response
        tool_calls: list of {name, arguments} dicts

    If `tools` is None, returns a plain string.
    """
    global _active_backend

    # Auto-detect backend if not yet set
    if _active_backend is None:
        check_health()

    # Build messages with tool descriptions if provided
    if tools:
        return _chat_with_tools(messages, tools, max_tokens, temperature)

    # Simple chat — return string
    if _active_backend == "local":
        return _local_chat(messages, max_tokens, temperature)
    elif _active_backend == "gemini":
        return _gemini_chat(messages, max_tokens, temperature)
    else:
        raise RuntimeError(
            "No LLM backend available. Check your .env settings.\n"
            "Either start the local service or set GEMINI_API_KEY."
        )


# ---------------------------------------------------------------------------
# Tool-calling support
# ---------------------------------------------------------------------------

def _inject_tool_descriptions(messages: list[dict], tools: list[dict]) -> list[dict]:
    """Inject tool definitions into the system prompt for text-based tool calling."""
    tool_text = "You have access to the following tools:\n\n"
    for tool in tools:
        tool_text += f"### {tool['name']}\n"
        tool_text += f"{tool['description']}\n"
        params = tool.get("parameters", {}).get("properties", {})
        if params:
            tool_text += "Parameters:\n"
            for pname, pinfo in params.items():
                desc = pinfo.get("description", "")
                ptype = pinfo.get("type", "string")
                tool_text += f"  - {pname} ({ptype}): {desc}\n"
        tool_text += "\n"

    tool_text += (
        "To call a tool, output EXACTLY this format (you may call multiple tools):\n"
        '<tool_call>\n{"name": "tool_name", "arguments": {"param": "value"}}\n</tool_call>\n\n'
        "If you do NOT need to call a tool, just respond with your final answer as plain text.\n"
        "When you have gathered enough information, give your final answer WITHOUT any tool_call tags.\n"
    )

    new_messages = []
    injected = False
    for msg in messages:
        if msg["role"] == "system" and not injected:
            new_messages.append({
                "role": "system",
                "content": msg["content"] + "\n\n" + tool_text,
            })
            injected = True
        else:
            new_messages.append(msg)

    if not injected:
        new_messages.insert(0, {"role": "system", "content": tool_text})

    return new_messages


def _parse_tool_calls(text: str) -> list[dict]:
    """Extract tool calls from the response.

    Handles two formats:
      1. <tool_call>{"name": ..., "arguments": ...}</tool_call>  (preferred)
      2. Raw JSON object / list when the model skips the tags
    """
    calls = []

    # Try tagged format first
    tag_pattern = r"<tool_call>\s*(\{.*?\})\s*</tool_call>"
    for match in re.findall(tag_pattern, text, re.DOTALL):
        try:
            parsed = json.loads(match)
            calls.append({
                "name": parsed.get("name", ""),
                "arguments": parsed.get("arguments", {}),
            })
        except json.JSONDecodeError:
            continue

    if calls:
        return calls

    # Fallback: try to parse the whole response as a bare JSON tool call
    stripped = text.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
            return [{"name": parsed["name"], "arguments": parsed.get("arguments", {})}]
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and "name" in item and "arguments" in item:
                    calls.append({"name": item["name"], "arguments": item.get("arguments", {})})
    except (json.JSONDecodeError, ValueError):
        pass

    return calls


def _strip_tool_calls(text: str) -> str:
    """Remove tool call JSON from text to get the content-only response."""
    # Remove tagged blocks
    cleaned = re.sub(
        r"<tool_call>\s*\{.*?\}\s*</tool_call>", "", text, flags=re.DOTALL
    ).strip()

    # If what remains is itself a bare JSON tool call, return empty string
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict) and "name" in parsed and "arguments" in parsed:
            return ""
        if isinstance(parsed, list) and all(
            isinstance(i, dict) and "name" in i for i in parsed
        ):
            return ""
    except (json.JSONDecodeError, ValueError):
        pass

    return cleaned


def _chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    max_tokens: int,
    temperature: float,
) -> dict:
    """Chat with tool-calling support. Returns structured response."""
    enriched = _inject_tool_descriptions(messages, tools)

    if _active_backend == "local":
        raw = _local_chat(enriched, max_tokens, temperature)
    elif _active_backend == "gemini":
        raw = _gemini_chat(enriched, max_tokens, temperature)
    else:
        raise RuntimeError("No LLM backend available.")

    tool_calls = _parse_tool_calls(raw)
    content = _strip_tool_calls(raw)

    return {
        "content": content,
        "raw": raw,
        "tool_calls": tool_calls,
    }


# ---------------------------------------------------------------------------
# Convenience: generate (raw prompt, local only)
# ---------------------------------------------------------------------------

def generate(prompt: str, max_tokens=2048, temperature=0.7) -> str:
    """Send a raw prompt. Uses local service if available, otherwise Gemini."""
    global _active_backend
    if _active_backend is None:
        check_health()

    if _active_backend == "local":
        return _local_generate(prompt, max_tokens, temperature)
    elif _active_backend == "gemini":
        # Wrap raw prompt as a user message for Gemini
        return _gemini_chat(
            [{"role": "user", "content": prompt}],
            max_tokens,
            temperature,
        )
    else:
        raise RuntimeError("No LLM backend available.")


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Checking LLM service health...")
    health = check_health()
    print(f"  Status  : {health['status']}")
    print(f"  Backend : {health['backend']}")
    print(f"  Model   : {health['model']}")

    if health["model_loaded"]:
        print("\nSending test message...")
        reply = chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one sentence."},
        ])
        print(f"  Reply: {reply}")
    else:
        print("\nNo backend available. Set up your .env file.")
