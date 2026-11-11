import logging
from sqlalchemy import create_engine
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
            pass
        logger.info("Conexión exitosa a PostgreSQL.")
        return eng
    except Exception as e:
        logger.warning(
            f"PostgreSQL en {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT} no está activo ({e}). "
            "Activando SQLite local ('sqlite:///./legadovivo_dev.db') para desarrollo continuo."
        )
        return create_engine(
            "sqlite:///./legadovivo_dev.db",
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
    """Inicializa las tablas SQL (en PostgreSQL o SQLite local)."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas de base de datos verificadas/creadas con éxito.")
    except Exception as e:
        logger.error(f"Error inicializando tablas SQL: {e}")
