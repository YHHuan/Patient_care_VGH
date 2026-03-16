from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # VGH credentials
    vgh_username: str = ""
    vgh_password: str = ""
    doctor_code: str = ""

    # OpenRouter
    openrouter_api_key: str = ""
    ai_model: str = "anthropic/claude-sonnet-4-6"

    # Delay config (seconds)
    request_delay_min: float = 1.5
    request_delay_max: float = 3.5
    patient_delay_min: float = 30.0
    patient_delay_max: float = 60.0

    # AI rounds
    max_rounds: int = 3

    # Paths
    cache_dir: str = "cache_data"
    output_dir: str = "output_data"


settings = Settings()
