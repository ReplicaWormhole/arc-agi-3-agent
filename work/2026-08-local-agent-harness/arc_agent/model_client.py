"""Provider-neutral development-only chat model adapter.

The agent controller must be able to use a local or remote inference server
without changing its reasoning/verifier interfaces. This module intentionally
does not issue environment actions and is never called by the unit tests.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol, Sequence
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ModelEndpointConfig:
    base_url: str
    model: str
    api_key: str | None = None
    timeout_seconds: float = 120.0

    @classmethod
    def from_environment(cls) -> "ModelEndpointConfig":
        base_url = os.environ.get("ARC_MODEL_BASE_URL")
        model = os.environ.get("ARC_MODEL_NAME")
        if not base_url or not model:
            raise RuntimeError(
                "Set ARC_MODEL_BASE_URL and ARC_MODEL_NAME before enabling a model proposer."
            )
        return cls(
            base_url=base_url,
            model=model,
            api_key=os.environ.get("ARC_MODEL_API_KEY"),
        )


class ChatModel(Protocol):
    def complete(self, messages: Sequence[ChatMessage]) -> str: ...


class OpenAICompatibleChatModel:
    """Minimal client for local or remote OpenAI-compatible chat endpoints."""

    def __init__(self, config: ModelEndpointConfig) -> None:
        self.config = config

    def request_payload(self, messages: Sequence[ChatMessage]) -> dict[str, object]:
        return {
            "model": self.config.model,
            "messages": [message.__dict__ for message in messages],
            "temperature": 0,
        }

    def complete(self, messages: Sequence[ChatMessage]) -> str:
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        request = Request(
            url,
            data=json.dumps(self.request_payload(messages)).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=self.config.timeout_seconds) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        try:
            return str(payload["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("model endpoint returned an invalid chat completion") from error
