"""Minimal Ollama client (stdlib only).

Talks to a local Ollama server. Set SOFTTARGET_OLLAMA / SOFTTARGET_MODEL to change them.
"""
import json
import os
import urllib.error
import urllib.request

HOST = os.environ.get("SOFTTARGET_OLLAMA", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.environ.get("SOFTTARGET_MODEL", "qwen2.5:7b-instruct")


class LLMError(Exception):
    pass


def chat(messages, tools=None, temperature=0.4):
    """Send a chat request; return the assistant message dict ({content, tool_calls?})."""
    body = {"model": MODEL, "messages": messages, "stream": False,
            "options": {"temperature": temperature}}
    if tools:
        body["tools"] = tools
    req = urllib.request.Request(HOST + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())["message"]
    except urllib.error.URLError as e:
        raise LLMError(f"Can't reach Ollama at {HOST} ({e.reason}). Is it running? Try: ollama serve") from e
    except (KeyError, ValueError) as e:
        raise LLMError(f"Unexpected reply from Ollama: {e}") from e


def health():
    try:
        with urllib.request.urlopen(HOST + "/api/tags", timeout=3) as r:
            names = [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "host": HOST, "model": MODEL, "error": str(e)}
    return {"ok": MODEL in names, "host": HOST, "model": MODEL, "installed": names,
            "error": None if MODEL in names else f"Model not installed. Run: ollama pull {MODEL}"}
