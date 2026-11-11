from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User
from app.core.security import decode_access_token

# Esquema de autenticación Bearer Token
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False
)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia de seguridad que extrae el token Bearer, lo decodifica,
    valida la firma y obtiene el registro del usuario desde PostgreSQL.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales de acceso. Inicie sesión nuevamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo en el sistema."
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar identidad: {str(e)}"
        )


def get_current_titular_id(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> str:
    """
    Obtiene el ID del titular en contexto:
    Si hay token válido, retorna el id del usuario logueado.
    Si no hay token o es entorno demo, retorna el ID demo.
    """
    if token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            return payload["sub"]
    return "titular-demo-12345"
