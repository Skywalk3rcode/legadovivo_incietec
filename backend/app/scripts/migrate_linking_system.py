"""
Migración idempotente para el Sistema de Vinculación por Códigos en LegadoVivo.
Agrega estados de vigencia, columnas de expiración y tabla de protección contra fuerza bruta.
"""
import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import text, inspect
from app.db.postgres import engine, Base
from app.models.sql_models import CodeAttempt, LegacyConnection

logger = logging.getLogger("migration_linking")


def run_linking_migration():
    """Ejecuta la migración de esquema en la base de datos PostgreSQL de forma segura e idempotente."""
    logger.info("Iniciando migración del sistema de vinculación por códigos...")

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        dialect_name = engine.dialect.name

        if dialect_name == "postgresql":
            # 1. Actualizar el tipo Enum de PostgreSQL
            for val in ["PENDING", "EXPIRED", "CANCELLED"]:
                try:
                    res = conn.execute(text(
                        "SELECT 1 FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                        "WHERE typname = 'connectionstatus' AND enumlabel = :val"
                    ), {"val": val}).fetchone()
                    if not res:
                        conn.execute(text(f"ALTER TYPE connectionstatus ADD VALUE '{val}'"))
                        logger.info(f"Valor Enum '{val}' añadido a connectionstatus en PostgreSQL.")
                except Exception as e:
                    logger.warning(f"Aviso al verificar/añadir valor Enum '{val}': {e}")

            # 2. Agregar columnas expires_at y revoked_at a legacy_connections
            try:
                conn.execute(text("""
                    ALTER TABLE legacy_connections 
                    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
                """))
                conn.execute(text("""
                    UPDATE legacy_connections 
                    SET expires_at = created_at + INTERVAL '48 hours' 
                    WHERE expires_at IS NULL;
                """))
                conn.execute(text("""
                    ALTER TABLE legacy_connections 
                    ALTER COLUMN expires_at SET NOT NULL;
                """))
                conn.execute(text("""
                    ALTER TABLE legacy_connections 
                    ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITHOUT TIME ZONE;
                """))
                logger.info("Columnas 'expires_at' y 'revoked_at' verificadas en legacy_connections.")
            except Exception as e:
                logger.warning(f"Aviso migrando columnas de legacy_connections: {e}")

            # 3. Crear índices para optimizar búsquedas de códigos y estados
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_legacy_connections_expires_at 
                    ON legacy_connections(expires_at);
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_legacy_connections_status 
                    ON legacy_connections(status);
                """))
            except Exception as e:
                logger.warning(f"Aviso creando índices en legacy_connections: {e}")

        # 4. Crear tabla code_attempts e índices si no existen (vía Base metadata para cualquier motor)
        try:
            Base.metadata.create_all(bind=engine, tables=[CodeAttempt.__table__, LegacyConnection.__table__])
            logger.info("Tabla 'code_attempts' y restricciones verificadas correctamente.")
        except Exception as e:
            logger.warning(f"Aviso asegurando tablas vía metadata: {e}")

    logger.info("Migración del sistema de vinculación completada exitosamente.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_linking_migration()
