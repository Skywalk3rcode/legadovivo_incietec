from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User, LegacyPlan, LegacyConnection, ConnectionStatus
from app.core.security import verify_supabase_token

# Esquema Bearer Token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de seguridad que valida el token de Supabase Auth,
    obtiene o sincroniza el usuario en la base de datos PostgreSQL y retorna su entidad.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales de acceso no válidas o expiradas. Inicie sesión mediante Supabase Auth.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = verify_supabase_token(token)
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    email: str = payload.get("email") or ""
    full_name: str = payload.get("full_name") or "Usuario"

    if not user_id:
        raise credentials_exception

    try:
        # 1. Buscar por ID único de Supabase
        user = db.query(User).filter(User.id == user_id).first()

        # 2. Si no se encuentra por ID, intentar buscar por email (caso de migración o alta previa)
        if user is None and email:
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Sincronizar ID de Supabase si estaba huérfano
                user.id = user_id

        # 3. Si el usuario aún no existe en PostgreSQL, sincronizarlo automáticamente
        if user is None:
            user = User(
                id=user_id,
                email=email if email else f"user_{user_id[:8]}@supabase.local",
                full_name=full_name,
                hashed_password=None,
                is_active=True
            )
            db.add(user)
            db.flush()

            # Inicializar su Plan de Legado como Titular
            plan = LegacyPlan(titular_id=user.id)
            db.add(plan)
            db.commit()
            db.refresh(user)

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta de usuario se encuentra desactivada."
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar identidad con Supabase: {str(e)}"
        )


def get_current_titular_id(
    token: Optional[str] = Depends(oauth2_scheme),
) -> str:
    """Obtiene el ID autenticado del titular; nunca comparte datos demo entre sesiones."""
    if token:
        payload = verify_supabase_token(token)
        if payload and "sub" in payload:
            return payload["sub"]
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="La sesión no es válida. Inicia sesión de nuevo con Supabase.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def ensure_titular_access(target_titular_id: str, current_user_id: str, db: Session) -> str:
    """Allow a user to access their own memories or an active linked titular's memories."""
    if target_titular_id == current_user_id:
        return target_titular_id

    connection = db.query(LegacyConnection.id).filter(
        LegacyConnection.owner_id == target_titular_id,
        LegacyConnection.beneficiary_id == current_user_id,
        LegacyConnection.status == ConnectionStatus.ACTIVE,
    ).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes una vinculación activa con este legado.",
        )
    return target_titular_id
