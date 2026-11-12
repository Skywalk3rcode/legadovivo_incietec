import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.postgres import Base


class ConnectionStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    PENDING_POST_MORTEM = "PENDING_POST_MORTEM"


class ActivationRule(str, enum.Enum):
    MANUAL_CONFIRMATION = "manual_confirmation"    # Certificado o confirmación delegada
    INACTIVITY_TIMER = "inactivity_timer"          # Ausencia de check-in tras N días
    TRUSTEE_QUORUM = "trustee_quorum"              # Aprobación de 2 o más albaceas


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Conexiones donde este usuario es el Titular (dueño del legado)
    owned_connections = relationship(
        "LegacyConnection",
        foreign_keys="LegacyConnection.owner_id",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    # Conexiones donde este usuario es el Beneficiario (ser querido con acceso)
    beneficiary_connections = relationship(
        "LegacyConnection",
        foreign_keys="LegacyConnection.beneficiary_id",
        back_populates="beneficiary",
        cascade="all, delete-orphan"
    )

    # Plan de activación post-mortem, auditoría e intentos de seguridad
    legacy_plan = relationship("LegacyPlan", back_populates="titular", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")
    code_attempts = relationship("CodeAttempt", back_populates="user")


class LegacyConnection(Base):
    """
    Tabla Intermedia que vincula quién tiene acceso a los recuerdos de quién.
    Permite el concepto de Doble Rol: un mismo usuario puede ser Titular en unas
    conexiones y Beneficiario en otras.
    """
    __tablename__ = "legacy_connections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    beneficiary_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    status = Column(SQLEnum(ConnectionStatus, name="connectionstatus"), default=ConnectionStatus.PENDING, nullable=False, index=True)
    connection_code = Column(String(32), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    linked_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    # Relaciones
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_connections")
    beneficiary = relationship("User", foreign_keys=[beneficiary_id], back_populates="beneficiary_connections")


class LegacyPlan(Base):
    __tablename__ = "legacy_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    titular_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    is_activated = Column(Boolean, default=False, nullable=False)  # Si el titular falleció / plan activo
    activated_at = Column(DateTime, nullable=True)
    activation_rule = Column(SQLEnum(ActivationRule), default=ActivationRule.MANUAL_CONFIRMATION)
    inactivity_days_threshold = Column(String(50), default="90")
    emergency_contact_email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    titular = relationship("User", back_populates="legacy_plan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")


class CodeAttempt(Base):
    """
    Registro de intentos de validación/canje de códigos para limitar intentos
    (Rate Limiting) y mitigar ataques de fuerza bruta.
    """
    __tablename__ = "code_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    attempted_code = Column(String(32), nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="code_attempts")
