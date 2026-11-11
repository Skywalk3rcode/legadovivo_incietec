"""
API Router configuration for LegadoVivo
"""
from fastapi import APIRouter
from app.api.routes_auth import router as auth_router
from app.api.routes_connections import router as connections_router
from app.api.routes_capsules import router as capsules_router
from app.api.routes_chat import router as chat_router
from app.api.routes_users import router as users_router

api_router = APIRouter()

# Autenticación y Cuentas
api_router.include_router(auth_router, prefix="/auth", tags=["Autenticación & Sesión"])

# Lógica de Vinculación y Conexiones (Titular <-> Beneficiario)
api_router.include_router(connections_router, prefix="/legacy", tags=["Vinculaciones & Legado"])

# Recuerdos y Chat Neuronal
api_router.include_router(capsules_router, prefix="/capsules", tags=["Cápsulas de Memoria"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat del Legado"])

# Auditoría y Activación
api_router.include_router(users_router, prefix="/users", tags=["Usuarios & Activación"])

__all__ = ["api_router"]
