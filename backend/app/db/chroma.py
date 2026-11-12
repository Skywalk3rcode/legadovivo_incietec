import os
import logging
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

_chroma_client = None


def get_chroma_client():
    """Retorna un cliente ChromaDB embebido y persistente en disco (cero Docker)."""
    global _chroma_client
    if _chroma_client is None:
        persist_path = Path(settings.CHROMA_PERSIST_DIRECTORY).expanduser()
        if not persist_path.is_absolute():
            persist_path = Path(__file__).resolve().parents[2] / persist_path
        persist_path = persist_path.resolve()
        os.makedirs(persist_path, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB embebido inicializado en disco: '{persist_path}'")
    return _chroma_client


def get_chroma_collection(collection_name: str = "legado_capsules"):
    """Obtiene o crea una colección vectorial indexada por similitud coseno."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
