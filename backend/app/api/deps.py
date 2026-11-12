from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User, LegacyPlan
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
    db: Session = Depends(get_db)
) -> str:
    """
    Obtiene el ID del titular en contexto:
    - Si hay un token válido de Supabase, retorna el sub (UUID del usuario).
    - Si no hay token o es entorno demo/local, retorna el ID demo.
    """
    if token:
        payload = verify_supabase_token(token)
        if payload and "sub" in payload:
            return payload["sub"]
    return "titular-demo-12345"
