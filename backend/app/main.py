import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.postgres import init_sql_db
from app.db.mongodb import connect_mongo, close_mongo
from app.db.chroma import get_chroma_collection
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
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.API_PORT, reload=settings.DEBUG)

