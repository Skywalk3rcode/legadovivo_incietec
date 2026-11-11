import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    is_connected: bool = False


db_manager = MongoDBManager()


async def connect_mongo() -> bool:
    """
    Inicializa el cliente Motor y comprueba activamente la disponibilidad
    del servidor de MongoDB mediante un comando 'ping'.
    """
    try:
        db_manager.client = AsyncIOMotorClient(
            settings.MONGO_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=3000
        )
        # Comprobar la conexión real enviando ping al servidor
        await db_manager.client.admin.command('ping')
        db_manager.db = db_manager.client[settings.MONGO_DB]
        db_manager.is_connected = True
        logger.info(f"Conexión verificada exitosamente con MongoDB: base de datos '{settings.MONGO_DB}'")
        return True
    except Exception as e:
        db_manager.is_connected = False
        db_manager.db = None
        logger.warning(
            f"MongoDB en {settings.MONGO_HOST}:{settings.MONGO_PORT} no está disponible ({e}). "
            "Las operaciones NoSQL quedarán en espera o funcionarán con memoria de respaldo."
        )
        return False


async def check_mongo_health() -> Dict[str, Any]:
    """Verifica el estado de salud de MongoDB para el endpoint de diagnóstico."""
    if not db_manager.client:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": "Cliente MongoDB no inicializado"
        }
    try:
        await db_manager.client.admin.command('ping')
        db_manager.is_connected = True
        return {
            "status": "healthy",
            "connected": True,
            "database": settings.MONGO_DB,
            "host": f"{settings.MONGO_HOST}:{settings.MONGO_PORT}"
        }
    except Exception as e:
        db_manager.is_connected = False
        return {
            "status": "unhealthy",
            "connected": False,
            "host": f"{settings.MONGO_HOST}:{settings.MONGO_PORT}",
            "error": str(e)
        }


async def close_mongo():
    """Cierra la conexión con MongoDB al apagar el servicio."""
    if db_manager.client:
        db_manager.client.close()
        db_manager.is_connected = False
        logger.info("Conexión con MongoDB cerrada.")


def get_mongo_db() -> Optional[AsyncIOMotorDatabase]:
    """Retorna la instancia activa de la base de datos MongoDB."""
    return db_manager.db


