import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDBManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

db_manager = MongoDBManager()


async def connect_mongo():
    """Conecta al pool de MongoDB con Motor."""
    try:
        db_manager.client = AsyncIOMotorClient(
            settings.MONGO_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )
        db_manager.db = db_manager.client[settings.MONGO_DB]
        logger.info(f"Conexión establecida con MongoDB: base de datos '{settings.MONGO_DB}'")
    except Exception as e:
        logger.error(f"Error conectando con MongoDB: {e}")


async def close_mongo():
    """Cierra la conexión con MongoDB al apagar el servicio."""
    if db_manager.client:
        db_manager.client.close()
        logger.info("Conexión con MongoDB cerrada.")


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Retorna la instancia activa de la base de datos MongoDB."""
    return db_manager.db

