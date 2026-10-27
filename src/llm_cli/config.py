from __future__ import annotations
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = 'utf-8',
        env_prefix = 'LLM_',
        extra = "ignore",
    )

    api_key: str = Field(default = "", description = "")
    base_url: str = Field(default = "https://api.openai.com/v1", description = "")
    model: str = Field(default = "gpt-4o-mini", description = "")

    timeout: float = Field(default = 60.0, gt = 0)
    max_retries: int = Field(default = 2, ge = 0, le = 10)
    temperature: float = Field(default = 0.7, ge = 0, le = 2)
    max_tokens: int = Field(default = 1024, ge = 1, le = 32768)
