import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def ensure_postgres_database_exists():
    """
    Verifica e intenta crear automáticamente la base de datos 'legadovivo_db'
    en el servidor PostgreSQL local de tu PC si aún no existe.
    """
    try:
        conn = psycopg2.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname="postgres",
            connect_timeout=3
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{settings.POSTGRES_DB}';")
        exists = cursor.fetchone()
        if not exists:
            cursor.execute(f"CREATE DATABASE {settings.POSTGRES_DB} ENCODING 'UTF8';")
            logger.info(f"Base de datos '{settings.POSTGRES_DB}' creada en PostgreSQL local.")
        else:
            logger.info(f"Base de datos '{settings.POSTGRES_DB}' ya existe en PostgreSQL local.")
        cursor.close()
        conn.close()
    except Exception as e:
        try:
            err_msg = str(e)
        except Exception:
            err_msg = repr(e)
        logger.warning(f"Aviso al verificar base de datos en PostgreSQL: {err_msg}")


def get_engine():
    """Crea el motor SQLAlchemy para PostgreSQL nativo en tu PC."""
    ensure_postgres_database_exists()
    return create_engine(
        settings.POSTGRES_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
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
    """Crea todas las tablas (users, legacy_connections, legacy_plans, audit_logs) en PostgreSQL."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Tablas de PostgreSQL creadas/verificadas con éxito en '{settings.POSTGRES_DB}'.")
    except Exception as e:
        logger.error(f"Error inicializando tablas en PostgreSQL: {e}")
