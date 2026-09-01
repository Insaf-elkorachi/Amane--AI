from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "AMAN AI"
    DATABASE_URL: str = f"sqlite:///{(BACKEND_DIR / 'amane_local.db').as_posix()}"
    PUBLIC_APP_URL: str = ""

    LLM_PROVIDER: str = "openai"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_VISION_MODEL: str = "llama3.2-vision"
    OLLAMA_TIMEOUT_SECONDS: float = 90.0
    OLLAMA_KEEP_ALIVE: str = "30m"
    OLLAMA_NUM_CTX: int = 3072
    OLLAMA_NUM_PREDICT: int = 550

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_VISION_MODEL: str = "gpt-4.1-mini"
    OPENAI_VISION_IMAGE_DETAIL: str = "high"
    OPENAI_VISION_MAX_TOKENS: int = 1800
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    TTS_PROVIDER: str = "openai"
    OPENAI_TTS_MODEL: str = "gpt-4o-mini-tts"
    OPENAI_TTS_VOICE: str = "nova"
    OPENAI_STT_MODEL: str = "gpt-4o-mini-transcribe"
    STT_PROVIDER: str = "local"
    LOCAL_STT_MODEL: str = "base"
    LOCAL_STT_DEVICE: str = "cpu"
    LOCAL_STT_COMPUTE_TYPE: str = "int8"
    TTS_ENABLED: bool = True
    RAG_TOP_K: int = 4
    LLM_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=(PROJECT_DIR / ".env", BACKEND_DIR / ".env"), extra="ignore")


settings = Settings()
