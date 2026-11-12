import os
from typing import List, Union
from pydantic import field_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    USE_PYDANTIC_SETTINGS = True
except ImportError:
    USE_PYDANTIC_SETTINGS = False


if USE_PYDANTIC_SETTINGS:
    class Settings(BaseSettings):
        PROJECT_NAME: str = "LegadoVivo API (PostgreSQL & MongoDB en PC)"
        VERSION: str = "0.2.0"
        ENVIRONMENT: str = "development"
        DEBUG: bool = True
        API_PORT: int = 8080

        # PostgreSQL en PC local (sin Docker)
        POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
        POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "12345")
        POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
        POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
        POSTGRES_DB: str = os.getenv("POSTGRES_DB", "legadovivo_db")
        POSTGRES_URL: str = os.getenv(
            "POSTGRES_URL",
            f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )

        # MongoDB en PC local (sin Docker)
        MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
        MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
        MONGO_DB: str = os.getenv("MONGO_DB", "legadovivo_nosql")
        MONGO_URI: str = os.getenv("MONGO_URI", f"mongodb://{MONGO_HOST}:{MONGO_PORT}")

        # Base Vectorial: ChromaDB persistente en disco
        CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_storage")

        # Ollama LLM Local
        OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:8b")
        EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

        # Supabase Auth
        SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
        SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
        SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

        # Seguridad y JWT
        SECRET_KEY: str = "legadovivo_super_secret_jwt_key_2026_change_in_production"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días

        # Vinculación por Códigos & Seguridad
        INVITE_CODE_EXPIRATION_HOURS: int = int(os.getenv("INVITE_CODE_EXPIRATION_HOURS", "48"))
        MAX_CODE_ATTEMPTS: int = int(os.getenv("MAX_CODE_ATTEMPTS", "5"))
        CODE_ATTEMPT_LOCKOUT_MINUTES: int = int(os.getenv("CODE_ATTEMPT_LOCKOUT_MINUTES", "15"))

        # CORS
        ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

        @field_validator("ALLOWED_ORIGINS", mode="before")
        @classmethod
        def parse_cors_origins(cls, v):
            if isinstance(v, str):
                v_clean = v.strip()
                if v_clean.startswith("[") and v_clean.endswith("]"):
                    import json
                    try:
                        return json.loads(v_clean)
                    except Exception:
                        pass
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            return v

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )

    settings = Settings()

else:
    class Settings:
        PROJECT_NAME: str = "LegadoVivo API (PostgreSQL & MongoDB en PC)"
        VERSION: str = "0.2.0"
        ENVIRONMENT: str = "development"
        DEBUG: bool = True
        API_PORT: int = 8080

        # PostgreSQL en PC local
        POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
        POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "12345")
        POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
        POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
        POSTGRES_DB: str = os.getenv("POSTGRES_DB", "legadovivo_db")
        POSTGRES_URL: str = os.getenv(
            "POSTGRES_URL",
            f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )

        # MongoDB en PC local
        MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
        MONGO_PORT: int = int(os.getenv("MONGO_PORT", "27017"))
        MONGO_DB: str = os.getenv("MONGO_DB", "legadovivo_nosql")
        MONGO_URI: str = os.getenv("MONGO_URI", f"mongodb://{MONGO_HOST}:{MONGO_PORT}")

        # Base Vectorial: ChromaDB persistente en disco
        CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_storage")

        # Ollama LLM Local
        OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3:8b")
        EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

        # Supabase Auth
        SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
        SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
        SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

        # Seguridad y JWT
        SECRET_KEY: str = os.getenv("SECRET_KEY", "legadovivo_super_secret_jwt_key_2026_change_in_production")
        ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

        # Vinculación por Códigos & Seguridad
        INVITE_CODE_EXPIRATION_HOURS: int = int(os.getenv("INVITE_CODE_EXPIRATION_HOURS", "48"))
        MAX_CODE_ATTEMPTS: int = int(os.getenv("MAX_CODE_ATTEMPTS", "5"))
        CODE_ATTEMPT_LOCKOUT_MINUTES: int = int(os.getenv("CODE_ATTEMPT_LOCKOUT_MINUTES", "15"))

        # CORS
        ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    settings = Settings()
