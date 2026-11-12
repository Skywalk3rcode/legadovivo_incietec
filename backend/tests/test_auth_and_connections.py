import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_connection_code
)


def test_password_hashing_and_verification():
    raw_password = "ClaveUltraSegura2026!"
    hashed = get_password_hash(raw_password)

    # 1. El hash no debe ser igual a la clave plana
    assert hashed != raw_password
    # 2. La verificación debe retornar True para la clave correcta
    assert verify_password(raw_password, hashed) is True
    # 3. La verificación debe fallar para una clave incorrecta
    assert verify_password("PasswordErronea", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = "test-user-uuid-12345"
    token = create_access_token(subject=user_id)

    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_invalid_token_returns_none():
    invalid_token = "token_invalido_corrupto_12345"
    payload = decode_access_token(invalid_token)
    assert payload is None


def test_connection_code_generation():
    code1 = generate_connection_code()
    code2 = generate_connection_code()

    # Formato: LEG-XXXXXX
    assert code1.startswith("LEG-")
    assert code2.startswith("LEG-")
    assert len(code1) >= 10
    # Códigos deben ser únicos
    assert code1 != code2
    # No deben contener caracteres confusos (O, 0, I, 1)
    for bad_char in ['O', '0', 'I', '1']:
        assert bad_char not in code1[4:]

