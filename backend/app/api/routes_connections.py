from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User, LegacyConnection, ConnectionStatus, CodeAttempt, AuditLog
from app.core.security import generate_connection_code
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter()


# ==========================================
# Esquemas Pydantic para Request / Response
# ==========================================

class GenerateCodeRequest(BaseModel):
    expiration_hours: Optional[int] = Field(None, ge=1, le=720, description="Horas de validez (1 a 720)")
    auto_cancel_previous: bool = Field(False, description="Cancelar códigos pendientes anteriores al generar uno nuevo")


class GenerateCodeResponse(BaseModel):
    connection_id: str
    connection_code: str
    owner_id: str
    owner_name: str
    status: str
    created_at: datetime
    expires_at: datetime
    message: str


class ValidateCodeRequest(BaseModel):
    connection_code: str = Field(..., min_length=4, max_length=32, example="LEG-A7K92M")


class CodePreviewResponse(BaseModel):
    connection_id: str
    connection_code: str
    owner_id: str
    owner_name: str
    created_at: datetime
    expires_at: datetime
    message: str


class LinkCodeRequest(BaseModel):
    connection_code: str = Field(..., min_length=4, max_length=32, example="LEG-A7K92M")


class TitularConnectionSummary(BaseModel):
    connection_id: str
    owner_id: str
    owner_name: str
    owner_email: str
    status: str
    linked_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class BeneficiarySummary(BaseModel):
    connection_id: str
    beneficiary_id: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_email: Optional[str] = None
    connection_code: str
    status: str
    linked_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    time_remaining_seconds: Optional[int] = None
    is_expired: bool = False


class ActionResponse(BaseModel):
    success: bool
    message: str
    connection_id: Optional[str] = None


# ==========================================
# Helpers de Seguridad y Rate Limiting
# ==========================================

def get_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente considerando posibles proxies."""
    if not request:
        return "127.0.0.1"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def check_rate_limit(db: Session, ip_address: Optional[str], user_id: Optional[str]):
    """
    Verifica que el usuario o la IP no hayan superado el umbral de intentos fallidos
    en la ventana de tiempo configurada (mitigación de ataques de fuerza bruta).
    Si el usuario está autenticado, el límite se evalúa por usuario para no afectar a otros clientes en la misma red.
    """
    lockout_delta = datetime.utcnow() - timedelta(minutes=settings.CODE_ATTEMPT_LOCKOUT_MINUTES)
    
    if user_id:
        failed_count = db.query(CodeAttempt).filter(
            CodeAttempt.timestamp >= lockout_delta,
            CodeAttempt.success.is_(False),
            CodeAttempt.user_id == user_id
        ).count()
    elif ip_address:
        failed_count = db.query(CodeAttempt).filter(
            CodeAttempt.timestamp >= lockout_delta,
            CodeAttempt.success.is_(False),
            CodeAttempt.ip_address == ip_address
        ).count()
    else:
        failed_count = 0

    if failed_count >= settings.MAX_CODE_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Has superado el límite de intentos fallidos ({settings.MAX_CODE_ATTEMPTS}). "
                   f"Por seguridad, el acceso a validación de códigos está bloqueado temporalmente por {settings.CODE_ATTEMPT_LOCKOUT_MINUTES} minutos."
        )


def record_code_attempt(db: Session, code: str, success: bool, ip_address: Optional[str], user_id: Optional[str]):
    """Registra de manera atómica el intento de verificación o canje de código."""
    try:
        attempt = CodeAttempt(
            user_id=user_id,
            ip_address=ip_address,
            attempted_code=code[:32],
            success=success,
            timestamp=datetime.utcnow()
        )
        db.add(attempt)
        db.commit()
    except Exception:
        db.rollback()


# ==========================================
# Endpoints de la API
# ==========================================

@router.post("/generate-code", response_model=GenerateCodeResponse, status_code=status.HTTP_201_CREATED)
def generate_invite_code(
    payload: Optional[GenerateCodeRequest] = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL TITULAR: Genera un código alfanumérico único de alta entropía con fecha
    de expiración configurable para vincular a un familiar.
    Permite además invalidar códigos pendientes previos si se regenera.
    """
    now = datetime.utcnow()
    exp_hours = payload.expiration_hours if (payload and payload.expiration_hours) else settings.INVITE_CODE_EXPIRATION_HOURS

    # Si se solicitó cancelar códigos previos o regenerar
    if payload and payload.auto_cancel_previous:
        pending_invites = db.query(LegacyConnection).filter(
            LegacyConnection.owner_id == current_user.id,
            LegacyConnection.status == ConnectionStatus.PENDING
        ).all()
        for p in pending_invites:
            p.status = ConnectionStatus.CANCELLED
            p.revoked_at = now

    # Generar código criptográficamente seguro y verificar que no exista duplicado
    code = ""
    for _ in range(10):
        candidate = generate_connection_code(length=8)
        exists = db.query(LegacyConnection).filter(LegacyConnection.connection_code == candidate).first()
        if not exists:
            code = candidate
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando código único de vinculación. Intente de nuevo."
        )

    expires_at = now + timedelta(hours=exp_hours)

    connection = LegacyConnection(
        owner_id=current_user.id,
        beneficiary_id=None,
        status=ConnectionStatus.PENDING,
        connection_code=code,
        created_at=now,
        expires_at=expires_at
    )
    db.add(connection)

    # Registrar en auditoría
    client_ip = get_client_ip(request) if request else None
    audit = AuditLog(
        user_id=current_user.id,
        action="CODIGO_GENERADO",
        ip_address=client_ip,
        details=f"Código {code} generado por {current_user.full_name} con expiración en {exp_hours}h"
    )
    db.add(audit)
    db.commit()
    db.refresh(connection)

    return GenerateCodeResponse(
        connection_id=connection.id,
        connection_code=connection.connection_code,
        owner_id=current_user.id,
        owner_name=current_user.full_name,
        status=connection.status.value,
        created_at=connection.created_at,
        expires_at=connection.expires_at,
        message=f"Código generado exitosamente. Válido durante {exp_hours} horas."
    )


@router.post("/cancel-code/{connection_id}", response_model=ActionResponse)
def cancel_invite_code(
    connection_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL TITULAR: Cancela o invalida un código de invitación pendiente antes de que sea utilizado.
    """
    connection = db.query(LegacyConnection).filter(
        LegacyConnection.id == connection_id
    ).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de invitación no encontrado."
        )

    if connection.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar este código."
        )

    if connection.status == ConnectionStatus.ACTIVE and connection.beneficiary_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código ya ha sido canjeado. Para revocar el acceso debes desvincular al usuario."
        )

    connection.status = ConnectionStatus.CANCELLED
    connection.revoked_at = datetime.utcnow()

    audit = AuditLog(
        user_id=current_user.id,
        action="CODIGO_CANCELADO",
        ip_address=get_client_ip(request),
        details=f"Titular canceló el código {connection.connection_code}"
    )
    db.add(audit)
    db.commit()

    return ActionResponse(
        success=True,
        message="El código de invitación ha sido cancelado exitosamente.",
        connection_id=connection.id
    )


@router.post("/preview-code", response_model=CodePreviewResponse)
def preview_invite_code(
    payload: ValidateCodeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL BENEFICIARIO: Valida en el servidor un código ingresado y retorna la
    identidad pública del Titular antes de solicitar confirmación explícita.
    Aplica protección contra ataques de fuerza bruta (Rate Limiting).
    """
    ip = get_client_ip(request)
    check_rate_limit(db, ip, current_user.id)
    code_cleaned = payload.connection_code.strip().upper()
    now = datetime.utcnow()

    connection = db.query(LegacyConnection).filter(
        LegacyConnection.connection_code == code_cleaned
    ).first()

    if not connection:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de vinculación inválido o inexistente."
        )

    # 1. No vincularse consigo mismo
    if connection.owner_id == current_user.id:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes vincularte a tu propio legado."
        )

    # 2. Verificar estado de cancelación / revocación
    if connection.status == ConnectionStatus.CANCELLED:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de invitación ha sido cancelado por su titular."
        )

    if connection.status == ConnectionStatus.REVOKED:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de vinculación ha sido revocado."
        )

    # 3. Verificar expiración temporal
    if connection.expires_at and connection.expires_at < now:
        connection.status = ConnectionStatus.EXPIRED
        db.commit()
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de vinculación ha expirado. Solicita un nuevo código al titular."
        )

    # 4. Verificar si ya fue canjeado
    if connection.beneficiary_id is not None or connection.status == ConnectionStatus.ACTIVE:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de vinculación ya ha sido utilizado por otro usuario."
        )

    # 5. Evitar vinculaciones duplicadas con el mismo titular
    already_linked = db.query(LegacyConnection).filter(
        LegacyConnection.owner_id == connection.owner_id,
        LegacyConnection.beneficiary_id == current_user.id,
        LegacyConnection.status == ConnectionStatus.ACTIVE
    ).first()

    if already_linked:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya te encuentras vinculado activamente al legado de este titular."
        )

    # Intento exitoso
    record_code_attempt(db, code_cleaned, True, ip, current_user.id)

    owner = db.query(User).filter(User.id == connection.owner_id).first()
    owner_name = owner.full_name if owner else "Titular del Legado"

    return CodePreviewResponse(
        connection_id=connection.id,
        connection_code=connection.connection_code,
        owner_id=connection.owner_id,
        owner_name=owner_name,
        created_at=connection.created_at,
        expires_at=connection.expires_at,
        message="Titular verificado exitosamente. Confirma para establecer la vinculación."
    )


@router.post("/confirm-link", response_model=TitularConnectionSummary)
@router.post("/link", response_model=TitularConnectionSummary)
def confirm_link_beneficiary(
    payload: LinkCodeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL BENEFICIARIO: Confirma explícitamente y registra de manera ATÓMICA la vinculación.
    Utiliza bloqueo por fila (with_for_update) para evitar condiciones de carrera (doble canje concurrente).
    """
    ip = get_client_ip(request)
    check_rate_limit(db, ip, current_user.id)
    code_cleaned = payload.connection_code.strip().upper()
    now = datetime.utcnow()

    # Transacción atómica con bloqueo a nivel de fila
    connection = db.query(LegacyConnection).filter(
        LegacyConnection.connection_code == code_cleaned
    ).with_for_update().first()

    if not connection:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de vinculación inválido o inexistente."
        )

    # 1. No vincularse a sí mismo
    if connection.owner_id == current_user.id:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes vincularte a tu propio legado como beneficiario."
        )

    # 2. Validar estados no vinculables
    if connection.status == ConnectionStatus.CANCELLED:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de invitación ha sido cancelado por su titular."
        )

    if connection.status == ConnectionStatus.REVOKED:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de vinculación ha sido revocado."
        )

    # 3. Validar expiración
    if connection.expires_at and connection.expires_at < now:
        connection.status = ConnectionStatus.EXPIRED
        db.commit()
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de vinculación ha expirado. Solicita un nuevo código al titular."
        )

    # 4. Validar que no haya sido ya canjeado
    if connection.beneficiary_id is not None or connection.status == ConnectionStatus.ACTIVE:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de vinculación ya ha sido utilizado por otro usuario."
        )

    # 5. Evitar vinculaciones duplicadas
    already_linked = db.query(LegacyConnection).filter(
        LegacyConnection.owner_id == connection.owner_id,
        LegacyConnection.beneficiary_id == current_user.id,
        LegacyConnection.status == ConnectionStatus.ACTIVE
    ).first()

    if already_linked:
        record_code_attempt(db, code_cleaned, False, ip, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya te encuentras vinculado activamente al legado de este titular."
        )

    # Operación de vinculación atómica
    connection.beneficiary_id = current_user.id
    connection.linked_at = now
    connection.status = ConnectionStatus.ACTIVE

    audit = AuditLog(
        user_id=current_user.id,
        action="VINCULACION_CONFIRMADA",
        ip_address=ip,
        details=f"Beneficiario {current_user.full_name} ({current_user.id}) vinculado con éxito al titular {connection.owner_id}"
    )
    db.add(audit)
    db.commit()
    db.refresh(connection)

    record_code_attempt(db, code_cleaned, True, ip, current_user.id)

    owner = db.query(User).filter(User.id == connection.owner_id).first()

    return TitularConnectionSummary(
        connection_id=connection.id,
        owner_id=connection.owner_id,
        owner_name=owner.full_name if owner else "Titular",
        owner_email=owner.email if owner else "",
        status=connection.status.value,
        linked_at=connection.linked_at,
        created_at=connection.created_at,
        expires_at=connection.expires_at
    )


@router.post("/unlink/{connection_id}", response_model=ActionResponse)
@router.delete("/connections/{connection_id}", response_model=ActionResponse)
def unlink_connection(
    connection_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    GESTIÓN DE VINCULACIONES: Permite desvincular o revocar una relación.
    Tanto el Titular como el Beneficiario pueden revocar el acceso de forma segura.
    """
    connection = db.query(LegacyConnection).filter(
        LegacyConnection.id == connection_id
    ).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conexión de vinculación no encontrada."
        )

    # Validar que el usuario sea parte de la vinculación (dueño o beneficiario)
    if connection.owner_id != current_user.id and connection.beneficiary_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes autorización para desvincular esta relación."
        )

    connection.status = ConnectionStatus.REVOKED
    connection.revoked_at = datetime.utcnow()

    role = "Titular" if connection.owner_id == current_user.id else "Beneficiario"
    audit = AuditLog(
        user_id=current_user.id,
        action="DESVINCULACION_REVOCADA",
        ip_address=get_client_ip(request),
        details=f"{role} revocó la vinculación {connection_id} (Titular: {connection.owner_id}, Beneficiario: {connection.beneficiary_id})"
    )
    db.add(audit)
    db.commit()

    return ActionResponse(
        success=True,
        message="La vinculación ha sido desvinculada exitosamente.",
        connection_id=connection.id
    )


@router.get("/my-connections", response_model=List[TitularConnectionSummary])
def get_my_connections_as_beneficiary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL BENEFICIARIO (Pestaña 'Seres Queridos'):
    Devuelve la lista de Titulares a cuyos legados tiene acceso activo el usuario actual.
    """
    connections = db.query(LegacyConnection).filter(
        LegacyConnection.beneficiary_id == current_user.id,
        LegacyConnection.status == ConnectionStatus.ACTIVE
    ).order_by(LegacyConnection.linked_at.desc()).all()

    results: List[TitularConnectionSummary] = []
    for conn in connections:
        owner = db.query(User).filter(User.id == conn.owner_id).first()
        if owner:
            results.append(TitularConnectionSummary(
                connection_id=conn.id,
                owner_id=conn.owner_id,
                owner_name=owner.full_name,
                owner_email=owner.email,
                status=conn.status.value,
                linked_at=conn.linked_at,
                created_at=conn.created_at,
                expires_at=conn.expires_at
            ))

    return results


@router.get("/my-beneficiaries", response_model=List[BeneficiarySummary])
def get_my_invited_beneficiaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL TITULAR (Pestaña 'Mi Legado'):
    Muestra los códigos generados, su vigencia, estado (Pendiente, Activo, Expirado, Cancelado, Revocado)
    y los seres queridos vinculados.
    Actualiza de forma reactiva códigos pendientes que hayan rebasado su fecha de expiración.
    """
    connections = db.query(LegacyConnection).filter(
        LegacyConnection.owner_id == current_user.id
    ).order_by(LegacyConnection.created_at.desc()).all()

    now = datetime.utcnow()
    has_status_updates = False

    results: List[BeneficiarySummary] = []
    for conn in connections:
        bene = None
        if conn.beneficiary_id:
            bene = db.query(User).filter(User.id == conn.beneficiary_id).first()

        # Chequeo dinámico de expiración para códigos pendientes
        is_expired = False
        remaining_seconds = None
        if conn.expires_at:
            delta = (conn.expires_at - now).total_seconds()
            if delta <= 0:
                is_expired = True
                remaining_seconds = 0
                if conn.status == ConnectionStatus.PENDING:
                    conn.status = ConnectionStatus.EXPIRED
                    has_status_updates = True
            else:
                remaining_seconds = int(delta)

        results.append(BeneficiarySummary(
            connection_id=conn.id,
            beneficiary_id=conn.beneficiary_id,
            beneficiary_name=bene.full_name if bene else None,
            beneficiary_email=bene.email if bene else None,
            connection_code=conn.connection_code,
            status=conn.status.value,
            linked_at=conn.linked_at,
            created_at=conn.created_at,
            expires_at=conn.expires_at,
            time_remaining_seconds=remaining_seconds,
            is_expired=is_expired
        ))

    if has_status_updates:
        try:
            db.commit()
        except Exception:
            db.rollback()

    return results
