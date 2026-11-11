from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User
from app.api.deps import get_current_user
from app.core.config import settings

router = APIRouter()


class UserPublicResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthStatusResponse(BaseModel):
    provider: str = "Supabase Auth"
    configured: bool
    supabase_url: Optional[str] = None


@router.get("/me", response_model=UserPublicResponse)
def get_authenticated_profile(
    current_user: User = Depends(get_current_user)
):
    """Devuelve los datos del perfil del usuario autenticado mediante Supabase Auth."""
    return UserPublicResponse.model_validate(current_user)


@router.get("/status", response_model=AuthStatusResponse)
def get_auth_status():
    """Retorna el estado de integración de Supabase Auth."""
    configured = bool(
        settings.SUPABASE_URL
        and settings.SUPABASE_ANON_KEY
        and not settings.SUPABASE_ANON_KEY.startswith("your-")
    )
    return AuthStatusResponse(
        provider="Supabase Auth",
        configured=configured,
        supabase_url=settings.SUPABASE_URL if configured else None
    )


# Respuestas informativas para clientes antiguos que intenten llamar a los endpoints obsoletos
@router.post("/login", status_code=status.HTTP_410_GONE)
def deprecated_login():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="El inicio de sesión legado con contraseña local ha sido deprecado. Utilice Supabase Auth en el frontend."
    )


@router.post("/register", status_code=status.HTTP_410_GONE)
def deprecated_register():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="El registro con contraseña local ha sido deprecado. Utilice Supabase Auth en el frontend."
    )
