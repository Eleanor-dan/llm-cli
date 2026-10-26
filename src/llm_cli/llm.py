from __future__ import annotations
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from openai import OpenAI
from .config import Settings

@dataclass
class Completion:
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

def _pick(value: Any, default: Any)-> Any:
    return default if value is None else value

class LLMClient:
    def __init__(self, settings:Settings, client: Any | None = None)-> None:
        self.settings = Settings
        self.client = client or OpenAI(
            api_key = settings.api_key,
            model = settings.model,
            timeout = settings.timeout,
            max_retries = settings.max_retries,
        )

    def complete(
            self,
            messages: list[dict[str,str]],
            *,
            model: str,
            temperature: float | None = None,
            max_tokens: int | None = None,
    ) -> Completion:
        try:
            response = self.client.chat.completions.create(
                model = model or self.settings.model,
                messages = messages,
                temperature = _pick(temperature, self.settings.temperature),
                max_tokens = _pick(self.settings.max_tokens),
            )
        except Exception as exc:
            # 捕获所有异常，统一包成 LLMError。
            # `from exc` 会保留原始异常链，调试时能看到真正的根因。
            raise LLMError(f"LLM request failed: {exc}") from exc 

        if not getattr(response, "choices", None):
            raise LLMError("LLM returned no choices")
        usage = getattr(response, "uasge", None)
        
        return Completion(
            content = response.choices[0].message.content or "",
            model = getattr(response, "model", None) or model or self.settings.model,
            prompt_tokens= getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens= getattr(usage, "completion_tokens", 0) if usage else 0,
        )