from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    This class defines the application settings.
    """

    # Application settings
    APP_NAME: str
    APP_VERSION: str
    OPENAI_API_KEY: str

    # File settings
    FILE_ALLOWED_TYPES: list
    FILE_MAX_SIZE: int
    FILE_DEFAULT_CHUNK_SIZE: int

    # PostgreSQL settings
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_MAIN_DATABASE: str

    # LLM settings
    GENERATION_BACKEND: str
    EMBEDDING_BACKEND: str

    # API keys
    OPENAI_API_KEY: str = None
    OPENAI_API_URL: str = None
    COHERE_API_KEY: str = None

    # Model settings
    GENERATION_MODEL_ID_LITERAL: List[str] = None
    GENERATION_MODEL_ID: str = None
    EMBEDDING_MODEL_ID: str = None
    EMBEDDING_MODEL_SIZE: int = None
    INPUT_DAFAULT_MAX_CHARACTERS: int = None
    GENERATION_DAFAULT_MAX_TOKENS: int = None
    GENERATION_DAFAULT_TEMPERATURE: float = None

    # Vector database settings
    VECTOR_DB_BACKEND_LITERAL: List[str] = None
    VECTOR_DB_BACKEND: str
    VECTOR_DB_PATH: str
    VECTOR_DB_DISTANCE_METHOD: str = None
    VECTOR_DB_PGVEC_INDEX_THRESHOLD: int = 100

    # Language settings
    PRIMARY_LANG: str = "en"
    DEFAULT_LANG: str = "en"

    class Config:
        """
        This class defines the configuration for the settings.
        """

        env_file = ".env"


def get_settings():
    """
    Gets the application settings.

    Returns:
        Settings: The application settings.
    """
    return Settings()
