import os
import sys
import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_db")

# Credenciales por defecto de PostgreSQL local en Windows
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "12345")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB_NAME = "legadovivo_db"

# MongoDB local
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = "legadovivo_nosql"


def setup_postgresql():
    logger.info(f"Conectando a PostgreSQL en {PG_HOST}:{PG_PORT}...")
    try:
        # Conectar a la base 'postgres' por defecto para crear la base de datos
        conn = psycopg2.connect(
            user=PG_USER,
            password=PG_PASSWORD,
            host=PG_HOST,
            port=PG_PORT,
            dbname="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Verificar si la base de datos legadovivo_db ya existe
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{PG_DB_NAME}';")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f"CREATE DATABASE {PG_DB_NAME} OWNER {PG_USER} ENCODING 'UTF8';")
            logger.info(f"Base de datos PostgreSQL '{PG_DB_NAME}' CREADA con éxito.")
        else:
            logger.info(f"Base de datos PostgreSQL '{PG_DB_NAME}' ya existe. Lista para usar.")

        cursor.close()
        conn.close()

    except Exception as e:
        try:
            err_msg = str(e)
        except Exception:
            err_msg = repr(e)
        logger.error(f"Error conectando a PostgreSQL ({err_msg}).")
        logger.info("Si la contrasena es diferente, puedes configurarla con $env:POSTGRES_PASSWORD='tu_clave'")
        return False
    return True


def setup_mongodb():
    logger.info(f"Conectando a MongoDB en {MONGO_URI}...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        # Test de conexión
        client.server_info()

        db = client[MONGO_DB_NAME]

        # Crear colecciones e índices
        # 1. Colección capsules
        if "capsules" not in db.list_collection_names():
            db.create_collection("capsules")
            logger.info("Coleccion 'capsules' creada en MongoDB.")
        db.capsules.create_index([("titular_id", 1)])
        db.capsules.create_index([("created_at", -1)])

        # 2. Colección style_profiles
        if "style_profiles" not in db.list_collection_names():
            db.create_collection("style_profiles")
            logger.info("Coleccion 'style_profiles' creada en MongoDB.")
        db.style_profiles.create_index([("titular_id", 1)], unique=True)

        # 3. Colección chat_sessions
        if "chat_sessions" not in db.list_collection_names():
            db.create_collection("chat_sessions")
            logger.info("Coleccion 'chat_sessions' creada en MongoDB.")
        db.chat_sessions.create_index([("titular_id", 1)])

        # Insertar documentos semilla para forzar la materialización física de la base de datos en disco
        db.capsules.update_one(
            {"_id": "capsule-bienvenida-001"},
            {"$set": {
                "titular_id": "titular-demo-12345",
                "title": "Mi primer recuerdo en LegadoVivo",
                "content": "Mijito lindo, bienvenido a mi legado. He creado este espacio para dejarte mis recuerdos con todo mi cariño.",
                "category": "Familia y Tradición",
                "tags": ["bienvenida", "familia"],
                "emotional_tone": "afectuoso y cálido"
            }},
            upsert=True
        )

        db.style_profiles.update_one(
            {"titular_id": "titular-demo-12345"},
            {"$set": {
                "typical_phrases": ["mijito lindo", "oye", "te cuento", "con todo mi cariño"],
                "formality_level": "cálido, cercano y profundamente afectuoso",
                "warmth_score": 0.95,
                "sentiment_tendency": "nostálgico, protector y sereno"
            }},
            upsert=True
        )

        logger.info(f"Base de datos MongoDB '{MONGO_DB_NAME}' MATERIALIZADA y visible en MongoDB Compass.")
        client.close()
        return True

    except Exception as e:
        logger.error(f"Error conectando a MongoDB ({e}).")
        logger.info("Asegurate de que el servicio de MongoDB este iniciado en Windows.")
        return False


if __name__ == "__main__":
    logger.info("==================================================")
    logger.info("   INICIALIZANDO BASES DE DATOS NATIVAS EN PC     ")
    logger.info("==================================================")
    pg_ok = setup_postgresql()
    mongo_ok = setup_mongodb()

    if pg_ok and mongo_ok:
        logger.info("AMBAS BASES DE DATOS (PostgreSQL & MongoDB) ESTAN LISTAS.")
    else:
        logger.warning("Revise los mensajes anteriores para los detalles de conexion.")

