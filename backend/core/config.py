from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "AMAN AI"
    DATABASE_URL: str = f"sqlite:///{(BACKEND_DIR / 'amane_local.db').as_posix()}"
    PUBLIC_APP_URL: str = ""

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_TTS_MODEL: str = "gpt-4o-mini-tts"
    OPENAI_TTS_VOICE: str = "alloy"
    TTS_ENABLED: bool = True

    RAG_TOP_K: int = 4
    LLM_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"), extra="ignore")


settings = Settings()




