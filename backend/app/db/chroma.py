import os
import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

_chroma_client = None


def get_chroma_client():
    """Retorna un cliente ChromaDB embebido y persistente en disco (cero Docker)."""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        logger.info(f"ChromaDB embebido inicializado en disco: '{settings.CHROMA_PERSIST_DIRECTORY}'")
    return _chroma_client


def get_chroma_collection(collection_name: str = "legado_capsules"):
    """Obtiene o crea una colección vectorial indexada por similitud coseno."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
