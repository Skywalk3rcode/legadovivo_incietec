from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.sql_models import User, LegacyPlan, ActivationRule, AuditLog
from app.core.security import get_password_hash
from app.api.deps import get_current_user

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LegacyPlanCreate(BaseModel):
    activation_rule: ActivationRule = ActivationRule.MANUAL_CONFIRMATION
    emergency_contact_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class LegacyPlanResponse(BaseModel):
    id: str
    titular_id: str
    is_activated: bool
    activation_rule: ActivationRule
    emergency_contact_email: Optional[str] = None
    notes: Optional[str] = None
    activated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Crea un usuario en PostgreSQL con hash seguro BCrypt.
    (Para registro completo con token JWT, use /api/auth/register).
    """
    existing = db.query(User).filter(User.email == user_in.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya se encuentra registrado."
        )

    new_user = User(
        email=user_in.email.lower().strip(),
        full_name=user_in.full_name.strip(),
        hashed_password=get_password_hash(user_in.password),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Inicializar su Plan de Legado como titular
    plan = LegacyPlan(titular_id=new_user.id)
    db.add(plan)
    db.commit()

    return new_user


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    """Obtiene los datos públicos de un usuario por su ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    return user


@router.get("/{titular_id}/plan", response_model=LegacyPlanResponse)
def get_legacy_plan(titular_id: str, db: Session = Depends(get_db)):
    """Obtiene el plan de legado de un titular."""
    plan = db.query(LegacyPlan).filter(LegacyPlan.titular_id == titular_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de legado no encontrado."
        )
    return plan


@router.post("/{titular_id}/activate-plan", response_model=LegacyPlanResponse)
def activate_legacy_plan(titular_id: str, db: Session = Depends(get_db)):
    """Activa el plan de legado tras confirmación o deceso."""
    plan = db.query(LegacyPlan).filter(LegacyPlan.titular_id == titular_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan de legado no encontrado."
        )

    plan.is_activated = True
    plan.activated_at = datetime.utcnow()

    # Registrar en auditoría
    audit = AuditLog(
        user_id=titular_id,
        action="LEGACY_PLAN_ACTIVATED",
        details="El plan ha sido activado. Los beneficiarios ahora pueden acceder al chat."
    )
    db.add(audit)
    db.commit()
    db.refresh(plan)

    return plan


