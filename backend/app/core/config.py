import os
from typing import List, Union
from pathlib import Path

# Directorio raíz del proyecto y del backend
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import field_validator
    USE_PYDANTIC_SETTINGS = True
except ImportError:
    from pydantic import BaseModel
    USE_PYDANTIC_SETTINGS = False


def _parse_origins(v: Union[str, List[str], None]) -> List[str]:
    if not v:
        return ["http://localhost:5173", "http://localhost:3000"]
    if isinstance(v, str):
        return [o.strip() for o in v.split(",") if o.strip()]
    return list(v)


if USE_PYDANTIC_SETTINGS:
    class Settings(BaseSettings):
        PROJECT_NAME: str = "LegadoVivo API"
        VERSION: str = "0.1.0"
        ENVIRONMENT: str = "development"
        DEBUG: bool = True
        API_PORT: int = 8080

        # PostgreSQL
        POSTGRES_USER: str = "legado_admin"
        POSTGRES_PASSWORD: str = "legado_secure_pass_2026"
        POSTGRES_HOST: str = "localhost"
        POSTGRES_PORT: int = 5432
        POSTGRES_DB: str = "legadovivo_db"
        POSTGRES_URL: str = "postgresql+psycopg2://legado_admin:legado_secure_pass_2026@localhost:5432/legadovivo_db"

        # SQLite de Respaldo Local (Ruta predecible)
        SQLITE_DB_PATH: str = str(PROJECT_ROOT / "legadovivo_dev.db")

        # MongoDB
        MONGO_HOST: str = "localhost"
        MONGO_PORT: int = 27017
        MONGO_DB: str = "legadovivo_nosql"
        MONGO_URI: str = "mongodb://mongo_admin:mongo_secure_pass_2026@localhost:27017/?authSource=admin"

        # ChromaDB
        CHROMA_HOST: str = "localhost"
        CHROMA_PORT: int = 8000
        CHROMA_PERSIST_DIRECTORY: str = str(PROJECT_ROOT / "chroma_storage")

        # Ollama & Embeddings
        OLLAMA_HOST: str = "http://localhost:11434"
        OLLAMA_MODEL: str = "llama3:8b"
        EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

        # Seguridad y JWT
        SECRET_KEY: str = "legadovivo_super_secret_jwt_key_2026_change_in_production"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días

        # CORS
        ALLOWED_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]

        @field_validator("ALLOWED_ORIGINS", mode="before")
        @classmethod
        def validate_allowed_origins(cls, v):
            return _parse_origins(v)

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )

    settings = Settings()

else:
    class Settings:
        PROJECT_NAME: str = "LegadoVivo API"
        VERSION: str = "0.1.0"
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        DEBUG: bool = True
        API_PORT: int = int(os.getenv("API_PORT", 8080))

        # PostgreSQL
        POSTGRES_USER: str = os.getenv("POSTGRES_USER", "legado_admin")
        POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "legado_secure_pass_2026")
        POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
        POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
        POSTGRES_DB: str = os.getenv("POSTGRES_DB", "legadovivo_db")
        POSTGRES_URL: str = os.getenv(
            "POSTGRES_URL",
            "postgresql+psycopg2://legado_admin:legado_secure_pass_2026@localhost:5432/legadovivo_db"
        )

        # SQLite de Respaldo Local (Ruta predecible)
        SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", str(PROJECT_ROOT / "legadovivo_dev.db"))

        # MongoDB
        MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
        MONGO_PORT: int = int(os.getenv("MONGO_PORT", 27017))
        MONGO_DB: str = os.getenv("MONGO_DB", "legadovivo_nosql")
        MONGO_URI: str = os.getenv(
            "MONGO_URI",
            "mongodb://mongo_admin:mongo_secure_pass_2026@localhost:27017/?authSource=admin"
        )

        # ChromaDB
        CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
        CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", 8000))
        CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", str(PROJECT_ROOT / "chroma_storage"))

        # Ollama & Embeddings
        OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:8b")
        EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

        # Seguridad y JWT
        SECRET_KEY: str = os.getenv("SECRET_KEY", "legadovivo_super_secret_jwt_key_2026_change_in_production")
        ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))

        # CORS
        ALLOWED_ORIGINS: List[str] = _parse_origins(os.getenv("ALLOWED_ORIGINS"))

    settings = Settings()

