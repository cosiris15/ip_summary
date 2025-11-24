from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field


class LLMSettings(BaseModel):
    provider: str = Field(default="deepseek")
    api_key: str
    base_url: str = Field(default="https://api.deepseek.com")
    model: str = Field(default="deepseek-chat")
    temperature: float = Field(default=0.1)
    top_p: float = Field(default=0.9)
    max_output_tokens: int = Field(default=2000)
    request_timeout: int = Field(default=60)


class PipelineSettings(BaseModel):
    input_dir: Path
    intermediate_dir: Path
    final_dir: Path
    history_dir: Path
    concurrent_requests: int = Field(default=3)

    def resolve_paths(self, base: Path) -> "PipelineSettings":
        return PipelineSettings(
            input_dir=(base / self.input_dir).resolve(),
            intermediate_dir=(base / self.intermediate_dir).resolve(),
            final_dir=(base / self.final_dir).resolve(),
            history_dir=(base / self.history_dir).resolve(),
            concurrent_requests=self.concurrent_requests,
        )


class Settings(BaseModel):
    llm: LLMSettings
    pipeline: PipelineSettings


def load_settings(config_path: Path) -> Settings:
    """
    Load YAML config and fall back to environment variables for sensitive values.
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Missing config file at {config_path}. Please copy "
            "config/deepseek_config.example.yaml to config/deepseek_config.yaml and fill in your values."
        )

    with config_path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f) or {}

    # Allow overriding API key via environment variable to avoid storing secrets in files.
    llm_cfg = data.get("llm", {})
    llm_cfg["api_key"] = os.getenv("DEEPSEEK_API_KEY", llm_cfg.get("api_key"))
    data["llm"] = llm_cfg

    settings = Settings(**data)
    # Resolve pipeline paths relative to the project root (one level above config/ by default).
    default_base = (
        config_path.parent.parent if config_path.parent.name == "config" else config_path.parent
    )
    resolved_pipeline = settings.pipeline.resolve_paths(default_base)
    return Settings(llm=settings.llm, pipeline=resolved_pipeline)
