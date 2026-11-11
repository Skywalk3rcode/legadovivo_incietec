import logging
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

logger = logging.getLogger(__name__)

_chroma_client = None


def get_chroma_client():
    """Retorna un cliente singleton de ChromaDB (vía HTTP o almacenamiento local)."""
    global _chroma_client
    if _chroma_client is None:
        try:
            # Intento de conexión al servidor ChromaDB levantado en Docker
            _chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            # Verificación de conexión
            _chroma_client.heartbeat()
            logger.info(f"Conectado exitosamente al servidor ChromaDB en {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        except Exception as e:
            logger.warning(
                f"Servidor ChromaDB HTTP no disponible ({e}). Utilizando cliente persistente local en '{settings.CHROMA_PERSIST_DIRECTORY}'"
            )
            _chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
    return _chroma_client


def get_chroma_collection(collection_name: str = "legado_capsules"):
    """Obtiene o crea una colección vectorial para un usuario o para el sistema general."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

