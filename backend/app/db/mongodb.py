import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db_manager = MongoDBManager()


async def connect_mongo():
    """
    Conecta al pool asíncrono de MongoDB nativo en tu PC (localhost:27017)
    y asegura que las colecciones e índices existan en 'legadovivo_nosql'.
    """
    try:
        db_manager.client = AsyncIOMotorClient(
            settings.MONGO_URI,
            maxPoolSize=50,
            minPoolSize=10,
            serverSelectionTimeoutMS=4000
        )
        db_manager.db = db_manager.client[settings.MONGO_DB]
        
        # Test de conexión
        await db_manager.client.server_info()
        logger.info(f"Conectado a MongoDB nativo en tu PC: '{settings.MONGO_URI}'")

        # Inicializar colecciones e índices en legadovivo_nosql
        db = db_manager.db
        await db.capsules.create_index([("titular_id", 1)])
        await db.capsules.create_index([("created_at", -1)])
        await db.style_profiles.create_index([("titular_id", 1)], unique=True)
        await db.chat_sessions.create_index([("titular_id", 1)])

        logger.info(f"Base de datos MongoDB '{settings.MONGO_DB}' y sus colecciones/índices inicializados con éxito.")
    except Exception as e:
        logger.error(f"Error conectando a MongoDB en localhost:27017: {e}")
        logger.info("Verifica que el servicio de MongoDB en Windows esté iniciado.")
        db_manager.client = None
        db_manager.db = None


async def close_mongo():
    """Cierra la conexión con MongoDB al apagar el servicio."""
    if db_manager.client:
        db_manager.client.close()
        logger.info("Conexión con MongoDB cerrada.")


def get_mongo_db() -> AsyncIOMotorDatabase:
    """Retorna la instancia activa de la base de datos MongoDB."""
    return db_manager.db
