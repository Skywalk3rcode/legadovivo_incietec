import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine():
    """
    Crea el motor SQL con resiliencia:
    1. Intenta conectar a PostgreSQL.
    2. Si PostgreSQL no está corriendo en local, conmuta automáticamente a SQLite
       para que la autenticación, roles y códigos funcionen inmediatamente sin bloquear al desarrollador.
    """
    try:
        # Timeout corto para no demorar el inicio
        eng = create_engine(
            settings.POSTGRES_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3}
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Conexión exitosa a PostgreSQL.")
        return eng
    except Exception as e:
        logger.warning(
            f"PostgreSQL en {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT} no está activo ({e}). "
            f"Activando SQLite local en '{settings.SQLITE_DB_PATH}' para desarrollo continuo."
        )
        return create_engine(
            f"sqlite:///{settings.SQLITE_DB_PATH}",
            connect_args={"check_same_thread": False}
        )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para inyección de sesiones SQL en FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_sql_db():
    """Inicializa las tablas SQL (en PostgreSQL o SQLite local) asegurando que los modelos estén cargados."""
    try:
        # Asegurarse de que todos los modelos SQL estén registrados en Base.metadata
        import app.models.sql_models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos verificadas/creadas con éxito.")
    except Exception as e:
        logger.error(f"Error inicializando tablas SQL: {e}")


def check_sql_health() -> dict:
    """Verifica el estado de la base de datos SQL y las tablas creadas."""
    dialect_name = engine.dialect.name
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        required_tables = {"users", "legacy_connections", "legacy_plans", "audit_logs"}
        missing_tables = required_tables - set(tables)

        return {
            "status": "healthy" if not missing_tables else "degraded",
            "dialect": dialect_name,
            "connected": True,
            "fallback_sqlite": dialect_name == "sqlite",
            "tables_found": tables,
            "missing_tables": list(missing_tables)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "dialect": dialect_name,
            "connected": False,
            "error": str(e)
        }

