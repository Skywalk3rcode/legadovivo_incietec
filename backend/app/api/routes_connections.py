from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User, LegacyConnection, ConnectionStatus
from app.core.security import generate_connection_code
from app.api.deps import get_current_user

router = APIRouter()


class GenerateCodeResponse(BaseModel):
    connection_code: str
    owner_id: str
    owner_name: str
    status: ConnectionStatus
    created_at: datetime
    message: str


class LinkCodeRequest(BaseModel):
    connection_code: str = Field(..., example="LEG-A7K92M")


class TitularConnectionSummary(BaseModel):
    connection_id: str
    owner_id: str
    owner_name: str
    owner_email: str
    status: ConnectionStatus
    linked_at: Optional[datetime]
    created_at: datetime


class BeneficiarySummary(BaseModel):
    connection_id: str
    beneficiary_id: Optional[str]
    beneficiary_name: Optional[str]
    beneficiary_email: Optional[str]
    connection_code: str
    status: ConnectionStatus
    linked_at: Optional[datetime]
    created_at: datetime


@router.post("/generate-code", response_model=GenerateCodeResponse, status_code=status.HTTP_201_CREATED)
def generate_invite_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL TITULAR: Genera un código alfanumérico único para que un ser querido
    pueda vincularse y acceder a sus memorias y al Chat RAG.
    """
    # 1. Generar código único que no exista previamente
    for _ in range(5):
        code = generate_connection_code()
        exists = db.query(LegacyConnection).filter(LegacyConnection.connection_code == code).first()
        if not exists:
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generando código único de vinculación. Intente de nuevo."
        )

    # 2. Crear la invitación pendiente de vinculación
    connection = LegacyConnection(
        owner_id=current_user.id,
        beneficiary_id=None,
        status=ConnectionStatus.ACTIVE,
        connection_code=code,
        created_at=datetime.utcnow()
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    return GenerateCodeResponse(
        connection_code=connection.connection_code,
        owner_id=current_user.id,
        owner_name=current_user.full_name,
        status=connection.status,
        created_at=connection.created_at,
        message="Comparte este código con tu ser querido para vincularse a tu legado."
    )


@router.post("/link", response_model=TitularConnectionSummary)
def link_beneficiary_to_titular(
    payload: LinkCodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL BENEFICIARIO: Envía un código de vinculación provisto por un Titular.
    El sistema busca a quién pertenece el código y asocia al usuario actual
    como beneficiario en la tabla LegacyConnection.
    """
    code_cleaned = payload.connection_code.strip().upper()

    # 1. Buscar la conexión por código
    connection = db.query(LegacyConnection).filter(
        LegacyConnection.connection_code == code_cleaned
    ).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de vinculación inválido o inexistente."
        )

    # 2. Evitar que un usuario se vincule consigo mismo
    if connection.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes vincularte a tu propio legado como beneficiario."
        )

    # 3. Si ya estaba vinculado a otra persona
    if connection.beneficiary_id and connection.beneficiary_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este código de vinculación ya ha sido canjeado por otro beneficiario."
        )

    # 4. Vincular al beneficiario
    connection.beneficiary_id = current_user.id
    connection.linked_at = datetime.utcnow()
    connection.status = ConnectionStatus.ACTIVE
    db.commit()
    db.refresh(connection)

    # Obtener datos del dueño (Titular)
    owner = db.query(User).filter(User.id == connection.owner_id).first()

    return TitularConnectionSummary(
        connection_id=connection.id,
        owner_id=connection.owner_id,
        owner_name=owner.full_name if owner else "Titular",
        owner_email=owner.email if owner else "",
        status=connection.status,
        linked_at=connection.linked_at,
        created_at=connection.created_at
    )


@router.get("/my-connections", response_model=List[TitularConnectionSummary])
def get_my_connections_as_beneficiary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL BENEFICIARIO (Pestaña 'Seres Queridos'):
    Devuelve la lista de Titulares a cuyos legados tiene acceso el usuario actual.
    """
    connections = db.query(LegacyConnection).filter(
        LegacyConnection.beneficiary_id == current_user.id,
        LegacyConnection.status != ConnectionStatus.REVOKED
    ).all()

    results: List[TitularConnectionSummary] = []
    for conn in connections:
        owner = db.query(User).filter(User.id == conn.owner_id).first()
        if owner:
            results.append(TitularConnectionSummary(
                connection_id=conn.id,
                owner_id=conn.owner_id,
                owner_name=owner.full_name,
                owner_email=owner.email,
                status=conn.status,
                linked_at=conn.linked_at,
                created_at=conn.created_at
            ))

    return results


@router.get("/my-beneficiaries", response_model=List[BeneficiarySummary])
def get_my_invited_beneficiaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ROL TITULAR (Pestaña 'Mi Legado'):
    Muestra los códigos generados y la lista de seres queridos vinculados a su propio legado.
    """
    connections = db.query(LegacyConnection).filter(
        LegacyConnection.owner_id == current_user.id
    ).order_by(LegacyConnection.created_at.desc()).all()

    results: List[BeneficiarySummary] = []
    for conn in connections:
        bene = None
        if conn.beneficiary_id:
            bene = db.query(User).filter(User.id == conn.beneficiary_id).first()

        results.append(BeneficiarySummary(
            connection_id=conn.id,
            beneficiary_id=conn.beneficiary_id,
            beneficiary_name=bene.full_name if bene else None,
            beneficiary_email=bene.email if bene else None,
            connection_code=conn.connection_code,
            status=conn.status,
            linked_at=conn.linked_at,
            created_at=conn.created_at
        ))

    return results

