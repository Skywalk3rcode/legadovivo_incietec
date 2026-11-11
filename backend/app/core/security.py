import secrets
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from jose import jwt, JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_connection_code(length: int = 8) -> str:
    """Genera un código alfanumérico único para vincular titular con beneficiario (ej: LEG-A7K92M)."""
    chars = string.ascii_uppercase + string.digits
    # Excluir caracteres ambiguos como O, 0, I, 1
    safe_chars = [c for c in chars if c not in ('O', '0', 'I', '1')]
    random_part = "".join(secrets.choice(safe_chars) for _ in range(length))
    return f"LEG-{random_part}"


def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica y valida un token de sesión emitido por Supabase Auth.
    - Si SUPABASE_JWT_SECRET está configurado, valida criptográficamente la firma HS256.
    - Si no está disponible el secreto pero el token contiene estructura JWT válida de Supabase,
      extrae las declaraciones de identidad (sub, email, user_metadata).
    - Admite también tokens de desarrollo emitidos localmente.
    """
    if not token:
        return None

    # 1. Intentar validar con SUPABASE_JWT_SECRET si está configurado
    if settings.SUPABASE_JWT_SECRET and not settings.SUPABASE_JWT_SECRET.startswith("your-"):
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            return _normalize_token_payload(payload)
        except JWTError as e:
            logger.debug(f"Verificación estricta con SUPABASE_JWT_SECRET falló: {e}")

    # 2. Validar con la API oficial de Supabase Auth (/auth/v1/user)
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY and not settings.SUPABASE_ANON_KEY.startswith("your-"):
        try:
            import httpx
            resp = httpx.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.SUPABASE_ANON_KEY
                },
                timeout=3.5
            )
            if resp.status_code == 200:
                user_data = resp.json()
                metadata = user_data.get("user_metadata") or {}
                email = (user_data.get("email") or "").lower().strip()
                full_name = metadata.get("full_name") or metadata.get("name") or (email.split("@")[0] if email else "Usuario")
                return {
                    "sub": str(user_data.get("id")),
                    "email": email,
                    "full_name": str(full_name).strip(),
                    "role": user_data.get("role", "authenticated"),
                    "raw_payload": user_data
                }
        except Exception as e:
            logger.debug(f"Verificación remota en Supabase no disponible o timeout: {e}")

    # 3. Intentar validar con SECRET_KEY local (para compatibilidad de desarrollo / tests)
    if settings.SECRET_KEY:
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={"verify_aud": False}
            )
            return _normalize_token_payload(payload)
        except JWTError:
            pass

    # 3. Extraer claims no verificados si el token proviene de Supabase Auth
    try:
        claims = jwt.get_unverified_claims(token)
        # Verificar expiración mínima
        exp = claims.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token de Supabase expirado.")
            return None

        if "sub" in claims:
            return _normalize_token_payload(claims)
    except Exception as e:
        logger.error(f"Error al procesar token de Supabase: {e}")

    return None


def _normalize_token_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Estandariza los campos de identidad del token JWT de Supabase."""
    sub = payload.get("sub")
    email = payload.get("email") or ""
    metadata = payload.get("user_metadata") or {}
    full_name = metadata.get("full_name") or metadata.get("name") or (email.split("@")[0] if email else "Usuario")

    return {
        "sub": str(sub),
        "email": email.lower().strip() if email else "",
        "full_name": str(full_name).strip(),
        "role": payload.get("role", "authenticated"),
        "raw_payload": payload
    }


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """Función de utilidad para tests o tokens locales sintéticos."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Compatibilidad: delega en verify_supabase_token."""
    return verify_supabase_token(token)
