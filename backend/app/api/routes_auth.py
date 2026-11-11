from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User, LegacyPlan
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter()


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., example="alberto@legadovivo.com")
    password: str = Field(..., min_length=6, example="ClaveSegura2026!")
    full_name: str = Field(..., example="Alberto Gómez")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., example="alberto@legadovivo.com")
    password: str = Field(..., example="ClaveSegura2026!")


class UserPublicResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublicResponse


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en PostgreSQL con contraseña hasheada mediante BCrypt.
    Inicializa automáticamente su Plan de Legado para su rol de Titular
    y emite su token JWT de sesión.
    """
    # 1. Verificar si el email ya existe
    existing_user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una cuenta registrada con este correo electrónico."
        )

    # 2. Hashear la contraseña con BCrypt
    hashed = get_password_hash(payload.password)

    # 3. Crear el nuevo usuario
    new_user = User(
        email=payload.email.lower().strip(),
        hashed_password=hashed,
        full_name=payload.full_name.strip(),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Inicializar su Plan de Legado (como Titular)
    plan = LegacyPlan(titular_id=new_user.id)
    db.add(plan)
    db.commit()

    # 5. Emitir Token JWT
    access_token = create_access_token(subject=new_user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublicResponse.model_validate(new_user)
    )


@router.post("/login", response_model=TokenResponse)
def login_user(
    payload: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Autentica un usuario verificando el hash BCrypt y emite el token JWT de acceso.
    """
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas (correo o contraseña incorrectos)."
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas (correo o contraseña incorrectos)."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta se encuentra desactivada."
        )

    access_token = create_access_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublicResponse.model_validate(user)
    )


@router.get("/me", response_model=UserPublicResponse)
def get_authenticated_profile(
    current_user: User = Depends(get_current_user)
):
    """Devuelve los datos del usuario en sesión activa."""
    return UserPublicResponse.model_validate(current_user)

