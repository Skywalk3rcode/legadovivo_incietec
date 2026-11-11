try:
    import pytest
except ImportError:
    pytest = None
from app.core.security import (
    generate_connection_code,
    verify_supabase_token,
    create_access_token
)


def test_supabase_token_normalization_and_decoding():
    user_id = "test-user-uuid-12345"
    token = create_access_token(subject=user_id)

    assert isinstance(token, str)
    assert len(token) > 20

    payload = verify_supabase_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert "full_name" in payload


def test_supabase_invalid_token_returns_none():
    invalid_token = "token_invalido_corrupto_12345"
    payload = verify_supabase_token(invalid_token)
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
