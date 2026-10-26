from __future__ import annotations
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 优先读取项目根目录的 .env，其次读取当前工作目录的 .env。
# 这样无论从哪个目录运行 llm-cli，都能找到项目的配置。
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILES = (_PROJECT_ROOT / ".env", Path.cwd() / ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = _ENV_FILES,
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
