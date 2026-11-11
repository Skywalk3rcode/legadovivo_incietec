import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.postgres import init_sql_db, check_sql_health
from app.db.mongodb import connect_mongo, close_mongo, check_mongo_health
from app.db.chroma import get_chroma_collection, check_chroma_health
from app.services.ai_service import AIService
from app.api import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("legadovivo")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida del servicio (Startup y Shutdown)."""
    logger.info("Iniciando LegadoVivo Backend & Motor Neuronal...")

    # Inicializar conexiones
    init_sql_db()
    await connect_mongo()
    try:
        get_chroma_collection("legado_capsules")
        logger.info("Colección ChromaDB verificada exitosamente.")
    except Exception as e:
        logger.warning(f"ChromaDB en espera o inicialización diferida: {e}")

    yield

    logger.info("Apagando LegadoVivo Backend...")
    await close_mongo()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend y Motor RAG con mimetismo de personalidad y Cero Alucinación para LegadoVivo.",
    lifespan=lifespan
)

# Configuración de CORS para el Frontend (React + Vite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de rutas principales
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Salud"])
@app.get("/api/health", tags=["Salud"])
async def health_check():
    """
    Diagnóstico integral de salud del sistema LegadoVivo:
    Distingue con precisión entre:
    1. Contenedor/proceso iniciado (FastAPI responde).
    2. Base relacional lista y tablas inicializadas (PostgreSQL / SQLite fallback).
    3. Persistencia de recuerdos lista (MongoDB).
    4. Base vectorial lista (ChromaDB HTTP / local).
    5. Motor de inferencia listo y modelo descargado (Ollama + llama3:8b).
    """
    sql_diag = check_sql_health()
    mongo_diag = await check_mongo_health()
    chroma_diag = check_chroma_health()
    ollama_diag = await AIService.check_ollama_health()

    # Evaluación de estado global
    # Unhealthy: si la base relacional principal no responde
    if sql_diag.get("status") == "unhealthy":
        global_status = "unhealthy"
    # Degraded: si se usa SQLite fallback, o falta MongoDB, o el modelo Ollama no está descargado
    elif (
        sql_diag.get("fallback_sqlite")
        or mongo_diag.get("status") != "healthy"
        or chroma_diag.get("status") != "healthy"
        or ollama_diag.get("status") != "healthy"
    ):
        global_status = "degraded"
    else:
        global_status = "healthy"

    notes = []
    if sql_diag.get("fallback_sqlite"):
        notes.append("PostgreSQL inactivo; operando en SQLite local de desarrollo.")
    if mongo_diag.get("status") != "healthy":
        notes.append("MongoDB no responde; almacenamiento NoSQL en espera.")
    if chroma_diag.get("mode") == "persistent":
        notes.append("ChromaDB en modo persistente local (no HTTP).")
    if not ollama_diag.get("service_ready"):
        notes.append("Servicio Ollama no detectado en el host configurado.")
    elif not ollama_diag.get("model_downloaded"):
        notes.append(f"Ollama activo pero falta descargar el modelo '{settings.OLLAMA_MODEL}'.")

    return {
        "status": global_status,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "database": sql_diag,
            "mongodb": mongo_diag,
            "chromadb": chroma_diag,
            "ollama": ollama_diag
        },
        "diagnostic_notes": notes
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.API_PORT, reload=settings.DEBUG)

