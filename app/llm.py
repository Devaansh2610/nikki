import json
import re
from collections.abc import Generator

import httpx

from app.config import settings


class ChatLLM:
    def __init__(self) -> None:
        self._client = httpx.Client(timeout=120.0)

    def stream_reply(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        if settings.use_openai:
            yield from self._stream_openai(messages)
        else:
            yield from self._stream_ollama(messages)

    def _stream_ollama(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
        payload = {
            "model": settings.ollama_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.8,
                "num_predict": 1024,
            },
        }

        with self._client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                data = json.loads(line)
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token
                if data.get("done"):
                    break

    def _stream_openai(self, messages: list[dict[str, str]]) -> Generator[str, None, None]:
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        payload = {
            "model": settings.openai_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.8,
            "max_tokens": 1024,
        }

        with self._client.stream("POST", url, headers=headers, json=payload) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                chunk = line[6:]
                if chunk == "[DONE]":
                    break
                data = json.loads(chunk)
                delta = data["choices"][0].get("delta", {})
                token = delta.get("content", "")
                if token:
                    yield token

    def close(self) -> None:
        self._client.close()
