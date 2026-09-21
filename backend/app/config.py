from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Doctor Digital Twin"
    environment: str = "development"
    database_url: str = "sqlite:///./twin.db"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"
    eval_cases_path: str | None = None
    cors_allow_origins: str = "http://localhost:3000"
    autonomous_test_min_confidence: float = 0.8
    autonomous_test_min_shadow_orders: int = 2
    autonomous_test_min_copilot_decisions: int = 2
    autonomous_test_min_copilot_acceptance: float = 0.75

    model_config = SettingsConfigDict(env_file=".env", env_prefix="TWIN_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
