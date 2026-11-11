import sys
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("verify")

def test_postgresql():
    logger.info("1. Verificando conexión a PostgreSQL...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname="postgres",
            connect_timeout=3
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        ver = cursor.fetchone()
        cursor.close()
        conn.close()
        logger.info(f"   [OK] PostgreSQL conectado: {ver[0][:30]}...")
        return True
    except Exception as e:
        logger.warning(f"   [FALLO] PostgreSQL ({e})")
        return False

def test_mongodb():
    logger.info("2. Verificando conexión a MongoDB...")
    try:
        from pymongo import MongoClient
        client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
        dbs = client.list_database_names()
        logger.info(f"   [OK] MongoDB conectado. Bases encontradas: {dbs}")
        client.close()
        return True
    except Exception as e:
        logger.warning(f"   [FALLO] MongoDB ({e})")
        return False

def test_chromadb():
    logger.info("3. Verificando base vectorial ChromaDB embebida...")
    try:
        from app.db.chroma import get_chroma_collection
        col = get_chroma_collection("test_health")
        col.add(ids=["t1"], documents=["prueba"], embeddings=[[0.1]*384])
        count = col.count()
        col.delete(ids=["t1"])
        logger.info(f"   [OK] ChromaDB embebido operativo (persistencia en disco).")
        return True
    except Exception as e:
        logger.warning(f"   [FALLO] ChromaDB ({e})")
        return False

def test_ollama():
    logger.info(f"4. Verificando servicio Ollama en {settings.OLLAMA_HOST}...")
    try:
        import httpx
        res = httpx.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=2.0)
        if res.status_code == 200:
            models = [m.get("name") for m in res.json().get("models", [])]
            logger.info(f"   [OK] Ollama activo. Modelos instalados: {models}")
            return True
        else:
            logger.warning(f"   [AVISO] Ollama respondió con código {res.status_code}")
            return False
    except Exception as e:
        logger.warning(f"   [AVISO] Ollama no detectado en {settings.OLLAMA_HOST} ({e}). Recuerda iniciar 'ollama serve' o 'ollama run llama3:8b'.")
        return False

def test_nlp_embeddings():
    logger.info("5. Verificando modelo de embeddings (Sentence-Transformers)...")
    try:
        from app.services.ai_service import AIService
        vec = AIService.generate_embedding("Prueba de vectorización de recuerdo")
        logger.info(f"   [OK] Embeddings generados exitosamente ({len(vec)} dimensiones).")
        return True
    except Exception as e:
        logger.warning(f"   [FALLO] Sentence-Transformers ({e})")
        return False

if __name__ == "__main__":
    logger.info("========================================================")
    logger.info("   DIAGNÓSTICO INTEGRAL DE PLATAFORMA LEGADOVIVO        ")
    logger.info("========================================================")
    
    pg_ok = test_postgresql()
    mg_ok = test_mongodb()
    ch_ok = test_chromadb()
    nl_ok = test_nlp_embeddings()
    ol_ok = test_ollama()
    
    logger.info("========================================================")
    logger.info(f"RESUMEN: PostgreSQL={pg_ok} | MongoDB={mg_ok} | ChromaDB={ch_ok} | NLP={nl_ok} | Ollama={ol_ok}")
    logger.info("========================================================")

