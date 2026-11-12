import pytest
from datetime import datetime, timedelta
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.postgres import get_db, Base
from app.models.sql_models import User, LegacyConnection, ConnectionStatus, CodeAttempt
from app.core.security import create_access_token

client = TestClient(app)


# Setup base de datos de prueba en memoria o reutilizando la de test
@pytest.fixture(scope="module")
def db_session():
    from app.db.postgres import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def titular_user(db_session):
    user_id = f"test-titular-{uuid.uuid4().hex[:8]}"
    email = f"{user_id}@test.com"
    user = User(
        id=user_id,
        email=email,
        full_name="Abuelo Alberto Gómez",
        hashed_password="hash",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def titular_token(titular_user):
    return create_access_token(subject=titular_user.id)


@pytest.fixture
def beneficiary_user(db_session):
    user_id = f"test-beneficiary-{uuid.uuid4().hex[:8]}"
    email = f"{user_id}@test.com"
    user = User(
        id=user_id,
        email=email,
        full_name="Carlos Gómez (Nieto)",
        hashed_password="hash",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def beneficiary_token(beneficiary_user):
    return create_access_token(subject=beneficiary_user.id)


@pytest.fixture
def other_user(db_session):
    user_id = f"test-other-{uuid.uuid4().hex[:8]}"
    email = f"{user_id}@test.com"
    user = User(
        id=user_id,
        email=email,
        full_name="Extraño No Autorizado",
        hashed_password="hash",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_token(other_user):
    return create_access_token(subject=other_user.id)


# ==========================================
# Pruebas Unitarias & de Integración
# ==========================================

def test_generate_code_with_configurable_expiration(titular_token):
    # Generar código con 24 horas de vigencia
    headers = {"Authorization": f"Bearer {titular_token}"}
    response = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 24, "auto_cancel_previous": False},
        headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["connection_code"].startswith("LEG-")
    assert len(data["connection_code"]) >= 10
    assert data["status"] == "PENDING"
    assert "owner_name" in data
    assert "expires_at" in data

    created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
    delta = (expires - created).total_seconds()
    assert abs(delta - 24 * 3600) < 60


def test_cancel_pending_code(titular_token, other_token):
    headers_titular = {"Authorization": f"Bearer {titular_token}"}
    headers_other = {"Authorization": f"Bearer {other_token}"}

    # 1. Titular genera código
    gen_res = client.post("/api/legacy/generate-code", json={"expiration_hours": 12}, headers=headers_titular)
    assert gen_res.status_code == 201
    conn_id = gen_res.json()["connection_id"]

    # 2. Otro usuario intenta cancelarlo (debe dar 403)
    forbidden_res = client.post(f"/api/legacy/cancel-code/{conn_id}", headers=headers_other)
    assert forbidden_res.status_code == 403

    # 3. El titular legítimo lo cancela (debe dar 200)
    cancel_res = client.post(f"/api/legacy/cancel-code/{conn_id}", headers=headers_titular)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["success"] is True


def test_preview_code_shows_titular_safely(titular_token, beneficiary_token):
    # 1. Titular genera código
    gen_res = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 48},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    assert gen_res.status_code == 201
    code = gen_res.json()["connection_code"]

    # 2. Beneficiario previsualiza
    preview_res = client.post(
        "/api/legacy/preview-code",
        json={"connection_code": code},
        headers={"Authorization": f"Bearer {beneficiary_token}"}
    )
    assert preview_res.status_code == 200
    pdata = preview_res.json()
    assert pdata["owner_name"] == "Abuelo Alberto Gómez"
    assert pdata["connection_code"] == code
    # Verificar que no se expone información privada
    assert "password" not in pdata
    assert "email" not in pdata
    assert "hashed_password" not in pdata


def test_prevent_self_linking(titular_token):
    # Titular intenta validar o vincularse a su propio código
    gen_res = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 48},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    code = gen_res.json()["connection_code"]

    # Previsualizar propio código
    preview_res = client.post(
        "/api/legacy/preview-code",
        json={"connection_code": code},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    assert preview_res.status_code == 400
    assert "No puedes vincularte a tu propio legado" in preview_res.json()["detail"]

    # Confirmar propio código
    link_res = client.post(
        "/api/legacy/confirm-link",
        json={"connection_code": code},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    assert link_res.status_code == 400


def test_confirm_link_atomic_and_prevent_double_redeem(titular_token, beneficiary_token, other_token):
    # 1. Generar código
    gen_res = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 48},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    code = gen_res.json()["connection_code"]

    # 2. Beneficiario 1 confirma vinculación
    confirm_res = client.post(
        "/api/legacy/confirm-link",
        json={"connection_code": code},
        headers={"Authorization": f"Bearer {beneficiary_token}"}
    )
    assert confirm_res.status_code == 200
    data = confirm_res.json()
    assert data["status"] == "ACTIVE"
    assert data["linked_at"] is not None

    # 3. Usuario 2 intenta canjear el mismo código (debe fallar)
    second_confirm = client.post(
        "/api/legacy/confirm-link",
        json={"connection_code": code},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert second_confirm.status_code == 400
    assert "ya ha sido utilizado" in second_confirm.json()["detail"]


def test_prevent_duplicate_linking_with_same_titular(titular_token, beneficiary_token):
    # 1. Vincular por primera vez
    gen1_res = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 48},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    code1 = gen1_res.json()["connection_code"]
    client.post(
        "/api/legacy/confirm-link",
        json={"connection_code": code1},
        headers={"Authorization": f"Bearer {beneficiary_token}"}
    )

    # 2. El titular genera un segundo código
    gen2_res = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 48},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    code2 = gen2_res.json()["connection_code"]

    # 3. El mismo beneficiario intenta vincularse por segunda vez
    preview_res = client.post(
        "/api/legacy/preview-code",
        json={"connection_code": code2},
        headers={"Authorization": f"Bearer {beneficiary_token}"}
    )
    assert preview_res.status_code == 400
    assert "Ya te encuentras vinculado activamente" in preview_res.json()["detail"]


def test_expired_code_rejection(titular_token, other_token, db_session):
    # Generar código y forzar su expiración en el pasado
    gen_res = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 24},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    conn_id = gen_res.json()["connection_id"]
    code = gen_res.json()["connection_code"]

    # Manipular expires_at en DB para simular tiempo pasado
    conn = db_session.query(LegacyConnection).filter(LegacyConnection.id == conn_id).first()
    conn.expires_at = datetime.utcnow() - timedelta(hours=2)
    db_session.commit()

    # Intentar validar el código expirado
    preview_res = client.post(
        "/api/legacy/preview-code",
        json={"connection_code": code},
        headers={"Authorization": f"Bearer {other_token}"}
    )
    assert preview_res.status_code == 400
    assert "expirado" in preview_res.json()["detail"].lower()


def test_unlink_connection(titular_token, beneficiary_token):
    # 1. Vincular primero a los usuarios
    gen_res = client.post(
        "/api/legacy/generate-code",
        json={"expiration_hours": 48},
        headers={"Authorization": f"Bearer {titular_token}"}
    )
    code = gen_res.json()["connection_code"]
    link_res = client.post(
        "/api/legacy/confirm-link",
        json={"connection_code": code},
        headers={"Authorization": f"Bearer {beneficiary_token}"}
    )
    assert link_res.status_code == 200
    conn_to_unlink = link_res.json()["connection_id"]

    # 2. Beneficiario se desvincula
    unlink_res = client.post(
        f"/api/legacy/unlink/{conn_to_unlink}",
        headers={"Authorization": f"Bearer {beneficiary_token}"}
    )
    assert unlink_res.status_code == 200
    assert unlink_res.json()["success"] is True

    # 3. Verificar que ya no aparece en conexiones activas
    after_res = client.get(
        "/api/legacy/my-connections",
        headers={"Authorization": f"Bearer {beneficiary_token}"}
    )
    assert len(after_res.json()) == 0


def test_brute_force_rate_limiting(other_token):
    # Simular múltiples intentos fallidos continuos
    headers = {"Authorization": f"Bearer {other_token}"}
    for i in range(5):
        res = client.post(
            "/api/legacy/preview-code",
            json={"connection_code": f"LEG-FAKE{i}99"},
            headers=headers
        )
        assert res.status_code == 404

    # El sexto intento debe ser bloqueado con 429 Too Many Requests
    blocked_res = client.post(
        "/api/legacy/preview-code",
        json={"connection_code": "LEG-ANYTHING"},
        headers=headers
    )
    assert blocked_res.status_code == 429
    assert "límite de intentos fallidos" in blocked_res.json()["detail"]
